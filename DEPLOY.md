# Hosting KrishiVaani AI for free

The app is a single Flask server that serves both the website and the `/api/*` endpoints, and it runs a
PyTorch model. PyTorch needs about 600–800 MB of RAM, so most "free web service" tiers (Render free = 512 MB)
are too small. **Hugging Face Spaces** gives you a free 2 vCPU / 16 GB RAM container, so that's the recommended host.

## 0. Get the free API keys

| Key | Where | Used for |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey | Chat answers and translated remedies |
| `OPENWEATHER_API_KEY` | https://home.openweathermap.org/api_keys (free "Current weather" plan) | Weather card |
| `MANDI_API_KEY` | https://data.gov.in → sign up → *My Account* → API key | Mandi prices (AGMARKNET) |

Optional: `GEMINI_MODEL` (default `gemini-2.5-flash`) if Google renames/retires the model.

## 1. Recommended: Hugging Face Spaces (Docker) — free, always the full app

1. Create an account at https://huggingface.co and click **New → Space**.
2. Name it (e.g. `krishivaani`), choose **SDK: Docker → Blank**, hardware **CPU basic (free)**, visibility **Public**.
3. In the new Space, open **Settings → Variables and secrets** and add three **Secrets**:
   `GEMINI_API_KEY`, `OPENWEATHER_API_KEY`, `MANDI_API_KEY`.
4. Upload the code. Easiest is the web UI: **Files → Add file → Upload files**, and drag in:
   `Dockerfile`, `app.py`, `requirements.txt`, and the whole `model/` and `web/` folders.
   Do **not** upload the project `README.md` — the Space's own README holds its config.
5. Open the Space's `README.md` and make sure its header contains:

   ```yaml
   ---
   title: KrishiVaani AI
   sdk: docker
   app_port: 7860
   ---
   ```

6. The Space builds automatically (≈5 min). Your app is live at `https://<user>-krishivaani.hf.space`.
7. Open `https://<user>-krishivaani.hf.space/healthz`. All three `configured` values should be `true`;
   a `false` means that secret is missing or misspelled. (Restart the Space after changing secrets.)

Share the direct `*.hf.space` link, not the `huggingface.co/spaces/...` page: that page shows the app inside an
iframe, where browsers may block the microphone, location and "Install app".

Prefer git? Clone the Space, copy the same files in, then (binary files must go through LFS on HF):

```bash
git lfs install
git lfs track "*.pth" "*.jpg" "*.png" "*.webp"
git add .gitattributes . && git commit -m "Deploy KrishiVaani" && git push
```

Notes: free Spaces sleep after ~48 h without visitors and wake on the next visit (first load ~30 s).
Geolocation and the microphone need HTTPS — `*.hf.space` is HTTPS, so both work.

## 2. Optional: nicer URL for the front-end (Netlify or Vercel, free)

Keep the Space as the backend, and host only the static page elsewhere:

- **Vercel**: in `vercel.json`, replace `https://YOUR-BACKEND-URL` with your Space URL and push, then
  *Add New → Project → import the repo*, framework preset **Other**, leave build settings empty
  (`vercel.json` already sets the output folder to `web/`, and `.vercelignore` keeps the Python files out).
- **Netlify**: in `netlify.toml`, replace `https://YOUR-BACKEND-URL` with your Space URL and push, then
  *Add new site → Import from GitHub*. `netlify.toml` already publishes `web/`.

Both forward `/api/*` to the Space, so nothing else changes.

## 3. Alternative: Render (free, but tight)

`render.yaml` is ready: *New → Blueprint →* pick the repo, then fill in the three keys.
The free plan has 512 MB RAM and sleeps after 15 min idle; PyTorch may hit the memory limit and restart.
Use this only if Hugging Face isn't an option.

## Run locally

See [README.md](README.md#run-it-locally).

## Check a deployment

```bash
python scripts/smoke_test.py https://<user>-krishivaani.hf.space path/to/leaf.jpg
```

## Before a demo

- Open the site a few minutes early: a sleeping free Space takes ~30 s to wake up.
- Keep 2–3 real tomato / potato / pepper leaf photos on your phone. PlantVillage-style photos (one leaf,
  plain background) give the most confident results; anything else shows the "Not sure" warning, by design.
- Try one question in Hindi (or another language) and tap **Listen** to show voice output.
- On Android Chrome, use **Install app** to show it running as an installed app.
- `RATE_LIMIT_PER_MIN` (default 30 per IP per endpoint) protects your free Gemini quota if the link is shared.
