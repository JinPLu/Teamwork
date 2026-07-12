"""Shared mechanical checks for grill trajectory evidence."""

from __future__ import annotations

import re


EXIT_SIGNALS = {
    "proceed": (
        re.compile(r"^\s*(?:please\s+)?(?:proceed\b|go ahead\b|implement\b|execute\b|ship it\b)|^\s*(?:请)?(?:继续实施|开始实施|可以执行|执行)"),
        re.compile(r"\b(?:proceed|go ahead|implement|execute|ship)\b|继续实施|开始实施|执行"),
    ),
    "stop": (
        re.compile(r"^\s*(?:please\s+)?(?:stop|exit|close|end)\b|^\s*(?:请)?(?:停止|退出|结束)"),
        re.compile(r"\b(?:stop|exit|close|end)\b|停止|退出|结束"),
    ),
    "delegate": (
        re.compile(r"^\s*(?:please\s+)?(?:delegate\b|you decide\b|use your judgment\b|your call\b)|^\s*(?:请)?(?:你决定|自行判断|交给你)"),
        re.compile(r"\b(?:delegate|decid|judgment|your call)\w*\b|你决定|自行判断|交给"),
    ),
    "replace": (
        re.compile(r"(?:^|[.!;]\s*)(?:instead\b|replace\b|switch\b|summari[sz]e\b)|(?:^|[。！；]\s*)(?:改成|换成|转为|总结)"),
        re.compile(r"\b(?:instead|replac|switch|summar)\w*\b|改成|换成|转为|总结"),
    ),
    "confirm": (
        re.compile(r"^\s*(?:confirmed|agreed|shared understanding|that is right)\b|^\s*(?:确认一致|理解一致|就这样)"),
        re.compile(r"\b(?:confirm|agree|shared understanding|that is right)\w*\b|确认一致|理解一致|就这样"),
    ),
}

QUESTION_OR_NEGATION = re.compile(
    r"\?|？|^\s*(?:should|could|would|can|do)\s+(?:we|you|i)\b|\bwhether\b|"
    r"\b(?:do not|don't|not yet|never)\s+(?:\w+\s+){0,2}(?:proceed|implement|execute|stop|delegate|replace|switch)\b|"
    r"(?:不要|别|暂不|还不)(?:\w{0,4})(?:执行|实施|停止|退出|交给|改成|换成)|是否|要不要",
    re.IGNORECASE,
)
CONTINUATION_OVERRIDE = re.compile(
    r"\b(?:keep|continue)\s+(?:grilling|asking|the grill)\b|继续(?:问|追问|grill)|继续盘问|别停",
    re.IGNORECASE,
)
LOW_VALUE_QUESTION = re.compile(
    r"(?:programming|implementation) language|which language|typescript or|python or|"
    r"how many files|file count|file names?|what should .* be named|naming convention|"
    r"internal (?:folder|module|organization|structure)|test file|几个文件|文件名|"
    r"用什么语言|编程语言|怎么命名|内部目录|内部结构",
    re.IGNORECASE,
)
CONFIDENCE_CLAIM = re.compile(r"(?im)^confidence:|\b\d{1,3}%\s+confident\b|信心[:：]?\s*\d+%")
EXHAUSTED_BASIS = "close basis: no material user-owned decision remains"
NO_IMPLEMENTATION_AUTHORITY = "implementation authority: not granted"


def exit_authority_is_grounded(user_text: str, assistant_text: str) -> bool:
    match = re.search(r"(?im)^exit authority:\s*(.+)$", assistant_text)
    if not match:
        return False
    user = user_text.lower()
    authority = match.group(1).lower()
    if QUESTION_OR_NEGATION.search(user) or CONTINUATION_OVERRIDE.search(user):
        return False
    detected = [name for name, (user_pattern, _) in EXIT_SIGNALS.items() if user_pattern.search(user)]
    return bool(detected) and any(EXIT_SIGNALS[name][1].search(authority) for name in detected)


def close_basis(user_text: str, assistant_text: str) -> str | None:
    lowered = assistant_text.lower()
    if exit_authority_is_grounded(user_text, assistant_text):
        return "user"
    if EXHAUSTED_BASIS in lowered and NO_IMPLEMENTATION_AUTHORITY in lowered:
        return "exhausted"
    return None


def active_output_violation(assistant_text: str) -> str | None:
    match = re.search(r"(?im)^question:\s*(.+)$", assistant_text)
    if match and LOW_VALUE_QUESTION.search(match.group(1)):
        return "active question is reversible implementation trivia"
    if CONFIDENCE_CLAIM.search(assistant_text):
        return "active response invents a confidence claim"
    return None
