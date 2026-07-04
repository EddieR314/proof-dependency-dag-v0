import argparse
import json
import sys

from spu_utils import read_jsonl, validate_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", nargs="+", help="JSONL files to validate.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    all_results = []
    total_errors = 0

    for path in args.jsonl:
        records = read_jsonl(path)
        file_results = []
        seen_sample_ids = set()

        for index, record in enumerate(records, 1):
            errors = validate_record(record)
            sample_id = record.get("sample_id", f"line:{index}")
            if sample_id in seen_sample_ids:
                errors.append(("record", sample_id, "duplicate_sample_id"))
            seen_sample_ids.add(sample_id)

            total_errors += len(errors)
            file_results.append(
                {
                    "line": index,
                    "sample_id": sample_id,
                    "ok": not errors,
                    "errors": errors,
                }
            )

        all_results.append(
            {
                "path": path,
                "num_records": len(records),
                "num_errors": sum(len(result["errors"]) for result in file_results),
                "records": file_results,
            }
        )

    if args.json:
        print(json.dumps({"ok": total_errors == 0, "files": all_results}, ensure_ascii=False, indent=2))
    else:
        for result in all_results:
            print(f"{result['path']}: {result['num_records']} records, {result['num_errors']} errors")
            for record_result in result["records"]:
                if record_result["ok"]:
                    continue
                print(f"  line {record_result['line']} {record_result['sample_id']}")
                for error in record_result["errors"]:
                    print(f"    {error}")

    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
