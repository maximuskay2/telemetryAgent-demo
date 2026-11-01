# AutoParts Lagos Inventory Service — Telemetry Setup Manual

Owner: Maximusinfotech Services. Contact: maximuskay2@gmail.com.
Repository: github.com/maximuskay2/telemetryAgent-demo.
Kind: software service (Python inventory locking behind the AutoParts Lagos shop).
Location: Railway, europe-west4.

Upload this file at the **Teach normal** step. Sections 1–4 are read
automatically, one quoted sentence per value. Sections 5 and 6 are *not*
read from documents by design: type them into the Review screen by hand.

## 1. Normal ranges

- Order error rate stays between 0% and 1% in any 5-minute window.
- Order p95 latency stays between 5 ms and 300 ms.
- Retry lines stay between 0 and 1 per item in any 30-second window.
- Normal traffic is 10–40 orders per minute during opening hours (8:00–20:00 Africa/Lagos).

## 2. Expected behaviours (look scary, are normal)

- At startup the service logs WARN cache cold, warming exactly once while the SKU cache fills, and this needs no action.
- A single WARNING retry=1 ... (lock wait timeout) line during a busy minute is normal lock contention, as long as the error rate stays under 1%.
- A retried order backs off 20 ms, then 40 ms, then 80 ms before its next attempt, and a retry that then succeeds is a normal order.
- After a restart the service is unavailable for at most 5 seconds while the worker re-executes, and no orders fail during that gap.

## 3. Modes

- Deploy mode (POST /deploy) lasts at most 60 seconds, and during it a few retry=1 ... (deploy drain) lines are expected while connections drain.
- In deploy mode the error rate must still stay under 1%.
- After the deploy window ends, retries must stop within 30 seconds.
- Fix-reload mode (POST /reload with a verified patch) lasts at most 10 seconds, and a brief gap in order logs is expected during it.

## 4. Failure definitions (what really counts as broken)

- A single deadlock detected while acquiring lock on inventory_items is a failure at once, even if the transaction was rolled back.
- A retry storm is 2 or more retry lines on the same items within 30 seconds outside deploy mode.
- An outage is an order error rate above 5% for 30 seconds or longer.
- A slowdown is an order p95 latency above 300 ms for 60 seconds or longer.
- Any Traceback (most recent call last) in the service log is a failure.

## 5. Hard limits — enter by hand on the Review screen

These are the safety floor: the gate checks them first and never
suppresses them, even during a deploy. They are never taken from documents,
so add each row under **Hard limits** yourself.

| Metric | Op | Threshold | Meaning |
| --- | --- | --- | --- |
| `error_rate` | `>` | `0.5` | Over 50% of orders failing is a critical emergency, even during a deploy. |
| `p95_ms` | `>` | `1000` | An order p95 latency above 1 second is never normal. |
| `retry` | `>` | `10` | More than 10 retry lines in 30 seconds means locks are wedged. |

## 6. Policy — enter by hand on the Review screen

- **Allowed actions:** `rollback`, `restart` (through the signed deploy
  webhook at `https://deploy-hook-production-6c1c.up.railway.app/deploy`).
- **Forbidden actions:** push to `main`, delete order history, delete or
  edit the `inventory_items` table, edit the SKU catalog, scale to zero.
- **Auto-fix:** allowed; fixes arrive only as pull requests from
  `telemetry-agent/fix-*` branches and need a passing `pytest` run.
- **Veto countdown:** 20 seconds.
- **Alert contact:** maximuskay2@gmail.com.

## 7. Reference: where the numbers come from

| Fact | Value | Source |
| --- | --- | --- |
| Lock wait before a retry | 100 ms | `ACQUIRE_TIMEOUT_S` in the shop |
| Lock hold per order | 8 ms | `HOLD_S` |
| Attempts before an order fails | 3 | `MAX_ATTEMPTS` |
| Retry backoff | 20 / 40 / 80 ms | `min(100, 10 * 2**attempt)` |
| Retry-storm rule | ≥ 2 on one item in 30 s | TelemetryAgent log watcher |
| Deploy drain lines | 4 × `retry=1 items=axle,brake-pad` | `POST /deploy` |
| Seeded bug | `acquire_all` locks in caller order, not sorted order | `inventory.py` |
| Correct contract | locks taken in sorted item order | `test_acquire_all_uses_canonical_order` |
