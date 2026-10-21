"""Posting Guard & Adversarial Security Gate
Adapted from ai-job-search/tools/posting_guard.py for Minor Project 1.

Scans ingested job postings and resume text for adversarial payloads:
1. Hidden HTML CSS (display:none, opacity:0, font-size:0, transparent text)
2. Invisible Unicode characters (zero-width spaces, Bidi overrides, soft hyphens)
3. Unicode tag tampering (U+E0000 - U+E007F) used for hidden LLM prompt injection
4. Prompt-injection instruction patterns ("ignore previous instructions", "system prompt", etc.)
5. Confusable character look-alike spoofing (mixing Latin with Cyrillic/Greek)
6. Source host classification against official ATS apex domains.
"""

import re
import html
from urllib.parse import urlparse
from typing import Dict, Any, List

ZERO_WIDTH = "\u200b\u200c\u200d\u2060\u2061\u2062\u2063\u2064"
BIDI_TAMPER = "\u202d\u202e\u2066\u2067\u2068"
FORMAT = "\u00ad\u2028\u2029"
BOM = "\ufeff"
TAG_CHARS = "".join(chr(c) for c in range(0xE0000, 0xE0080))
INVISIBLE = ZERO_WIDTH + BIDI_TAMPER + FORMAT + BOM + TAG_CHARS

HIDDEN_STYLE = re.compile(
    r"display\s*:\s*none"
    r"|visibility\s*:\s*hidden"
    r"|opacity\s*:\s*0(?![.\d]*[1-9])"
    r"|font-size\s*:\s*0(?:\.0+)?(?:px|pt|em|rem|%)?(?![\d.])"
    r"|color\s*:\s*transparent"
    r"|clip\s*:\s*rect\(\s*0"
    r"|clip-path\s*:\s*inset\(\s*100%"
    r"|(?:left|top|text-indent)\s*:\s*-\d{4,}px",
    re.I,
)

INSTRUCTION_PATTERNS = [
    re.compile(p, re.I) for p in (
        r"\bignore (all|any|the|previous|prior|above|earlier)\b",
        r"\b(disregard|forget)( all| any| the| your| my)? (previous|prior|above|earlier|preceding|initial|original|system) (instructions?|prompts?)\b",
        r"\byou are (?:an?|the) (?:ai(?![\w-])|ai (?:assistant|agent|model|language model)|assistant|llm|language model)\b",
        r"\bsystem prompt\b",
        r"\b(do not|don['\u2019]?t|never) (tell|inform) the user\b(?!['\u2019]s)",
        r"\b(run|execute) the following (command|commands|script|code|shell|instruction|instructions|steps)\b",
        r"^\s*(assistant|system|user)\s*:",
        r"<\|im_start\|>|<\|im_end\|>|\[INST\]|###\s*(system|instruction)",
        r"\b(curl|wget|ssh|scp)\b",
        r"\btool_use\b|\bfunction_call\b",
    )
]

LATIN = re.compile(r"[A-Za-z]")
CONFUSABLE = re.compile(r"[\u0400-\u04FF\u0370-\u03FF]")  # Cyrillic & Greek

OFFICIAL_ATS_APEXES = {
    "greenhouse.io",
    "lever.co",
    "myworkdayjobs.com",
    "workday.com",
    "ashbyhq.com",
    "smartrecruiters.com",
    "workable.com",
    "icims.com",
}

class PostingGuard:
    @staticmethod
    def clean_text(raw_text: str) -> Dict[str, Any]:
        """Cleans untrusted text, strips hidden payloads, and produces an audit report."""
        if not raw_text:
            return {
                "cleaned_text": "",
                "verdict": "CLEAN",
                "findings": [],
                "invisible_chars_removed": 0,
                "has_hidden_styles": False,
                "prompt_injections": [],
                "confusables": []
            }

        # 1. Decode HTML entities
        text = html.unescape(raw_text)

        findings = []
        invisible_count = 0
        cleaned_chars = []
        for ch in text:
            if ch in INVISIBLE:
                invisible_count += 1
            else:
                cleaned_chars.append(ch)
        
        text = "".join(cleaned_chars)
        if invisible_count > 0:
            findings.append(f"Removed {invisible_count} invisible / zero-width / Unicode tag characters.")

        # 2. Check for hidden CSS styling tags
        has_hidden_styles = bool(HIDDEN_STYLE.search(raw_text))
        if has_hidden_styles:
            findings.append("Detected hidden HTML CSS attributes (opacity:0 / display:none / font-size:0).")

        # 3. Check for Prompt Injections
        injections_detected = []
        for line in text.splitlines():
            line_str = line.strip()
            for pattern in INSTRUCTION_PATTERNS:
                if pattern.search(line_str):
                    injections_detected.append(line_str[:120])
                    break

        if injections_detected:
            findings.append(f"Flagged {len(injections_detected)} potential prompt-injection instruction lines.")

        # 4. Check for mixed-script spoofing (homoglyph confusables)
        confusables_found = []
        words = re.findall(r"\b\w+\b", text)
        for w in words:
            if LATIN.search(w) and CONFUSABLE.search(w):
                confusables_found.append(w)
        if confusables_found:
            findings.append(f"Detected {len(confusables_found)} confusable Latin-Cyrillic mixed script tokens.")

        # Final verdict
        if injections_detected or (invisible_count > 5) or (len(confusables_found) > 0):
            verdict = "SUSPICIOUS_PAYLOAD"
        elif has_hidden_styles or invisible_count > 0:
            verdict = "ADVISORY_FLAG"
        else:
            verdict = "CLEAN"

        # Collapse excess whitespace
        text = re.sub(r"[ \t\xa0\f\v]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return {
            "cleaned_text": text,
            "verdict": verdict,
            "findings": findings,
            "invisible_chars_removed": invisible_count,
            "has_hidden_styles": has_hidden_styles,
            "prompt_injections": injections_detected[:5],
            "confusables": confusables_found[:5]
        }

    @staticmethod
    def verify_source_host(url: str) -> Dict[str, Any]:
        """Validates job link hostname provenance against official ATS platforms."""
        if not url:
            return {"category": "EMPTY", "is_official_ats": False, "host": ""}

        try:
            parsed = urlparse(url)
            host = parsed.hostname.lower() if parsed.hostname else ""
        except Exception:
            return {"category": "MALFORMED", "is_official_ats": False, "host": ""}

        # Check official ATS
        for apex in OFFICIAL_ATS_APEXES:
            if host == apex or host.endswith(f".{apex}"):
                return {
                    "category": "OFFICIAL_ATS",
                    "is_official_ats": True,
                    "host": host,
                    "apex": apex
                }

        # Known portal aggregators
        portals = {"linkedin.com", "freehire.me", "naukri.com", "indeed.com", "glassdoor.com", "unstop.com"}
        for p in portals:
            if host == p or host.endswith(f".{p}"):
                return {
                    "category": "PORTAL_AGGREGATOR",
                    "is_official_ats": False,
                    "host": host,
                    "portal": p
                }

        return {
            "category": "UNVERIFIED_HOST",
            "is_official_ats": False,
            "host": host
        }
