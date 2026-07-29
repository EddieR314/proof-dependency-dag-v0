from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "olympiad-algebra-expert"
PROMPT_FILES = (
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "references" / "topic-routing.md",
    SKILL_ROOT / "references" / "proof-audit.md",
    SKILL_ROOT / "references" / "pattern-library-v0.1.md",
)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def load_prompt_context() -> str:
    sections = []
    for path in PROMPT_FILES:
        sections.append(f"\n===== {path.name} =====\n{path.read_text(encoding='utf-8')}")
    return "".join(sections)


def build_prompt(row: dict, prompt_context: str, prompt_version: str) -> str:
    return f"""You are running a sealed olympiad-algebra proof-layer forward test.

Prompt version: {prompt_version}

Hard constraints:
- Use only the problem statement below and the embedded frozen Skill references.
- Do not browse, search, or open any local files.
- Do not use or infer a hidden reference solution.
- Route by the decisive proof mechanism, not the source bucket.
- Use ASCII characters only in every output string. Write <=, >=, in, subset,
  Q, R, sum, sqrt, and similar plain-text notation instead of Unicode symbols.
- Give a rigorous proof when you can close every step.
- Apply this state table exactly:
  * passed: the answer and proof are complete; unresolved_gap is ""; proof_review
    is "partial"; handoff readiness is "candidate".
  * blocked: no complete answer is claimed; unresolved_gap names the exact
    missing lemma or step; proof_review is "partial" if a substantial partial
    proof was audited, otherwise "not_run"; handoff readiness is "blocked".
  * failed: the attempted argument is known to be invalid; unresolved_gap
    explains the failure; proof_review is "failed"; handoff readiness is
    "blocked".
- Never label a proof "passed" if its own text retracts a claim, identifies an
  unresolved gap, or says the answer is unsupported.
- A model-generated proof is not human-reviewed. Therefore set
  component_status.proof_review="partial" for a complete candidate proof,
  "failed" for a known-invalid attempt, and "not_run" only when no proof audit
  was possible.
- DAG, formal_mapping, and lean_build must remain "not_run".
- dag_lean_handoff_readiness must be "candidate" only for a complete candidate
  proof, otherwise "blocked". Never use "reviewed".
- Return only the JSON object required by the supplied output schema.

Problem metadata:
problem_id: {row["problem_id"]}
pilot_id: {row["pilot_id"]}

Problem statement:
{row["statement"]}

Frozen Skill references:
{prompt_context}
"""


def parse_json_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1])
    return json.loads(text)


def validate_schema_for_api(schema: dict, location: str = "$") -> None:
    unsupported = {"uniqueItems", "minItems", "maxItems", "pattern"}
    present = unsupported.intersection(schema)
    if present:
        raise ValueError(
            f"{location} uses unsupported strict-output keywords: {sorted(present)}"
        )
    if "const" in schema or "enum" in schema:
        if "type" not in schema:
            raise ValueError(f"{location} uses const/enum without an explicit type")
    if schema.get("type") == "object":
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        missing = set(properties) - required
        if missing:
            raise ValueError(
                f"{location} has optional properties unsupported by strict output: "
                f"{sorted(missing)}"
            )
        for name, child in properties.items():
            validate_schema_for_api(child, f"{location}.properties.{name}")
    if schema.get("type") == "array" and "items" in schema:
        validate_schema_for_api(schema["items"], f"{location}.items")


def validate_prediction(prediction: dict, row: dict) -> None:
    serialized = json.dumps(prediction, ensure_ascii=False)
    if not serialized.isascii():
        raise ValueError("prediction contains non-ASCII characters")
    if prediction.get("problem_id") != row["problem_id"]:
        raise ValueError(
            f"problem_id mismatch: expected {row['problem_id']}, "
            f"got {prediction.get('problem_id')}"
        )
    if prediction.get("pilot_id") != row["pilot_id"]:
        raise ValueError(
            f"pilot_id mismatch: expected {row['pilot_id']}, "
            f"got {prediction.get('pilot_id')}"
        )
    secondary = prediction.get("routing", {}).get("secondary_modules", [])
    if len(secondary) != len(set(secondary)):
        raise ValueError("routing.secondary_modules contains duplicates")
    proof_result = prediction.get("proof_result")
    gap = prediction.get("unresolved_gap", "").strip()
    handoff = prediction.get("dag_lean_handoff_readiness")
    review = prediction.get("component_status", {}).get("proof_review")
    if proof_result == "passed":
        if gap:
            raise ValueError("passed prediction has a nonempty unresolved_gap")
        if review != "partial":
            raise ValueError("passed prediction must set proof_review=partial")
        if handoff != "candidate":
            raise ValueError("passed prediction must set handoff=candidate")
    elif proof_result == "blocked":
        if not gap:
            raise ValueError("blocked prediction must state an unresolved_gap")
        if review not in {"partial", "not_run"}:
            raise ValueError("blocked prediction has invalid proof_review state")
        if handoff != "blocked":
            raise ValueError("blocked prediction must set handoff=blocked")
    elif proof_result == "failed":
        if not gap:
            raise ValueError("failed prediction must explain the failure")
        if review != "failed":
            raise ValueError("failed prediction must set proof_review=failed")
        if handoff != "blocked":
            raise ValueError("failed prediction must set handoff=blocked")


def run_one(
    row: dict,
    config: dict,
    schema_path: Path,
    result_dir: Path,
    log_dir: Path,
    prompt_context: str,
) -> dict:
    problem_id = row["problem_id"]
    result_path = result_dir / f"{problem_id}.json"
    if result_path.exists():
        return parse_json_file(result_path)

    codex = shutil.which("codex.cmd") or shutil.which("codex")
    if not codex:
        raise RuntimeError("Codex CLI was not found")

    prompt = build_prompt(row, prompt_context, config["prompt_version"])
    prompt_sha256 = sha256_text(prompt)
    last_error = ""
    with tempfile.TemporaryDirectory(prefix="algebra-scale-pilot-") as work:
        work_dir = Path(work)
        for attempt in range(1, config["max_attempts_per_problem"] + 1):
            raw_output = work_dir / f"{problem_id}-attempt-{attempt}.json"
            command = [
                codex,
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--skip-git-repo-check",
                "--sandbox",
                config["sandbox"],
                "--model",
                config["model"],
                "-c",
                f'model_reasoning_effort="{config["reasoning_effort"]}"',
                "-c",
                f'service_tier="{config["service_tier"]}"',
                "--output-schema",
                str(schema_path.resolve()),
                "--color",
                "never",
                "--json",
                "--output-last-message",
                str(raw_output),
                "--cd",
                str(work_dir),
                "-",
            ]
            started = dt.datetime.now(dt.timezone.utc)
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
            )
            finished = dt.datetime.now(dt.timezone.utc)
            (log_dir / f"{problem_id}-attempt-{attempt}.stdout.jsonl").write_text(
                completed.stdout,
                encoding="utf-8",
            )
            (log_dir / f"{problem_id}-attempt-{attempt}.stderr.txt").write_text(
                completed.stderr,
                encoding="utf-8",
            )
            if completed.returncode != 0 or not raw_output.exists():
                last_error = (
                    f"attempt {attempt}: exit={completed.returncode}; "
                    f"stderr={completed.stderr[-1000:]}"
                )
                if "usage limit" in completed.stderr.lower() or "login" in completed.stderr.lower():
                    break
                continue
            try:
                prediction = parse_json_file(raw_output)
                validate_prediction(prediction, row)
            except (json.JSONDecodeError, OSError) as exc:
                last_error = f"attempt {attempt}: invalid JSON: {exc}"
                continue
            except ValueError as exc:
                last_error = f"attempt {attempt}: invalid prediction: {exc}"
                continue

            prediction["run_metadata"] = {
                "run_id": config["run_id"],
                "model": config["model"],
                "reasoning_effort": config["reasoning_effort"],
                "service_tier": config["service_tier"],
                "prompt_version": config["prompt_version"],
                "prompt_sha256": prompt_sha256,
                "attempt": attempt,
                "started_at_utc": started.isoformat(),
                "finished_at_utc": finished.isoformat(),
                "duration_seconds": (finished - started).total_seconds(),
            }
            result_path.write_text(
                json.dumps(prediction, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return prediction

    raise RuntimeError(f"{problem_id} failed: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--statements", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--count", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_schema_for_api(json.loads(args.schema.read_text(encoding="utf-8")))
    rows = read_jsonl(args.statements)
    stop = None if args.count is None else args.offset + args.count
    rows = rows[args.offset:stop]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_dir = args.output_dir / "individual"
    log_dir = args.output_dir / "logs"
    result_dir.mkdir(exist_ok=True)
    log_dir.mkdir(exist_ok=True)
    prompt_context = load_prompt_context()

    failures: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.concurrency
    ) as executor:
        futures = {
            executor.submit(
                run_one,
                row,
                config,
                args.schema,
                result_dir,
                log_dir,
                prompt_context,
            ): row
            for row in rows
        }
        for future in concurrent.futures.as_completed(futures):
            row = futures[future]
            try:
                future.result()
                print(f"completed {row['problem_id']}", flush=True)
            except Exception as exc:
                failures.append(
                    {"problem_id": row["problem_id"], "error": str(exc)}
                )
                print(f"failed {row['problem_id']}: {exc}", flush=True)

    result_rows = []
    for row in rows:
        result_path = result_dir / f"{row['problem_id']}.json"
        if result_path.exists():
            result_rows.append(parse_json_file(result_path))
    combined_path = args.output_dir / "predictions.jsonl"
    write_jsonl(combined_path, result_rows)
    summary = {
        "requested": len(rows),
        "completed": len(result_rows),
        "failed": len(failures),
        "failures": failures,
        "predictions_sha256": hashlib.sha256(combined_path.read_bytes()).hexdigest(),
    }
    (args.output_dir / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
