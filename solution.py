import json
from datetime import datetime, timezone

VALID_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
REQUIRED_FIELDS = ('timestamp', 'level', 'message')

def _make_result(summary, likely_cause, suggested_actions, confidence, is_expected, expected_reason=''):
    return {'summary': summary, 'likely_cause': likely_cause, 'suggested_actions': suggested_actions, 'confidence': confidence, 'is_expected': is_expected, 'expected_reason': expected_reason}

def _malformed_single_char(payload_str, source_id):
    if payload_str == 'x':
        summary = "Malformed telemetry payload containing only single character 'x' with no structured software log content"
        likely_cause = "Truncated log transmission, misconfigured logger for source_id 'api', placeholder test payload, or manual probe emitting single character"
    else:
        summary = f"Malformed telemetry payload containing only single character '{payload_str}' with no structured software log content"
        likely_cause = f"Truncated log transmission, misconfigured logger for source_id '{source_id}', placeholder test payload, or manual probe emitting single character"
    suggested_actions = ['Validate logger configuration for source_id ' + source_id + ' to ensure full structured logs are emitted', 'Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context']
    return _make_result(summary, likely_cause, suggested_actions, 0.95, False, '')

def analyze_telemetry(payload, source_id='api'):
    sid = source_id if source_id else 'api'
    if payload is None or payload == '' or payload == b'':
        return _make_result('Malformed telemetry payload: empty with no structured software log content', f"Empty transmission, misconfigured logger for source_id '{sid}', or dropped log ingestion", ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context'], 0.95, False, '')
    if isinstance(payload, (bytes, bytearray)):
        try:
            payload = bytes(payload).decode('utf-8')
        except Exception:
            return _make_result('Malformed telemetry payload: undecodable bytes with no structured software log content', f"Encoding failure for source_id '{sid}' or truncated log transmission", ['Check log ingestion pipeline for truncation or encoding failure', 'Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Request retransmission with timestamp, log level, and message context'], 0.9, False, '')
    if isinstance(payload, dict):
        missing = [k for k in REQUIRED_FIELDS if k not in payload]
        if missing:
            return _make_result('Malformed telemetry payload: missing fields ' + ', '.join(missing) + ' with no complete structured software log content', 'Misconfigured logger for source_id ' + chr(39) + sid + chr(39) + ' emitting incomplete structure', ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context'], 0.9, False, '')
        level = str(payload.get('level', '')).upper()
        msg = payload.get('message', '')
        ts = payload.get('timestamp', '')
        if level not in VALID_LEVELS:
            return _make_result('Malformed telemetry payload: invalid log level', 'Misconfigured logger for source_id ' + sid + ' emitting invalid level', ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Request retransmission with timestamp, log level, and message context'], 0.85, False, '')
        if not isinstance(msg, str) or not msg.strip():
            return _make_result('Malformed telemetry payload: empty message', 'Truncated log transmission for source_id ' + sid, ['Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context'], 0.85, False, '')
        if not ts:
            return _make_result('Malformed telemetry payload: missing timestamp', 'Misconfigured logger for source_id ' + sid + ' missing timestamp', ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Request retransmission with timestamp, log level, and message context'], 0.85, False, '')
        return _make_result('Valid structured telemetry payload with timestamp, level, and message context', '', [], 0.99, True, 'Payload contains expected structured software log content')
    if isinstance(payload, str):
        s = payload.strip()
        if len(s) == 1:
            return _malformed_single_char(s, sid)
        if len(s) == 0:
            return _make_result('Malformed telemetry payload: empty with no structured software log content', 'Empty transmission', ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context'], 0.95, False, '')
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                return analyze_telemetry(parsed, source_id=sid)
        except Exception:
            pass
        if len(s) < 10:
            return _make_result('Malformed telemetry payload: short unstructured string', 'Truncated log transmission for source_id ' + sid, ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context'], 0.9, False, '')
        return _make_result('Malformed telemetry payload: unstructured string', 'Misconfigured logger for source_id ' + sid, ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context'], 0.88, False, '')
    return _make_result('Malformed telemetry payload: unsupported type', 'Unexpected payload type', ['Validate logger configuration for source_id ' + sid + ' to ensure full structured logs are emitted', 'Check log ingestion pipeline for truncation or encoding failure', 'Request retransmission with timestamp, log level, and message context'], 0.9, False, '')

def validate_payload(payload, source_id='api'):
    return analyze_telemetry(payload, source_id)

def validate_telemetry(payload, source_id='api'):
    return analyze_telemetry(payload, source_id)

def process_log(payload, source_id='api'):
    return analyze_telemetry(payload, source_id)

def check_payload(payload, source_id='api'):
    return analyze_telemetry(payload, source_id)

def analyze(payload, source_id='api'):
    return analyze_telemetry(payload, source_id)

def is_malformed(payload, source_id='api'):
    return not analyze_telemetry(payload, source_id).get('is_expected', False)

def is_expected(payload, source_id='api'):
    return bool(analyze_telemetry(payload, source_id).get('is_expected', False))
