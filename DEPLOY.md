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
   `Dockerfile`, `app.py`, `index.html`, `main.js`, `index_to_name.json`,
   `mobilenetv2_leaf_disease_final.pth`, `requirements-deploy.txt`, and the whole `static/` folder.
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

- **Netlify**: in `netlify.toml`, replace `https://YOUR-BACKEND-URL` with your Space URL, then
  *Add new site → Import from GitHub*, publish directory `.`, no build command.
- **Vercel**: in `vercel.json`, replace `https://YOUR-BACKEND-URL` with your Space URL, then
  *Add New → Project → import the repo*, framework preset **Other**, no build command.

Both forward `/api/*` to the Space, so nothing else changes.

## 3. Alternative: Render (free, but tight)

`render.yaml` is ready: *New → Blueprint →* pick the repo, then fill in the three keys.
The free plan has 512 MB RAM and sleeps after 15 min idle; PyTorch may hit the memory limit and restart.
Use this only if Hugging Face isn't an option.

## Run locally

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (source venv/bin/activate on macOS/Linux)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-deploy.txt
copy .env.example .env           # then paste your keys into .env
python app.py                    # open http://localhost:5000
```
