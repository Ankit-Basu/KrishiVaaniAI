"""KrishiVaani AI — Flask backend.

Serves the static site in web/ and these JSON endpoints:
  POST /api/analyze  leaf photo -> disease class, confidence, remedy
  POST /api/chat     farmer question -> Gemini answer (uses weather + mandi context)
  GET  /api/weather  current weather by lat/lon or city
  GET  /api/mandi    AGMARKNET prices for a market + commodity
  POST /api/tts      text -> base64 MP3 (gTTS), used when the browser has no voice
"""
import base64
import io
import json
import os

import requests
import torch
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from gtts import gTTS
from PIL import Image
from torchvision import models, transforms

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, 'web')
MODEL_DIR = os.path.join(BASE_DIR, 'model')

load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
MANDI_API_KEY = os.getenv('MANDI_API_KEY')

OPENWEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
MANDI_URL = 'https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070'


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
with open(os.path.join(MODEL_DIR, 'index_to_name.json'), 'r') as f:
    idx_to_class = {int(k): v for k, v in json.load(f).items()}


def load_model(model_path):
    net = models.mobilenet_v2(num_classes=len(idx_to_class))
    state = torch.load(model_path, map_location='cpu')
    if isinstance(state, torch.nn.DataParallel):
        state = state.module
    net.load_state_dict(state)
    net.eval()
    return net


model = load_model(os.path.join(MODEL_DIR, 'mobilenetv2_leaf_disease_final.pth'))

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def predict_image(image_bytes):
    """Return (class_name, confidence 0..1) for a leaf photo."""
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    with torch.no_grad():
        logits = model(preprocess(image).unsqueeze(0))
    probs = torch.nn.functional.softmax(logits[0], dim=0)
    conf, idx = probs.max(0)
    return idx_to_class[idx.item()], float(conf.item())


# Field-level remedies for the model's 15 classes (PlantVillage subset)
REMEDY_MAP = {
    'Pepper__bell___Bacterial_spot': 'Remove spotted leaves, avoid overhead watering, and spray a copper-based bactericide every 7-10 days. Use certified disease-free seed next season.',
    'Pepper__bell___healthy': 'Your pepper plant looks healthy. Keep watering at the base and check the underside of leaves weekly.',
    'Potato___Early_blight': 'Remove lower infected leaves and spray mancozeb or chlorothalonil every 7-10 days. Rotate with non-solanaceous crops next season.',
    'Potato___Late_blight': 'Act fast: remove and destroy infected plants, then spray metalaxyl + mancozeb. Avoid irrigation late in the day.',
    'Potato___healthy': 'Your potato plant looks healthy. Keep earthing up and watch for dark leaf patches after cool, wet weather.',
    'Tomato_Bacterial_spot': 'Remove infected leaves, avoid working in the field when plants are wet, and spray copper oxychloride with streptocycline.',
    'Tomato_Early_blight': 'Prune lower leaves touching the soil, mulch, and spray mancozeb or chlorothalonil every 7-10 days.',
    'Tomato_Late_blight': 'Remove infected plants immediately and spray metalaxyl + mancozeb. Improve spacing for airflow.',
    'Tomato_Leaf_Mold': 'Improve ventilation, reduce humidity, remove affected leaves, and spray a copper fungicide or chlorothalonil.',
    'Tomato_Septoria_leaf_spot': 'Remove spotted lower leaves, mulch to stop soil splash, and spray mancozeb or chlorothalonil.',
    'Tomato_Spider_mites_Two_spotted_spider_mite': 'Spray water on leaf undersides, then neem oil (3-5 ml per litre) or a miticide such as abamectin if severe.',
    'Tomato__Target_Spot': 'Remove infected leaves, improve airflow, and spray azoxystrobin or chlorothalonil.',
    'Tomato__Tomato_YellowLeaf__Curl_Virus': 'There is no cure: uproot infected plants, control whiteflies with yellow sticky traps and neem oil or imidacloprid, and use resistant varieties.',
    'Tomato__Tomato_mosaic_virus': 'Uproot infected plants, wash hands and tools with soap, avoid tobacco near plants, and use resistant seed.',
    'Tomato_healthy': 'Your tomato plant looks healthy. Stake the plant, water at the base, and inspect leaves weekly.',
}


# ---------------------------------------------------------------------------
# External services
# ---------------------------------------------------------------------------
def gemini(prompt, timeout=30, **generation_config):
    """Call Gemini and return the text reply (raises on failure)."""
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'
    payload = {'contents': [{'parts': [{'text': prompt}]}]}
    if generation_config:
        payload['generationConfig'] = generation_config
    resp = requests.post(url, params={'key': GEMINI_API_KEY}, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()


def translate_text(text, target_lang):
    """Translate advice into target_lang (ISO code); returns the original on failure."""
    if target_lang == 'en' or not text:
        return text
    try:
        return gemini(
            f'Translate the following agricultural advice into the language with ISO code "{target_lang}". '
            f'Keep scientific names and pesticide ingredient names untranslated. Reply with the translation only.\n\n{text}',
            timeout=15,
        )
    except Exception:
        return text


def generate_remedy(disease_name, lang='en'):
    try:
        return gemini(
            'You are an expert plant pathologist. In one or two sentences, give a practical field-level remedy '
            'for this crop disease that an Indian farmer can follow. Plain text, no bullet points or asterisks.\n'
            f'Language: {lang}\nDisease: {disease_name}',
            timeout=15, temperature=0.6, maxOutputTokens=200,
        )
    except Exception:
        return 'Consult your local Krishi Vigyan Kendra for specific treatment options.'


def get_weather(lat=None, lon=None, city=None):
    """Return a dict with current weather; defaults to Delhi."""
    if lat and lon:
        params = {'lat': lat, 'lon': lon}
    else:
        params = {'q': city or 'Delhi'}
    params.update(appid=OPENWEATHER_API_KEY, units='metric')
    data = requests.get(OPENWEATHER_URL, params=params, timeout=10).json()
    city_name = data.get('name') or city or 'your area'
    desc = data['weather'][0]['description']
    temp = data['main']['temp']
    wind_ms = (data.get('wind') or {}).get('speed')
    return {
        'weather': f'{desc.capitalize()}, {temp}°C in {city_name}.',
        'city': city_name,
        'description': desc,
        'temp': temp,
        'feels_like': data['main'].get('feels_like'),
        'humidity': data['main'].get('humidity'),
        'wind_kmh': round(wind_ms * 3.6, 1) if wind_ms is not None else None,
        'icon': data['weather'][0].get('icon'),
    }


# ---------------------------------------------------------------------------
# App + static site
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder=None)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB uploads
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600


@app.route('/healthz')
def healthz():
    return jsonify({'ok': True})


@app.route('/')
@app.route('/<path:path>')
def site(path='index.html'):
    """Serve files from web/; unknown paths fall back to index.html.
    send_from_directory refuses paths outside web/, so .env and source stay private."""
    if path.startswith('api/'):
        return jsonify({'error': 'not found'}), 404
    if os.path.isfile(os.path.join(WEB_DIR, path)):
        return send_from_directory(WEB_DIR, path)
    return send_from_directory(WEB_DIR, 'index.html')


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    lang = request.form.get('lang', 'en')
    try:
        predicted_class, confidence = predict_image(request.files['image'].read())
    except Exception as e:
        return jsonify({'error': f'Could not read image: {e}'}), 400

    remedy = REMEDY_MAP.get(predicted_class)
    remedy = translate_text(remedy, lang) if remedy else generate_remedy(predicted_class, lang)
    return jsonify({'class': predicted_class, 'confidence': confidence, 'remedy': remedy, 'lang': lang})


@app.route('/api/weather', methods=['GET'])
def weather():
    try:
        return jsonify(get_weather(request.args.get('lat'), request.args.get('lon'), request.args.get('city')))
    except Exception:
        app.logger.exception('weather lookup failed')
        return jsonify({'weather': 'Weather unavailable right now.'})


@app.route('/api/mandi', methods=['GET'])
def mandi():
    market = request.args.get('market', 'DELHI').upper()
    commodity = request.args.get('commodity', 'Wheat').capitalize()
    params = {
        'api-key': MANDI_API_KEY, 'format': 'json', 'limit': 5,
        'filters[market]': market, 'filters[commodity]': commodity,
    }
    try:
        resp = requests.get(MANDI_URL, params=params, timeout=15)
        if resp.status_code != 200:
            return jsonify({'prices': 'No data', 'records': []})
        records = resp.json().get('records', [])
        if not records:
            return jsonify({'prices': 'No mandi price data found.', 'records': []})
        keep = ('commodity', 'variety', 'market', 'district', 'state', 'arrival_date',
                'min_price', 'max_price', 'modal_price')
        slim = [{k: rec.get(k) for k in keep} for rec in records]
        text = '\n'.join(
            f"{r['commodity']} in {r['market']} ({r['state']}): {r['modal_price']} ₹/quintal on {r['arrival_date']}"
            for r in slim
        )
        return jsonify({'prices': text, 'records': slim})
    except Exception:
        app.logger.exception('mandi lookup failed')
        return jsonify({'prices': 'Mandi prices unavailable right now.', 'records': []})


@app.route('/api/tts', methods=['POST'])
def tts():
    data = request.get_json(silent=True) or {}
    text, lang = data.get('text', ''), data.get('lang', 'en')
    if not text:
        return jsonify({'error': 'No text'}), 400
    try:
        fp = io.BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(fp)
        return jsonify({'audio': base64.b64encode(fp.getvalue()).decode('utf-8')})
    except ValueError:
        return jsonify({'error': 'unsupported_lang'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 502


CHAT_PROMPT = """You are KrishiVaani AI, an Indian agriculture assistant.
- Only introduce yourself when the farmer greets you or asks who you are; otherwise answer directly.
- You may answer questions about crops, diseases, pests, weather, mandi prices and selling decisions, storage, or general agriculture.

Weather: {weather}
MandiPrices: {mandi}
PreferredLanguage: {lang}

### FarmerQuestion
{query}

### Guidelines
- Reply in the preferred language, in plain text with no Markdown or asterisks.
- Keep it concise and actionable.

### YourResponse
"""


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'reply': 'Please type a question.'}), 400
    try:
        weather_context = 'Current weather: ' + get_weather(data.get('lat'), data.get('lon'))['weather']
    except Exception:
        weather_context = 'Weather data unavailable.'
    prompt = CHAT_PROMPT.format(weather=weather_context, mandi=data.get('mandi', ''),
                                lang=data.get('lang', 'en'), query=query)
    try:
        return jsonify({'reply': gemini(prompt)})
    except Exception:
        # Don't echo the exception: request errors include the URL with the API key.
        app.logger.exception('gemini chat failed')
        return jsonify({'reply': 'Sorry, the assistant is unavailable right now. Please try again.'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG') == '1')
