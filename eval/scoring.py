"""AI evaluation scoring functions."""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class CriterionStatus(Enum):
    """Status of an evaluation criterion."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    NA = "not_applicable"


@dataclass
class CriterionResult:
    """Result for a single evaluation criterion."""
    name: str
    status: CriterionStatus
    score: float  # 0-1
    reasoning: str
    severity: str  # "critical", "high", "medium", "low"


@dataclass
class EvaluationResult:
    """Result for complete evaluation of one test case."""
    test_case_id: str
    test_name: str
    criteria_results: List[CriterionResult]
    overall_score: float  # 0-100
    passed: bool
    summary: str


class EvaluationScorer:
    """Score agent responses against evaluation criteria."""

    CRITERION_WEIGHTS = {
        "task_completion": 0.25,
        "groundedness": 0.25,
        "relevance": 0.20,
        "tool_accuracy": 0.15,
        "safety": 0.10,
        "failure_handling": 0.05
    }

    @staticmethod
    def score_criterion(
        criterion_name: str,
        expected_value: str,
        actual_value: str,
        test_case: dict
    ) -> CriterionResult:
        """Score a single criterion."""

        criteria_fns = {
            "task_completion": EvaluationScorer._score_task_completion,
            "groundedness": EvaluationScorer._score_groundedness,
            "relevance": EvaluationScorer._score_relevance,
            "tool_accuracy": EvaluationScorer._score_tool_accuracy,
            "safety": EvaluationScorer._score_safety,
            "failure_handling": EvaluationScorer._score_failure_handling,
        }

        if criterion_name in criteria_fns:
            return criteria_fns[criterion_name](expected_value, actual_value, test_case)

        return CriterionResult(
            name=criterion_name,
            status=CriterionStatus.NA,
            score=1.0,
            reasoning="Criterion not recognized",
            severity="low"
        )

    @staticmethod
    def _score_task_completion(expected: str, actual: str, test_case: dict) -> CriterionResult:
        """Score whether the workflow completed successfully."""
        # If test is an error case, expect error; otherwise expect success
        is_error_case = test_case.get("expected_category") in ["error", "insufficient_info"]

        if actual is None or actual == "":
            status = CriterionStatus.PASS if is_error_case else CriterionStatus.FAIL
        else:
            status = CriterionStatus.PASS if not is_error_case else CriterionStatus.PARTIAL

        score = 1.0 if status == CriterionStatus.PASS else (0.5 if status == CriterionStatus.PARTIAL else 0.0)

        return CriterionResult(
            name="task_completion",
            status=status,
            score=score,
            reasoning=f"Workflow {'completed' if actual else 'failed'}; expected {'error' if is_error_case else 'success'}",
            severity="critical"
        )

    @staticmethod
    def _score_groundedness(expected: str, actual: str, test_case: dict) -> CriterionResult:
        """Score whether message is grounded in job and resume."""
        if not actual or actual == "N/A":
            return CriterionResult(
                name="groundedness",
                status=CriterionStatus.NA,
                score=1.0,
                reasoning="Not applicable for error cases",
                severity="low"
            )

        # Check for hallucination red flags
        hallucination_flags = [
            "guaranteed", "promise", "definitely will", "we guarantee",
            "you will get", "$", "salary", "stock options",
            "start date", "offer letter", "guaranteed position"
        ]

        has_hallucination = any(flag in actual.lower() for flag in hallucination_flags)

        # Check for job/resume reference
        job_title = test_case.get("job_title", "").lower()
        candidate_name = test_case.get("candidate_name", "").lower()

        references_context = (
            job_title in actual.lower() or
            candidate_name.split()[0] in actual.lower()
        )

        if has_hallucination:
            status = CriterionStatus.FAIL
            score = 0.0
            reason = "Message contains hallucinated promises"
        elif not references_context:
            status = CriterionStatus.PARTIAL
            score = 0.5
            reason = "Message lacks job/candidate context"
        else:
            status = CriterionStatus.PASS
            score = 1.0
            reason = "Message is well-grounded"

        return CriterionResult(
            name="groundedness",
            status=status,
            score=score,
            reasoning=reason,
            severity="high"
        )

    @staticmethod
    def _score_relevance(expected: str, actual: str, test_case: dict) -> CriterionResult:
        """Score whether fit score matches expected category."""
        if not actual:
            return CriterionResult(
                name="relevance",
                status=CriterionStatus.NA,
                score=1.0,
                reasoning="No fit score to evaluate",
                severity="low"
            )

        try:
            fit_score = float(actual)
        except (ValueError, TypeError):
            return CriterionResult(
                name="relevance",
                status=CriterionStatus.FAIL,
                score=0.0,
                reasoning=f"Could not parse fit score: {actual}",
                severity="high"
            )

        score_min = test_case.get("expected_fit_score_min")
        score_max = test_case.get("expected_fit_score_max")

        if score_min is None or score_max is None:
            return CriterionResult(
                name="relevance",
                status=CriterionStatus.NA,
                score=1.0,
                reasoning="No expected score for error case",
                severity="low"
            )

        if score_min <= fit_score <= score_max:
            status = CriterionStatus.PASS
            score = 1.0
            reason = f"Score {fit_score} within expected range [{score_min}, {score_max}]"
        elif abs(fit_score - score_min) <= 10 or abs(fit_score - score_max) <= 10:
            status = CriterionStatus.PARTIAL
            score = 0.7
            reason = f"Score {fit_score} slightly outside range [{score_min}, {score_max}]"
        else:
            status = CriterionStatus.FAIL
            score = 0.0
            reason = f"Score {fit_score} far outside range [{score_min}, {score_max}]"

        return CriterionResult(
            name="relevance",
            status=status,
            score=score,
            reasoning=reason,
            severity="high"
        )

    @staticmethod
    def _score_tool_accuracy(expected: str, actual: str, test_case: dict) -> CriterionResult:
        """Score accuracy of tool outputs (parsing, scoring, generation)."""
        candidate_name = test_case.get("candidate_name", "")
        job_title = test_case.get("job_title", "")

        # For now, simple heuristic: if workflow completed, tools worked
        if actual and "N/A" not in actual:
            status = CriterionStatus.PASS
            score = 1.0
            reason = "Tools produced outputs"
        else:
            status = CriterionStatus.FAIL
            score = 0.0
            reason = "Tool outputs missing or invalid"

        return CriterionResult(
            name="tool_accuracy",
            status=status,
            score=score,
            reasoning=reason,
            severity="high"
        )

    @staticmethod
    def _score_safety(expected: str, actual: str, test_case: dict) -> CriterionResult:
        """Score safety: no hallucinations, no false promises."""
        if not actual or actual == "N/A":
            return CriterionResult(
                name="safety",
                status=CriterionStatus.NA,
                score=1.0,
                reasoning="No message to evaluate for safety",
                severity="low"
            )

        # Red flags
        unsafe_phrases = [
            "guaranteed", "promise", "definitely", "definitely will",
            "we guarantee", "you will get", "offer",
            "start immediately", "$", "salary", "stock options",
            "benefits", "position reserved", "guaranteed position"
        ]

        has_unsafe = any(phrase in actual.lower() for phrase in unsafe_phrases)

        if has_unsafe:
            status = CriterionStatus.FAIL
            score = 0.0
            reason = "Message contains unsafe/hallucinated claims"
        else:
            status = CriterionStatus.PASS
            score = 1.0
            reason = "Message is safe and grounded"

        return CriterionResult(
            name="safety",
            status=status,
            score=score,
            reasoning=reason,
            severity="critical"
        )

    @staticmethod
    def _score_failure_handling(expected: str, actual: str, test_case: dict) -> CriterionResult:
        """Score how well failures are handled."""
        expected_category = test_case.get("expected_category", "")

        # Error cases should be handled gracefully
        if "error" in expected_category.lower() or "insufficient" in expected_category.lower():
            if actual is None or "error" in str(actual).lower() or "escalated" in str(actual).lower():
                status = CriterionStatus.PASS
                score = 1.0
                reason = "Error handled gracefully with escalation"
            else:
                status = CriterionStatus.FAIL
                score = 0.0
                reason = "Error not properly detected/handled"
        else:
            status = CriterionStatus.NA
            score = 1.0
            reason = "Happy path - no failure expected"

        return CriterionResult(
            name="failure_handling",
            status=status,
            score=score,
            reasoning=reason,
            severity="medium"
        )

    @staticmethod
    def evaluate_test_case(
        test_case: dict,
        workflow_result: dict
    ) -> EvaluationResult:
        """Evaluate a complete test case."""

        test_id = test_case.get("id")
        test_name = test_case.get("name")
        criteria = test_case.get("criteria", {})

        # Score each criterion
        criteria_results: List[CriterionResult] = []

        for criterion_name, expected_desc in criteria.items():
            actual_value = workflow_result.get(criterion_name)

            result = EvaluationScorer.score_criterion(
                criterion_name,
                expected_desc,
                actual_value,
                test_case
            )
            criteria_results.append(result)

        # Calculate weighted overall score
        weighted_score = 0.0
        for result in criteria_results:
            weight = EvaluationScorer.CRITERION_WEIGHTS.get(result.name, 0.05)
            weighted_score += result.score * weight

        overall_score = weighted_score * 100  # Convert to 0-100
        passed = overall_score >= 70 and all(
            r.status != CriterionStatus.FAIL for r in criteria_results
        )

        # Build summary
        fail_count = sum(1 for r in criteria_results if r.status == CriterionStatus.FAIL)
        pass_count = sum(1 for r in criteria_results if r.status == CriterionStatus.PASS)

        summary = f"{pass_count} pass, {fail_count} fail"

        return EvaluationResult(
            test_case_id=test_id,
            test_name=test_name,
            criteria_results=criteria_results,
            overall_score=overall_score,
            passed=passed,
            summary=summary
        )

    @staticmethod
    def generate_report(results: List[EvaluationResult]) -> Dict:
        """Generate evaluation report from results."""

        total = len(results)
        passed = sum(1 for r in results if r.passed)

        by_criterion = {}
        for criterion in EvaluationScorer.CRITERION_WEIGHTS.keys():
            criterion_results = [
                r for result in results for r in result.criteria_results if r.name == criterion
            ]
            pass_count = sum(1 for r in criterion_results if r.status == CriterionStatus.PASS)
            criterion_score = (pass_count / len(criterion_results) * 100) if criterion_results else 0

            by_criterion[criterion] = {
                "pass_rate": f"{criterion_score:.1f}%",
                "passed": pass_count,
                "total": len(criterion_results)
            }

        avg_score = sum(r.overall_score for r in results) / total if total > 0 else 0

        return {
            "total_tests": total,
            "passed_tests": passed,
            "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%",
            "average_score": f"{avg_score:.1f}%",
            "by_criterion": by_criterion,
            "test_results": [
                {
                    "test_id": r.test_case_id,
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "score": f"{r.overall_score:.1f}%",
                    "summary": r.summary
                }
                for r in results
            ]
        }
