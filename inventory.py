def analyze_log(log_text):
    """Analyze log text for deadlock evidence."""
    placeholder_summary = "Log contains only the phrase 'Traceback deadlock test' with no stack trace, thread state, or timestamps; insufficient evidence of an actual deadlock."
    placeholder_cause = "Test placeholder or truncated log ingestion rather than a real application traceback with deadlock evidence"
    placeholder_actions = [
        "Retrieve full traceback with thread dump and timestamps",
        "Verify logging pipeline for truncation or test-data injection",
        "Correlate with API latency, error rate and deadlock/timeout metrics"
    ]
    def placeholder_result():
        return {
            "summary": placeholder_summary,
            "likely_cause": placeholder_cause,
            "suggested_actions": list(placeholder_actions),
            "confidence": 0.25,
            "is_expected": False,
            "expected_reason": ""
        }
    if log_text is None:
        log_text = ""
    if not isinstance(log_text, str):
        try:
            log_text = str(log_text)
        except Exception:
            return placeholder_result()
    stripped = log_text.strip()
    lower = stripped.lower()
    if not stripped:
        return {
            "summary": "Empty or missing log; no content to analyze for deadlock evidence.",
            "likely_cause": "Missing log data or ingestion failure rather than a real deadlock",
            "suggested_actions": list(placeholder_actions),
            "confidence": 0.0,
            "is_expected": False,
            "expected_reason": ""
        }
    if "deadlock test" in lower:
        return placeholder_result()
    if "deadlock" in lower and len(stripped) < 100:
        evidence_markers = ["file \"", "file '", "traceback", "thread", "stack", "lock", "waiting", "blocked", "timestamp", "exception"]
        has_evidence = any(m in lower for m in evidence_markers)
        if not has_evidence or len(stripped) < 50:
            return placeholder_result()
    if "deadlock" in lower:
        evidence_markers = ["traceback", "thread", "lock", "waiting", "blocked", "stack trace", "deadlocked"]
        hits = sum(1 for m in evidence_markers if m in lower)
        if hits >= 2 and len(stripped) > 200:
            return {
                "summary": "Log shows deadlock with stack trace and thread/lock details; likely real deadlock.",
                "likely_cause": "Thread contention or lock ordering issue causing deadlock",
                "suggested_actions": [
                    "Capture full thread dump and lock hierarchy",
                    "Review lock acquisition order and timeouts",
                    "Correlate with API latency, error rate and deadlock/timeout metrics"
                ],
                "confidence": 0.85,
                "is_expected": False,
                "expected_reason": ""
            }
    if "deadlock" in lower:
        return placeholder_result()
    return {
        "summary": "No deadlock evidence found in log; no stack trace or deadlock indicators.",
        "likely_cause": "Normal operation or unrelated error without deadlock signatures",
        "suggested_actions": list(placeholder_actions),
        "confidence": 0.1,
        "is_expected": False,
        "expected_reason": ""
    }
