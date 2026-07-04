import argparse
import json
import sys

from spu_utils import dependency_closure_errors, read_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", help="SPU JSONL file to check.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    records = read_jsonl(args.jsonl)
    results = []
    total_errors = 0

    for record in records:
        errors = dependency_closure_errors(record)
        total_errors += len(errors)
        results.append(
            {
                "sample_id": record.get("sample_id"),
                "ok": not errors,
                "errors": errors,
            }
        )

    if args.json:
        print(json.dumps({"ok": total_errors == 0, "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"{args.jsonl}: {len(records)} records, {total_errors} closure errors")
        for result in results:
            if result["ok"]:
                continue
            print(f"  {result['sample_id']}")
            for error in result["errors"]:
                print(f"    {error}")

    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
