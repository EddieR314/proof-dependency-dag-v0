from __future__ import annotations

import unittest

from select_algebra_curriculum import (
    classify,
    deduplicate,
    take_diverse,
    unclassified_reason,
)


class CurriculumSelectorTests(unittest.TestCase):
    def test_specific_topics_take_priority(self) -> None:
        self.assertEqual(
            classify("Algebra > Polynomial operations\nAlgebra > Complex numbers"),
            "complex_algebra",
        )
        self.assertEqual(
            classify("Algebra > Functional Equations\nAlgebra > Floors and ceilings"),
            "discrete_algebra",
        )
        self.assertEqual(
            classify(
                "Algebra > Functional Equations\n"
                "Algebra > Sequences and Series > Telescoping series"
            ),
            "functional_equations",
        )
        self.assertEqual(
            classify("Algebra > Simple Equations\nAlgebra > Polynomial operations"),
            "polynomials",
        )
        self.assertEqual(
            classify(
                "Algebra > Polynomials > Vieta's formulas\n"
                "Algebra > Integers"
            ),
            "polynomials",
        )
        self.assertEqual(
            classify(
                "Algebra > Sequences > Sums and products\n"
                "Algebra > Linear and quadratic inequalities"
            ),
            "inequalities",
        )

    def test_normalized_hash_dedup_keeps_higher_score(self) -> None:
        rows = [
            {
                "problem_id": "a",
                "normalized_hash": "same",
                "proof_sample_score": "10",
            },
            {
                "problem_id": "b",
                "normalized_hash": "same",
                "proof_sample_score": "20",
            },
        ]
        self.assertEqual(deduplicate(rows)[0]["problem_id"], "b")

    def test_calibration_length_gate_is_hard(self) -> None:
        rows = [
            {
                "problem_id": "long",
                "solution_length": "7000",
                "competition": "A",
            },
            {
                "problem_id": "short",
                "solution_length": "2000",
                "competition": "B",
            },
        ]
        selected, remaining = take_diverse(
            rows, count=2, source_cap=2, max_solution_length=5000
        )
        self.assertEqual([row["problem_id"] for row in selected], ["short"])
        self.assertEqual([row["problem_id"] for row in remaining], ["long"])

    def test_unclassified_reason_distinguishes_noise_and_gap(self) -> None:
        self.assertEqual(
            unclassified_reason("Precalculus > Trigonometric functions"),
            "source_bucket_noise: primarily_trigonometry_or_calculus",
        )
        self.assertEqual(
            unclassified_reason("Algebra > Linear Algebra > Matrices"),
            "taxonomy_gap: linear_algebra_not_in_current_six_modules",
        )
        self.assertEqual(
            unclassified_reason(
                "Algebra > Quadratic functions",
                "Find the roots of a trigonometric equation involving sin x.",
            ),
            "source_bucket_noise: primarily_trigonometry_or_calculus",
        )


if __name__ == "__main__":
    unittest.main()
