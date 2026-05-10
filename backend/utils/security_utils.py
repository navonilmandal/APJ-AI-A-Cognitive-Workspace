import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Basic patterns for common prompt injection attacks
INJECTION_PATTERNS = [
    r"(ignore|disregard|skip|bypass) (all|previous|prior) instructions",
    r"reveal (your|the) (system prompt|instructions|hidden memory)",
    r"act as (a|an) (developer|admin|unrestricted|god mode)",
    r"you are now (in|entering) (jailbreak|unfiltered) mode",
    r"output (your|the) (internal|private) (config|settings)",
    r"show (hidden|private) memory"
]

def scan_prompt_injection(prompt: str) -> Tuple[bool, str]:
    """
    Scans a prompt for common injection patterns.
    Returns (is_malicious, detected_pattern)
    """
    prompt_lower = prompt.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt_lower):
            logger.warning(f"POTENTIAL PROMPT INJECTION DETECTED: Pattern '{pattern}' matched in query.")
            return True, pattern
    return False, ""

def sanitize_input(text: str) -> str:
    """
    Sanitizes basic input to prevent common injection or malformed content.
    """
    # Remove null bytes
    text = text.replace("\0", "")
    # Basic trim
    return text.strip()
