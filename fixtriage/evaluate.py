"""Measures the keyword+trailer baseline against real ground truth,
with rigorous acceptance criteria: report precision/recall
at the REAL class imbalance, not a rebalanced/synthetic split, and don't
just claim the baseline is good -- show the sweep and let the numbers say so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .classify import Candidate


@dataclass
class ThresholdResult:
    threshold: float
    predicted_positive: int
    true_positive: int
    false_positive: int
    precision: float | None
    recall: float


@dataclass
class EvalReport:
    total_candidates: int
    ground_truth_positive: int
    class_imbalance: str  # e.g. "1:23" -- positives:negatives, real not synthetic
    thresholds: list[ThresholdResult]
    trivial_flag_everything_precision: float
    trivial_flag_everything_recall: float


def evaluate(candidates: list[Candidate], upstream_landed_shas: set[str]) -> EvalReport:
    total = len(candidates)
    gt_positive_shas = {c.sha for c in candidates if c.sha in upstream_landed_shas}
    n_positive = len(gt_positive_shas)
    n_negative = total - n_positive

    ratio = f"1:{round(n_negative / n_positive)}" if n_positive else "n/a (0 positives observed)"

    scores = sorted({c.score.total for c in candidates}, reverse=True)
    # Sweep at each distinct score value present, plus 0 (== flag everything).
    thresholds = sorted(set(scores) | {0.0})
    results = []
    for t in thresholds:
        predicted = [c for c in candidates if c.score.total >= t]
        tp = sum(1 for c in predicted if c.sha in gt_positive_shas)
        fp = len(predicted) - tp
        precision = (tp / len(predicted)) if predicted else None
        recall = (tp / n_positive) if n_positive else 0.0
        results.append(
            ThresholdResult(
                threshold=t,
                predicted_positive=len(predicted),
                true_positive=tp,
                false_positive=fp,
                precision=round(precision, 4) if precision is not None else None,
                recall=round(recall, 4),
            )
        )
    results.sort(key=lambda r: r.threshold, reverse=True)

    trivial_precision = round(n_positive / total, 4) if total else 0.0

    return EvalReport(
        total_candidates=total,
        ground_truth_positive=n_positive,
        class_imbalance=ratio,
        thresholds=results,
        trivial_flag_everything_precision=trivial_precision,
        trivial_flag_everything_recall=1.0,
    )
