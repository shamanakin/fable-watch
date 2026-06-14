# FABLE PUBLIC ACCESS BACK?

A cyberpunk monument + **automatic sensor** for the 5 days the public had Claude Fable 5.
A GitHub Action checks the Anthropic model registry every 15 minutes; the static page shows
`NO` until Fable reappears, then flips to `YES` and **pushes a notification to your phone** —
so you find out the instant it's back, even at 3am.

```
status.json        ← the truth (available: true/false), updated by the sensor
index.html         ← the page (reads status.json, no backend)
scripts/check.py   ← the sensor (hits /v1/models, flips status, sends the push)
.github/workflows/fable-watch.yml  ← runs the sensor every 15 min on GitHub's servers
```

Nothing here contains your API key. The key lives only as an encrypted GitHub **secret**.

---

## Deploy it — step by step (~10 min, all free)

### 1. Make the repo
1. Go to **github.com → New repository**. Name it e.g. `fable-watch`. **Public**. Create.
2. Easiest upload: on the new repo page click **“uploading an existing file”**, then drag in
   everything from this folder — `index.html`, `status.json`, `README.md`, the `scripts/` folder,
   and the `.github/` folder. (If drag-drop hides the dotfolders, use **GitHub Desktop** or
   `git` — see the bottom note.) Commit.

### 2. Add your Anthropic key as a secret (NOT in any file)
1. **Rotate first:** console.anthropic.com → API Keys → delete the key you pasted earlier →
   **Create Key** → copy the new one.
2. In the repo: **Settings → Secrets and variables → Actions → New repository secret**.
3. Name it **exactly** `ANTHROPIC_API_KEY`. Paste the new key as the value. Save.
   *(This box is encrypted and never exposed to the page or to commits.)*

### 3. Set your phone-push topic
1. Install the **ntfy** app (iOS/Android), or open https://ntfy.sh in a browser.
2. Pick a private, hard-to-guess topic name, e.g. `fable-watch-7h2x9-mh`.
3. In the app, **subscribe** to that exact topic.
4. In the repo, edit **`.github/workflows/fable-watch.yml`** → change the `NTFY_TOPIC:` line to
   your topic name. Commit.
   *(Anyone who knows the topic can send you a push, so keep it unguessable. It carries no secrets.)*

### 4. Turn on Pages (the website)
1. **Settings → Pages → Source: “Deploy from a branch” → Branch: `main` / `/ (root)` → Save.**
2. Wait ~1 min. Your site is live at `https://<your-username>.github.io/fable-watch/`.

### 5. Turn on the sensor
1. **Actions** tab → if prompted, **enable workflows**.
2. Open **fable-watch** → **Run workflow** (manual button) to test it once now.
3. Check the run log: it should say `no change` (Fable still offline) — that means the probe
   worked. From here it runs itself every 15 minutes, forever.

**That's it.** The page says `NO`. When Anthropic puts Fable back on the public API, within
15 minutes the sensor flips `status.json`, the page shows `YES` + a confetti burst, and your
phone buzzes with **“ACCESS RESTORED.”**

---

## How the sensor decides
It calls `GET https://api.anthropic.com/v1/models` (authoritative — it lists what your key can
actually use) and looks for any model id containing `fable`. Found → available. Network/API
error → treated as *no change* (never a false alarm). It only commits when the answer changes
or to refresh the timestamp ~twice a day, so the repo history stays clean.

> Honest caveat: it reflects availability **to your API key / region**. Because the pull was an
> export-control action, return could roll out unevenly — the page says "per the Anthropic
> registry," which is the thing you actually care about (can *I* use it again).

## Tuning
- **Check more/less often:** edit the `cron` in the workflow (`*/15` = every 15 min; `*/5` = every 5).
- **Change the watched account / links:** edit the `@AnthropicAI` URLs in `index.html`.
- **Change "the lights went out" date:** edit `since` in `status.json` and `DEFAULT_SINCE` in `check.py`.
- **Email instead of phone push:** swap the `notify()` call in `check.py` for an email step
  (ask me and I'll wire `dawidd6/action-send-mail`).

## If drag-drop won't upload the `.github` folder
Dotfolders can be finicky in the web uploader. Cleanest path:
```
cd fable-watch
git init && git add -A && git commit -m "fable-watch"
git branch -M main
git remote add origin https://github.com/<you>/fable-watch.git
git push -u origin main
```
