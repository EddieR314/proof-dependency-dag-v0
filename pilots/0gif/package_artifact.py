from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PILOT = Path(__file__).resolve().parent
OUTPUT = REPO / "proof-dag-lean-0gif-pilot-v1.0.0-silver.zip"

EXCLUDED_NAMES = {"checksums.sha256", "zip_integrity_report.txt"}
SHARED_ROOTS = [
    REPO / "proof-skill-standard-v0.3.md",
    REPO / "skills" / "proof-dag-lean",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pilot_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in sorted(PILOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(PILOT)
        if ".lake" in relative.parts or "__pycache__" in relative.parts:
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        files.append((path, f"proof-dag-lean-0gif-pilot/{relative.as_posix()}"))
    return files


def shared_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for root in SHARED_ROOTS:
        if root.is_file():
            files.append((root, root.relative_to(REPO).as_posix()))
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files.append((path, path.relative_to(REPO).as_posix()))
    return files


def write_checksums(files: list[tuple[Path, str]]) -> Path:
    checksum_path = PILOT / "checksums.sha256"
    lines = [f"{sha256(path)}  {archive_name}" for path, archive_name in files]
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def write_zip(files: list[tuple[Path, str]]) -> None:
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, archive_name in files:
            archive.write(path, archive_name)


def verify_zip(expected_names: set[str]) -> dict[str, object]:
    with zipfile.ZipFile(OUTPUT) as archive:
        names = archive.namelist()
        bad_member = archive.testzip()
    return {
        "archive": OUTPUT.name,
        "member_count": len(names),
        "duplicate_member_count": len(names) - len(set(names)),
        "missing_expected_members": sorted(expected_names - set(names)),
        "unexpected_members": sorted(set(names) - expected_names),
        "bad_member": bad_member,
        "status": "passed"
        if bad_member is None
        and len(names) == len(set(names))
        and set(names) == expected_names
        else "failed",
    }


def main() -> None:
    base_files = pilot_files() + shared_files()
    checksum_path = write_checksums(base_files)
    checksum_entry = (
        checksum_path,
        "proof-dag-lean-0gif-pilot/checksums.sha256",
    )

    report_path = PILOT / "zip_integrity_report.txt"
    report_path.write_text("ZIP integrity check pending.\n", encoding="utf-8")
    report_entry = (
        report_path,
        "proof-dag-lean-0gif-pilot/zip_integrity_report.txt",
    )

    release_files = base_files + [checksum_entry, report_entry]
    write_zip(release_files)
    expected = {archive_name for _, archive_name in release_files}
    report = verify_zip(expected)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_zip(release_files)
    final_report = verify_zip(expected)
    if final_report["status"] != "passed":
        raise SystemExit(json.dumps(final_report, indent=2))
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "sha256": sha256(OUTPUT),
                **final_report,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
