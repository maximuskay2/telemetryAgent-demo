# TelemetryAgent demo target

The service that [TelemetryAgent](https://github.com/maximuskay2/telemetryAgent) repairs on its own.

`inventory.py` contains a seeded lock-ordering bug: two orders that lock the same items in opposite order deadlock. When the AutoParts Lagos demo shop hits it under load, TelemetryAgent:

1. catches the retries and deadlocks in the shop log,
2. diagnoses the root cause with Muse Spark,
3. writes a patch and a regression test with Muse Spark Open,
4. proves the test fails on this file and passes on the patch inside a sandbox,
5. opens a pull request here.

Every `telemetry-agent/fix-*` pull request in this repository was written and verified by the agent.

Run the tests: `python -m pytest -q` (stdlib only, plus pytest).
