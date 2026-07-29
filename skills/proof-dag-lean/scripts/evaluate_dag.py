#!/usr/bin/env python3
"""Evaluate derivability, first break, and optional node criticality."""

from __future__ import annotations

import argparse

from dag_core import (
    evaluate_criticality,
    evaluate_graph,
    read_graph,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", required=True)
    parser.add_argument("--critical-candidate")
    parser.add_argument("--output")
    args = parser.parse_args()

    graph = read_graph(args.graph)
    result = {"evaluation": evaluate_graph(graph)}
    if args.critical_candidate:
        result["criticality"] = evaluate_criticality(
            graph,
            args.critical_candidate,
        )
    write_json(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

