#!/usr/bin/env python3
"""fable-watch sensor — is Claude Fable 5 available on the Anthropic API again?

Runs in GitHub Actions on a schedule. Hits the Anthropic /v1/models endpoint
(authoritative: it lists what your account can actually use), looks for any
model id containing "fable", and updates status.json. On an offline->online
flip it pushes a phone notification via ntfy.sh. Never false-positives on a
network/API error (treats errors as "no change"). stdlib only — no pip.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NTFY = os.environ.get("NTFY_TOPIC", "").strip()
STATUS = "status.json"
DEFAULT_SINCE = "2026-06-12T00:00:00Z"   # the day the lights went out


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load():
    try:
        return json.load(open(STATUS))
    except Exception:
        return {"available": False, "model_id": None, "last_checked": None, "since": DEFAULT_SINCE}


def probe():
    """Return (ok, available, model_id). ok=False => change nothing (error-safe)."""
    if not KEY:
        print("no ANTHROPIC_API_KEY set", file=sys.stderr)
        return (False, None, None)
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": KEY, "anthropic-version": "2023-06-01"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"probe error (treating as no-change): {e}", file=sys.stderr)
        return (False, None, None)
    ids = [m.get("id", "") for m in data.get("data", [])]
    hits = [i for i in ids if "fable" in i.lower()]
    return (True, bool(hits), hits[0] if hits else None)


def notify(model_id):
    if not NTFY or NTFY.startswith("CHANGE"):
        print("ntfy topic not configured — skipping push", file=sys.stderr)
        return
    body = f"FABLE 5 IS BACK ONLINE — {model_id or 'available now'}. Go.".encode()
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY}",
            data=body,
            headers={"Title": "ACCESS RESTORED", "Priority": "max", "Tags": "rotating_light"},
        )
        urllib.request.urlopen(req, timeout=10)
        print("push sent")
    except Exception as e:
        print(f"notify error: {e}", file=sys.stderr)


def main():
    ok, available, model_id = probe()
    if not ok:
        print("probe failed — no change")
        return

    s = load()
    prev = bool(s.get("available"))

    # Heartbeat: refresh last_checked at most ~twice a day even when nothing
    # changes, so the page never looks dead — without spamming 96 commits/day.
    stale = True
    try:
        lc = s.get("last_checked")
        if lc:
            last = datetime.strptime(lc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            stale = (datetime.now(timezone.utc) - last).total_seconds() > 12 * 3600
    except Exception:
        stale = True

    changed = available != prev
    if not (changed or stale):
        print("no change")
        return

    s["available"] = available
    s["model_id"] = model_id
    s["last_checked"] = now_iso()
    s.setdefault("since", DEFAULT_SINCE)
    json.dump(s, open(STATUS, "w"), indent=2)

    if changed and available:
        notify(model_id)
    print("updated:", "ONLINE" if available else "offline", f"(changed={changed})")


if __name__ == "__main__":
    main()
