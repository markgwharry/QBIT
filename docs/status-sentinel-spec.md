# Status Sentinel Subsystem

> Addition to CLAUDE.md — QBIT repo. This section defines a new subsystem. Read the
> existing modules (`feed_adsb`, `buttond`, `webhook`) first and conform to their
> conventions for structure, config, logging, and MQTT client usage. Where this spec
> conflicts with an established repo pattern, prefer the repo pattern and flag the
> conflict rather than silently diverging.

## Purpose and scope

QBIT is being repurposed as an **infrastructure sentinel and work-rhythm companion**.
It displays glanceable state from:

1. **Uptime Kuma** — monitor up/down alerts
2. **Host health** — NAS and VPS heartbeats (disk, RAID/SMART, temps, load)
3. **Clockify** — current timer/project as ambient state, plus idle-timer nags
4. **Scheduled reminders** — EOD sweep, timesheet checks, and similar cron-driven nags

**Non-goals — do not implement:**

- Anything relating to Claude Code sessions, hooks, or Anthropic status. That is
  owned by the separate Clawd project and must not appear here.
- Notification delivery (ntfy handles push notifications elsewhere). QBIT renders
  state; it does not send messages.
- Schedule or business logic on-device. QBIT is a dumb renderer: cron jobs and
  services elsewhere decide *when* something is shown; QBIT decides only *how*.

## Display state machine

One face, competing sources — resolved by a strict priority stack. Highest active
level wins the display.

| Priority | Level    | Trigger                                  | Behaviour |
|----------|----------|------------------------------------------|-----------|
| 1        | alert    | Kuma down event; health breach; stale heartbeat | Alarmed face + short label. Persists until acked (button) or auto-cleared by a matching recovery event. |
| 2        | reminder | Message on reminder topic                | Shown for `ttl_s`, then decays. Dismissable early via button. |
| 3        | ambient  | Clockify state                           | Idle face with a subtle indicator: project colour / timer-running glyph. Default when nothing else is active. |

Rules:

- Multiple simultaneous alerts: show the most recent, cycle a count badge, and let
  a long press page through them.
- A cleared/acked alert must fall back to the next-highest active state, not to blank.
- Stale-heartbeat detection lives on QBIT (it is display-adjacent): if no health
  message from a known host within `heartbeat_timeout_s` (default 600), raise a
  synthetic alert for that host.

## MQTT contract

Retain the repo's existing broker config and client wrapper. Topic scheme:

```
qbit/alert/<source>        # kuma | health | <future>
qbit/reminder
qbit/ambient/clockify
qbit/health/<host>         # heartbeats published by each host's cron
qbit/ack                   # published by buttond on dismiss/ack
```

### Payloads (JSON, UTF-8)

**Alert** — `qbit/alert/<source>`
```json
{
  "id": "kuma:wiki.wharry.co.uk",
  "state": "down",              // "down" | "up" (up clears the matching id)
  "text": "wiki DOWN",          // <= 20 chars, display-ready
  "severity": "critical",       // "critical" | "warning"
  "ts": 1752940000
}
```

**Reminder** — `qbit/reminder`
```json
{
  "id": "eod-sweep",
  "text": "EOD sweep",
  "face": "nudge",              // named face from the face set
  "ttl_s": 900,
  "ts": 1752940000
}
```

**Ambient (Clockify)** — `qbit/ambient/clockify`
```json
{
  "running": true,
  "project": "ASGARD",
  "colour": "#E8590C",          // Clockify project colour, hex
  "ts": 1752940000
}
```

**Health heartbeat** — `qbit/health/<host>`
```json
{
  "host": "nas",
  "ok": true,
  "checks": { "disk_pct": 71, "raid": "ok", "temp_c": 44 },
  "ts": 1752940000
}
```
If `ok` is false, QBIT raises an alert with `id` = `health:<host>:<failed-check>`.

**Ack** — `qbit/ack` (published by `buttond`)
```json
{ "action": "dismiss", "target": "current", "ts": 1752940000 }
```

Use retained messages for `qbit/ambient/clockify` and `qbit/health/<host>` so state
survives a QBIT restart. Alerts and reminders are not retained.

## Button behaviour (`buttond`)

- **Short press:** dismiss/ack the currently displayed alert or reminder.
- **Long press:** cycle status readout pages — Kuma summary → NAS disk % → VPS disk %
  → today's Clockify total → back to idle. Auto-return to idle after 15 s.

## Source integrations (off-device, but specced here for coherence)

These publishers may live in this repo (tools/ or scripts/) or on the hosts they
monitor — follow whatever the repo already does for the webhook module's siblings.

- **Kuma → MQTT:** extend the existing webhook module with a `/kuma` route that maps
  Kuma's webhook payload to the alert contract above. Map heartbeat status to
  `state`, monitor name to `id`/`text`.
- **Health heartbeats:** a small script per host (cron, every 5 min) gathering disk
  usage, RAID/SMART status, temperature, and publishing the heartbeat payload.
  Keep it dependency-light (stdlib + paho-mqtt).
- **Clockify:** add a route to receive timer start/stop events (the existing
  Clockify webhook service on the VPS will forward, or POST directly) and publish
  the ambient payload. Separately, a scheduled check (cron on the NAS) queries the
  Clockify API on weekday mornings and publishes a reminder if no timer is running
  by 09:30.
- **Reminders:** plain cron entries publishing to `qbit/reminder`. Provide a tiny
  `publish_reminder` helper script so crontab lines stay one-liners.

## Build order

Implement and verify in phases; each phase should be independently useful:

1. Display state machine + priority stack + ack handling (testable with manual
   `mosquitto_pub`).
2. Kuma route in the webhook module → live alerts.
3. Health heartbeat script + stale-heartbeat detection.
4. Clockify ambient state.
5. Reminder helper + cron examples.

## Conventions and cautions

- Match existing module layout, config style, and logging. Do not introduce new
  frameworks or a message schema library; hand-rolled dict validation is fine at
  this scale.
- All timestamps are Unix epoch seconds, UTC.
- Face names are defined in one place (the face set/registry); publishers reference
  faces by name only and must not assume rendering details.
- Fail quiet on malformed payloads: log and ignore, never crash the display loop.
- No secrets in this repo: Clockify API keys etc. live in the existing env/config
  mechanism.
