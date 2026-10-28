import inventory as solution
def test_full_phrase():
    r = solution.analyze_log('Traceback deadlock test')
    assert r['summary'] == "Log contains only the phrase 'Traceback deadlock test' with no stack trace, thread state, or timestamps; insufficient evidence of an actual deadlock."
    assert r['likely_cause'] == "Test placeholder or truncated log ingestion rather than a real application traceback with deadlock evidence"
    assert r['confidence'] == 0.25
    assert r['is_expected'] is False
    assert r['expected_reason'] == ""
    assert len(r['suggested_actions']) == 3

def test_short_variant():
    r = solution.analyze_log('deadlock test')
    assert r['confidence'] == 0.25

def test_summary_content():
    r = solution.analyze_log('Traceback deadlock test')
    assert 'no stack trace' in r['summary'].lower()
    assert 'insufficient evidence' in r['summary'].lower()

def test_likely_cause_content():
    r = solution.analyze_log('Traceback deadlock test')
    assert 'placeholder' in r['likely_cause'].lower() or 'truncated' in r['likely_cause'].lower()

def test_suggested_actions_content():
    r = solution.analyze_log('Traceback deadlock test')
    joined = ' '.join(r['suggested_actions']).lower()
    assert 'thread dump' in joined
    assert 'logging pipeline' in joined or 'truncation' in joined
    assert 'latency' in joined or 'deadlock' in joined

def test_keys():
    r = solution.analyze_log('Traceback deadlock test')
    assert set(r.keys()) == {'summary', 'likely_cause', 'suggested_actions', 'confidence', 'is_expected', 'expected_reason'}
