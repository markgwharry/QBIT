# Status Sentinel Subsystem

> Addition to CLAUDE.md — QBIT repo. This section defines a new subsystem. Read the
> existing integration points below first and conform to their conventions for
> structure, config, logging, and MQTT client usage. Where this spec conflicts with
> an established repo pattern, prefer the repo pattern and flag the conflict rather
> than silently diverging.

### Existing components (on-device firmware, `firmware/src/`)

| Concern | Where it lives today |
|---|---|
| MQTT client, subscriptions, inbound callback | `network_task.cpp` — PubSubClient, `mqttCallback()`, subscribes in `mqttReconnect()`; buffer already 1024 bytes |
| Broker host / topic prefix / device ID | `settings.cpp` — `getMqttHost()`, `getMqttPrefix()` (default `qbit`), `getDeviceId()` |
| Home Assistant discovery + outbound state | `mqtt_ha.cpp` |
| Touch input (single pad) | `input_task.cpp` — gesture state machine → `gestureQueue` (`SINGLE_TAP`, `DOUBLE_TAP`, `LONG_PRESS` at 900 ms) |
| Display states and gesture dispatch | `app_state.h` (`DisplayState`), `display_task.cpp` |

`web/` (the Node/TypeScript pairing, poke and library service) is **not** an
integration point. The firmware's only use of it is the social layer, and both
are removed in phase 0 (see "Removed features").

### New components

- Firmware: a sentinel module (e.g. `sentinel.cpp/.h`) holding the priority stack,
  fed by new subscriptions in `network_task.cpp` and rendered from `display_task.cpp`.
- Off-device: a small **sentinel bridge** service (new, not part of `web/`) that
  receives Kuma and Clockify webhooks and publishes the MQTT contract below; plus
  per-host health scripts and the reminder helper. See "Source integrations".

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

### Removed features

The social layer is out of scope and is removed from the firmware rather than
integrated into the priority stack:

- Friend pokes, the WebSocket client to `web/backend`, and the server-offline overlay
  (`network_task.cpp` WebSocket section, `poke_handler.*`)
- Device claim and friend prompts (`CLAIM_PROMPT`, `FRIEND_PROMPT`, `POKE_DISPLAY`)
- The Home Assistant poke entities (`/command` poke, `/poke_text/set`, last-poke
  sensor in `mqtt_ha.cpp`) — superseded by `qbit/reminder`

- The HA `Server` connection binary sensor (`mqtt_ha.cpp`), which only reports
  the WebSocket link
- The whole `web/` stack (frontend, backend, admin, animation library, Docker
  Compose files): nothing else uses it
- `tools/qbit-ctl`, which only manages the `web/` backend's Docker container and data
- The `QBIT_WS_HOST` secret and `-DWS_HOST/-DWS_PORT` flags in
  `.github/workflows/build-and-release.yml`, and the `WS_HOST` comment in
  `firmware/platformio.ini`
- README sections on the web platform, self-hosting, claiming and friends (both
  `README.md` and `README.zh-TW.md`)

Kept: Wi-Fi provisioning, MQTT/HA discovery (mute, touch, animation), GIF playback,
the on-device web dashboard (`firmware/lib/web_dashboard`), the settings menu,
time, weather, OTA, and the GitHub Pages flasher (`tools/flasher`,
`deploy-gh-pages.yml`).

## Display state machine

One face, competing sources — resolved by a strict priority stack. Highest active
level wins the display.

| Priority | Level    | Trigger                                  | Behaviour |
|----------|----------|------------------------------------------|-----------|
| 1        | alert    | Kuma down event; health breach; stale heartbeat | Alarmed face + short label. Persists until acked (single tap) or auto-cleared by a matching recovery event. |
| 2        | reminder | Message on reminder topic                | Shown for `ttl_s`, then decays. Dismissable early via single tap. |
| 3        | ambient  | Clockify state                           | Idle face with a subtle indicator: project colour / timer-running glyph. Default when nothing else is active. |

Rules:

- Multiple simultaneous alerts: show the most recent with a count badge. Acking it
  reveals the next; there is no separate alert-paging gesture (the Kuma summary
  status page gives the overview).
- A cleared/acked alert must fall back to the next-highest active state, not to blank.
- Stale-heartbeat detection lives on QBIT (it is display-adjacent): if no health
  message from a known host within `heartbeat_timeout_s` (default 600), raise a
  synthetic alert for that host.

## MQTT contract

Retain the repo's existing broker config and PubSubClient instance in
`network_task.cpp`. `qbit` below is the configured `getMqttPrefix()`. Sentinel
topics are shared (not under `<device_id>`) so publishers need not know which QBIT
is listening. Topic scheme:

```
qbit/alert/<source>        # kuma | health | <future>
qbit/reminder
qbit/ambient/clockify
qbit/health/<host>         # heartbeats published by each host's cron
qbit/<device_id>/ack       # published by the firmware on dismiss/ack
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
  "ok": false,
  "checks": {
    "disk":  { "ok": false, "value": 93, "limit": 90, "text": "NAS disk 93%" },
    "raid":  { "ok": true,  "value": "ok" },
    "temp":  { "ok": true,  "value": 44,  "limit": 60 }
  },
  "ts": 1752940000
}
```

Thresholds are evaluated by the publishing script, not by QBIT; `limit` is
informational. `ok` is the AND of every `checks.*.ok`. Each heartbeat is a complete
snapshot of that host:

- For every check with `ok: false`, QBIT raises (or keeps) an alert with
  `id` = `health:<host>:<check>` and the check's `text` (fallback
  `"<host> <check>"`), severity `warning`.
- Any `health:<host>:*` alert whose check is absent or `ok: true` in the latest
  heartbeat is cleared, exactly as an `"up"` event clears a Kuma alert.
- Any heartbeat from `<host>` clears its stale alert, `health:<host>:stale`.

**Ack** — `qbit/<device_id>/ack` (published by the firmware)
```json
{ "action": "ack", "id": "kuma:wiki.wharry.co.uk", "ts": 1752940000 }
```
`action` is `"ack"` for an alert and `"dismiss"` for a reminder; `id` is the
alert or reminder `id`.

Use retained messages for `qbit/ambient/clockify` and `qbit/health/<host>` so state
survives a QBIT restart. Alerts and reminders are not retained.

## Touch behaviour

QBIT has one touch pad; gestures arrive on `gestureQueue` from `input_task.cpp`.
Each gesture has one meaning in every state, so the pad can be used without first
working out what the device is showing:

- **Single tap** — act on or advance what is on screen
- **Double tap** — status
- **Long press** — settings (unchanged)

| Showing | Single tap | Double tap | Long press |
|---|---|---|---|
| Alert | Ack; reveal the next alert or fall to the next level | Status pages | Settings menu |
| Reminder | Dismiss | Status pages | Settings menu |
| Ambient / idle | Next animation (unchanged) | Status pages | Settings menu |
| Status pages | Next page; exits after the last | Exit | Settings menu |

Status pages, in order: clock → Kuma summary (up/down counts, including acked
alerts still down) → NAS disk % → VPS disk % → today's Clockify total. The clock is
the existing double-tap view, now page 1.

- Leaving status pages — by double tap, by tapping past the last page, or after
  15 s with no touch — restores the **highest-priority active state**, not
  unconditionally idle.
- An alert arriving while status pages are shown pre-empts them immediately.
- **Accidental-ack guard:** ignore single taps for 1 s after an alert or reminder
  first appears, so a tap aimed at the previous screen cannot ack something unseen.
- Each ack/dismiss publishes the ack payload above to `qbit/<device_id>/ack`.

## Source integrations (off-device, but specced here for coherence)

All of these are **new**; none exists in the repo today. Keep the ones that ship
with QBIT under `tools/sentinel/` (alongside `tools/qbit-ctl`); host-specific
scripts may instead live on the hosts they monitor.

- **Sentinel bridge (new service):** a small standalone HTTP → MQTT bridge, run
  on the NAS in Docker.
- **Kuma → MQTT:** a `/kuma` route on the bridge that maps Kuma's webhook payload
  to the alert contract above. Map heartbeat status to `state`, monitor name to
  `id`/`text`.
- **Health heartbeats:** a small script per host (cron, every 5 min) gathering disk
  usage, RAID/SMART status, temperature, and publishing the heartbeat payload.
  Keep it dependency-light (stdlib + paho-mqtt).
- **Clockify:** add a route on the bridge to receive timer start/stop events (the existing
  Clockify webhook service on the VPS will forward, or POST directly) and publish
  the ambient payload. Separately, a scheduled check (cron on the NAS) queries the
  Clockify API on weekday mornings and publishes a reminder if no timer is running
  by 09:30.
- **Reminders:** plain cron entries publishing to `qbit/reminder`. Provide a tiny
  `publish_reminder` helper script so crontab lines stay one-liners.

## Build order

Implement and verify in phases; each phase should be independently useful:

0. Remove the social layer and `web/` (see "Removed features"); confirm the
   firmware builds in CI, and that provisioning, HA discovery, GIF playback, the
   on-device dashboard, settings, OTA and the Pages flasher still work.
1. Display state machine + priority stack + ack handling (testable with manual
   `mosquitto_pub`).
2. Sentinel bridge with the Kuma route → live alerts.
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
