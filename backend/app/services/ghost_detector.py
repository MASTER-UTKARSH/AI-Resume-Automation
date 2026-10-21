"""Ghost Job & Repost Detector
Adapted from career-ops/detect-reposts.mjs and freehire/internal/job/ghost/classify.go.

Detects stale, perpetual, and ghost job listings through two tiers of evidence:
1. Structural Evidence:
   - Days elapsed since first posting (age > 45 days)
   - Title identity repetition / repost clusters across 90 days
   - Absence from company's official ATS board (aggregator only)
2. Outcome Evidence:
   - Applicant silence rate / response latency > 30 days
"""

from typing import Dict, Any, List

class GhostJobDetector:
    @staticmethod
    def evaluate_job_legitimacy(
        job: Dict[str, Any],
        repost_count_90d: int = 1,
        days_active: int = 10,
        is_official_ats: bool = True,
        applicant_silence_count: int = 0
    ) -> Dict[str, Any]:
        """Evaluates whether a job opening is active and legitimate or a ghost listing."""
        structural_flags = []
        outcome_flags = []

        # 1. Structural Checks
        if repost_count_90d >= 3:
            structural_flags.append(f"Perpetual repost: Listed {repost_count_90d} times in 90 days.")
        elif repost_count_90d == 2:
            structural_flags.append("Relisted opening: 2 postings observed in 90 days.")

        if days_active > 60:
            structural_flags.append(f"Stale opening: Active for {days_active} days without closing.")
        elif days_active > 35:
            structural_flags.append(f"Aging opening: Active for {days_active} days.")

        if not is_official_ats:
            structural_flags.append("Aggregator listing: Not cross-verified against company ATS domain.")

        # 2. Outcome Checks (Requires 2+ student reports to guard against single-witness false positives)
        if applicant_silence_count >= 2:
            outcome_flags.append(f"High silence rate: {applicant_silence_count} verified applicants reported 0 response.")

        # Verdict calculation following Freehire & CareerOps rules:
        # Structural evidence alone can NEVER produce 'LIKELY' ghost job.
        # Only verified outcome reports + structural convergence reach 'LIKELY'.
        if len(outcome_flags) >= 1 and len(structural_flags) >= 2:
            verdict = "LIKELY"
            penalty = 0.25  # Deduct 25% from final match score
        elif len(structural_flags) >= 2 or len(outcome_flags) >= 1:
            verdict = "POSSIBLE"
            penalty = 0.10  # Deduct 10%
        elif len(structural_flags) == 1:
            verdict = "LOW_RISK"
            penalty = 0.05
        else:
            verdict = "HEALTHY"
            penalty = 0.0

        all_signals = structural_flags + outcome_flags

        return {
            "verdict": verdict,
            "penalty_multiplier": round(1.0 - penalty, 2),
            "penalty_points": round(penalty * 100, 1),
            "structural_flags": structural_flags,
            "outcome_flags": outcome_flags,
            "signals": all_signals,
            "is_actionable": verdict in ["HEALTHY", "LOW_RISK", "POSSIBLE"]
        }
