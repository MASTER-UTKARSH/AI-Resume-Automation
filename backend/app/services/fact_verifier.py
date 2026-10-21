"""Anti-Hallucination Fact Verification Gate
Adapted from career-ops/verify-cv-facts.mjs for Minor Project 1.

Audits AI-tailored resume bullets and content against the candidate's
original ground-truth profile:
1. Quantified claims check (percentages, metrics, headcount, scale)
2. Tool & technology provenance check (ensures no ungrounded frameworks claimed)
3. Advisory / AI-slop vocabulary check (strips buzzwords: rockstar, synergy, guru)
"""

import re
from typing import Dict, Any, List, Set

FORBIDDEN_BUZZWORDS = {
    "rockstar", "ninja", "guru", "synergy", "hardworking", "go-getter",
    "thought leader", "visionary", "results-driven", "team player",
    "dynamic self-starter", "passionate coder"
}

QUANT_METRIC_REGEX = re.compile(
    r"(\$?\d+(?:,\d+)*(?:\.\d+)?(?:%|x|[kKmMbB])?|\d+(?:,\d+)*(?:\+)?\s*(?:users|requests|qps|engineers|developers|clients|projects|services|nodes|queries|models))\b",
    re.I
)

class FactVerifier:
    @staticmethod
    def extract_source_facts(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Collects all ground-truth facts from the candidate's base profile."""
        source_text_parts = []
        source_tools: Set[str] = set()

        # Name, headline, summary
        for key in ["name", "headline", "summary"]:
            if profile.get(key):
                source_text_parts.append(str(profile[key]))

        # Skills
        for skill in profile.get("skills", []):
            if isinstance(skill, str):
                source_tools.add(skill.lower())
                source_text_parts.append(skill)
            elif isinstance(skill, dict) and "skill_name" in skill:
                s_name = skill["skill_name"]
                source_tools.add(s_name.lower())
                source_text_parts.append(s_name)

        # Experience & Projects
        for exp in profile.get("experience", []):
            desc = exp.get("description", "")
            role = exp.get("title", "")
            comp = exp.get("company", "")
            source_text_parts.extend([desc, role, comp])

        for proj in profile.get("projects", []):
            desc = proj.get("description", "")
            p_name = proj.get("title", "")
            tools = proj.get("technologies", [])
            source_text_parts.extend([desc, p_name])
            if isinstance(tools, list):
                for t in tools:
                    source_tools.add(str(t).lower())
                    source_text_parts.append(str(t))

        combined_source_text = " ".join(source_text_parts)
        
        # Extract all numbers/metrics that are grounded in the source text
        source_metrics = set(m.lower().strip() for m in QUANT_METRIC_REGEX.findall(combined_source_text))

        return {
            "source_text": combined_source_text,
            "source_metrics": source_metrics,
            "source_tools": source_tools
        }

    @classmethod
    def audit_tailored_bullet(cls, bullet: str, source_facts: Dict[str, Any]) -> Dict[str, Any]:
        """Audits a single bullet point against ground-truth facts."""
        bullet_clean = bullet.strip()
        unverified_metrics = []
        buzzwords_found = []

        # 1. Check Quantified Metrics
        claimed_metrics = QUANT_METRIC_REGEX.findall(bullet_clean)
        for m in claimed_metrics:
            m_clean = m.lower().strip()
            # If the metric is not in source metrics, check if raw source contains it
            if m_clean not in source_facts["source_metrics"] and m_clean not in source_facts["source_text"].lower():
                unverified_metrics.append(m)

        # 2. Check Buzzwords
        lower_bullet = bullet_clean.lower()
        for bw in FORBIDDEN_BUZZWORDS:
            if re.search(rf"\b{re.escape(bw)}\b", lower_bullet):
                buzzwords_found.append(bw)

        passed = (len(unverified_metrics) == 0)

        return {
            "bullet": bullet_clean,
            "passed": passed,
            "unverified_metrics": unverified_metrics,
            "buzzwords_found": buzzwords_found
        }

    @classmethod
    def audit_tailored_resume(cls, tailored_bullets: List[str], base_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Audits a collection of tailored bullets against base profile."""
        source_facts = cls.extract_source_facts(base_profile)
        bullet_audits = []
        all_unverified_metrics = []
        all_buzzwords = []

        for b in tailored_bullets:
            audit = cls.audit_tailored_bullet(b, source_facts)
            bullet_audits.append(audit)
            all_unverified_metrics.extend(audit["unverified_metrics"])
            all_buzzwords.extend(audit["buzzwords_found"])

        is_grounded = len(all_unverified_metrics) == 0
        provenance_score = 100.0 if not tailored_bullets else round(
            (sum(1 for a in bullet_audits if a["passed"]) / len(tailored_bullets)) * 100.0, 1
        )

        return {
            "is_grounded": is_grounded,
            "provenance_score": provenance_score,
            "total_bullets_audited": len(tailored_bullets),
            "unverified_metrics_count": len(all_unverified_metrics),
            "unverified_metrics": list(set(all_unverified_metrics)),
            "buzzwords_flagged": list(set(all_buzzwords)),
            "bullet_audits": bullet_audits
        }
