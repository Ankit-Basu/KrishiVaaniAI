<div align="center">

# 🌾 KrishiVaani AI

**A pocket agronomist for Indian farmers — in their own language.**

Photograph a sick leaf, ask a question by voice, and check today's weather and mandi prices,
in any of 13 Indian languages.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask)
![PyTorch](https://img.shields.io/badge/PyTorch-MobileNetV2-EE4C2C?logo=pytorch&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)

[Demo video](https://www.youtube.com/watch?v=Utio0C98-ZE) · [Deploy for free](DEPLOY.md) · [Report a bug](https://github.com/Ankit-Basu/KrishiVaaniAI/issues)

</div>

---

## The problem

Indian farmers lose crops to disease, guess at the weather, and sell without knowing the going rate.
Most advisory apps are English-first, heavy on data, or ignore local context.

## What KrishiVaani does

| | Feature | How |
|---|---|---|
| 🍃 | **Leaf check** — snap a leaf, get the disease and what to do | MobileNetV2 fine-tuned on PlantVillage, runs on CPU in ~300 ms |
| 💬 | **Ask anything** — by typing or speaking | Google Gemini, with your local weather and mandi prices as context |
| 🗣️ | **Hear the answer** | Browser speech, with a gTTS fallback on the server |
| 🌦️ | **Weather near you** — plus a spray/irrigation tip | OpenWeatherMap + browser geolocation |
| 💰 | **Mandi prices** — min / max / modal ₹ per quintal | AGMARKNET via data.gov.in, 50+ markets, 70+ crops |
| 🌐 | **13 languages** | English, हिन्दी, বাংলা, தமிழ், తెలుగు, मराठी, ગુજરાતી, ಕನ್ನಡ, മലയാളം, ਪੰਜਾਬੀ, اردو, ଓଡ଼ିଆ, অসমীয়া |

The UI is plain HTML/CSS/JS (no build step), mobile-first, and remembers the farmer's language.

## Demo

<p align="center">
  <a href="https://www.youtube.com/watch?v=Utio0C98-ZE" target="_blank">
    <img src="https://img.youtube.com/vi/Utio0C98-ZE/maxresdefault.jpg" alt="KrishiVaani demo video" width="720" />
  </a>
</p>

<details>
<summary>Screenshots of the first version (June 2025)</summary>

![Screenshot](https://github.com/user-attachments/assets/f9fb467b-0d06-4316-b95b-c3a94741420c)
![Screenshot](https://github.com/user-attachments/assets/e19994b2-f512-4519-bf0d-f2dbbfe40ded)
<img width="999" alt="Screenshot" src="https://github.com/user-attachments/assets/fcc7b117-5348-43db-ad3c-7687f5d86e11" />
<img width="979" alt="Screenshot" src="https://github.com/user-attachments/assets/1b16bbd9-f1b7-4ebc-8d6e-d100c13128b4" />
![Screenshot](https://github.com/user-attachments/assets/dd4c6329-7f0a-49c2-bb4a-7fe626597897)
![Screenshot](https://github.com/user-attachments/assets/6453da56-5dfa-412b-8116-23c92acbf54a)
![Screenshot](https://github.com/user-attachments/assets/b73a9d0f-c99b-4ac6-96a1-eeba7286d7aa)
![Screenshot](https://github.com/user-attachments/assets/05397c18-483b-4ebe-8a4f-c284a3904e5f)
<img width="1910" alt="Screenshot" src="https://github.com/user-attachments/assets/fe363168-d15c-4abd-ad77-47f80ed1c2e3" />
<img width="1911" alt="Screenshot" src="https://github.com/user-attachments/assets/db24e46e-b09b-4f39-b13e-cdca81db41e6" />

</details>

## How it works

```mermaid
flowchart LR
    U[Farmer's phone<br/>web/ — HTML, CSS, JS] -->|/api/*| F[Flask app.py]
    F --> M[MobileNetV2<br/>model/*.pth]
    F --> G[Google Gemini<br/>chat + translation]
    F --> W[OpenWeatherMap]
    F --> A[AGMARKNET<br/>data.gov.in]
    F --> T[gTTS]
```

One Flask process serves both the website and the API, so a single deploy is enough.

## Project structure

```
KrishiVaaniAI/
├── app.py                 # Flask server: serves web/ and the /api/* endpoints
├── model/
│   ├── mobilenetv2_leaf_disease_final.pth   # trained weights (9 MB)
│   └── index_to_name.json                   # class index → label
├── web/                   # the website (static, no build step)
│   ├── index.html
│   ├── main.js            # UI logic, i18n, voice, API calls
│   ├── css/style.css
│   └── images/
├── training/
│   ├── train_mobilenetv2_leaf_disease.ipynb
│   └── split_train_val.py # 80/20 train/val split helper
├── scripts/
│   └── smoke_test.py      # checks a running server end to end
├── requirements.txt       # includes CPU-only PyTorch
├── Dockerfile             # Hugging Face Spaces / any Docker host
├── render.yaml            # Render blueprint
├── netlify.toml           # Netlify: static site + /api proxy
├── vercel.json            # Vercel: static site + /api proxy
├── .env.example
└── DEPLOY.md              # free hosting guide
```

## Run it locally

You need Python 3.11 and three free API keys (see [DEPLOY.md](DEPLOY.md#0-get-the-free-api-keys)).

```bash
git clone https://github.com/Ankit-Basu/KrishiVaaniAI.git
cd KrishiVaaniAI
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env — then add your keys
python app.py
```

Open http://localhost:5000. To check every endpoint at once:

```bash
python scripts/smoke_test.py http://localhost:5000 path/to/leaf.jpg
```

### Environment variables

| Name | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | yes | Chat answers and translated remedies |
| `OPENWEATHER_API_KEY` | yes | Weather card and chat context |
| `MANDI_API_KEY` | yes | Mandi prices (data.gov.in) |
| `GEMINI_MODEL` | no | Defaults to `gemini-2.5-flash` |
| `PORT` | no | Defaults to `5000` |
| `FLASK_DEBUG` | no | Set to `1` for auto-reload while developing |

## API

| Method | Path | Body / query | Returns |
|---|---|---|---|
| `POST` | `/api/analyze` | form-data `image`, `lang` | `class`, `confidence`, `remedy` |
| `POST` | `/api/chat` | JSON `query`, `lang`, `lat`, `lon`, `mandi` | `reply` |
| `GET` | `/api/weather` | `lat`&`lon` or `city` | `temp`, `description`, `humidity`, `wind_kmh`, … |
| `GET` | `/api/mandi` | `market`, `commodity` | `records[]` with min/max/modal price |
| `POST` | `/api/tts` | JSON `text`, `lang` | `audio` (base64 MP3) |
| `GET` | `/healthz` | — | `{ "ok": true }` |

## Deploy for free

Short version: push this repo to a **Hugging Face Space (Docker)**, add the three keys as secrets, done.
Optionally put the front-end on **Vercel** or **Netlify** and point `/api` at the Space.
Full steps: **[DEPLOY.md](DEPLOY.md)**.

## The model

MobileNetV2 fine-tuned on a 15-class subset of the PlantVillage dataset (pepper, potato, tomato).
Training notebook: [training/train_mobilenetv2_leaf_disease.ipynb](training/train_mobilenetv2_leaf_disease.ipynb).

| | |
|---|---|
| Input | 224 × 224 RGB |
| Training | 5 epochs, batch 32, Adam (lr 1e-4) |
| Test accuracy | **99.44%** on 4,134 images |
| Macro precision / recall / F1 | 99.51% / 99.48% / 99.49% |
| Size / speed | 9.2 MB, ~300 ms per image on CPU |

<details>
<summary>Per-class results</summary>

| Class | Precision | Recall | F1 | Samples |
|---|---|---|---|---|
| Pepper — Bacterial spot | 1.0000 | 1.0000 | 1.0000 | 200 |
| Pepper — Healthy | 1.0000 | 1.0000 | 1.0000 | 296 |
| Potato — Early blight | 1.0000 | 0.9950 | 0.9975 | 200 |
| Potato — Late blight | 1.0000 | 0.9950 | 0.9975 | 200 |
| Potato — Healthy | 1.0000 | 1.0000 | 1.0000 | 31 |
| Tomato — Bacterial spot | 0.9953 | 0.9883 | 0.9918 | 426 |
| Tomato — Early blight | 0.9800 | 0.9800 | 0.9800 | 200 |
| Tomato — Late blight | 0.9845 | 0.9974 | 0.9909 | 382 |
| Tomato — Leaf Mold | 1.0000 | 0.9895 | 0.9947 | 191 |
| Tomato — Septoria leaf spot | 0.9916 | 1.0000 | 0.9958 | 355 |
| Tomato — Spider mites | 0.9853 | 0.9940 | 0.9896 | 336 |
| Tomato — Target Spot | 0.9929 | 0.9893 | 0.9911 | 281 |
| Tomato — Yellow Leaf Curl Virus | 1.0000 | 0.9938 | 0.9969 | 642 |
| Tomato — Mosaic Virus | 1.0000 | 1.0000 | 1.0000 | 75 |
| Tomato — Healthy | 0.9969 | 1.0000 | 0.9984 | 319 |

</details>

PlantVillage photos are taken on plain backgrounds, so accuracy on real field photos will be lower.
Photos of a single leaf, close up, in daylight work best.

## Roadmap

- [ ] Installable PWA with offline caching
- [ ] More crops (rice, wheat, cotton) trained on field photos
- [ ] Multi-day forecast and rainfall alerts
- [ ] WhatsApp / SMS bot for feature phones
- [ ] Community Q&A and remedy ratings

## Contributing

Pull requests are welcome. For larger changes, open an issue first to discuss what you'd like to change.
Run `python scripts/smoke_test.py` against your local server before submitting.

## Credits

- Built by **Ankan Basu** and **Ankit Basu**, Lovely Professional University
- Dataset: [PlantVillage](https://www.kaggle.com/datasets/emmarex/plantdisease)
- Data: OpenWeatherMap, AGMARKNET (data.gov.in), Google Gemini

## License

[MIT](LICENSE) © 2025 Ankan Basu, Ankit Basu
