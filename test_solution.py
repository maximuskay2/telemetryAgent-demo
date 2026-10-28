import solution

def test_single_char_x_is_malformed():
    r = solution.analyze_telemetry('x', source_id='api')
    assert r['is_expected'] is False
    assert r['confidence'] == 0.95
    assert r['expected_reason'] == ''
    assert 'x' in r['summary']
    assert 'Malformed telemetry payload' in r['summary']
    assert 'Truncated log transmission' in r['likely_cause']
    assert len(r['suggested_actions']) == 3

def test_reference_payload_exact_match():
    r = solution.analyze_telemetry('x', source_id='api')
    assert r['summary'] == "Malformed telemetry payload containing only single character 'x' with no structured software log content"
    assert 'api' in r['likely_cause']
    assert 'Validate logger configuration for source_id api' in r['suggested_actions'][0]

def test_valid_structured_payload_is_expected():
    payload = {'timestamp': '2026-10-28T00:00:00Z', 'level': 'INFO', 'message': 'hello world'}
    r = solution.analyze_telemetry(payload, source_id='api')
    assert r['is_expected'] is True
    assert r['confidence'] >= 0.99
    assert r['expected_reason'] != ''

def test_empty_and_none_malformed():
    for p in [None, '', '   ']:
        r = solution.analyze_telemetry(p, source_id='api')
        assert r['is_expected'] is False
        assert r['confidence'] >= 0.9

def test_aliases_and_helpers():
    assert solution.validate_payload('x')['is_expected'] is False
    assert solution.validate_telemetry('x')['is_expected'] is False
    assert solution.is_malformed('x') is True
    assert solution.is_expected('x') is False
    assert solution.is_expected({'timestamp': '2026-10-28T00:00:00Z', 'level': 'ERROR', 'message': 'boom'}) is True
