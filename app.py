import os
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import io
import json
from flask import Flask, request, jsonify, send_file, send_from_directory, url_for, redirect
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
import requests
from gtts import gTTS
import base64

# Load config.env
from dotenv import load_dotenv
load_dotenv('.env')
load_dotenv('config.env')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')


def gemini_url():
    return f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


# Load class to index mapping
with open(os.path.join(BASE_DIR, 'index_to_name.json'), 'r') as f:
    class_to_name = json.load(f)
    idx_to_class = {int(k): v for k, v in class_to_name.items()}

# Initialize the model
def load_model(model_path):
    # Create model
    model = models.mobilenet_v2(num_classes=len(idx_to_class))
    
    # Load the trained weights
    checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
    
    # Handle DataParallel or other wrappers
    if isinstance(checkpoint, torch.nn.DataParallel):
        checkpoint = checkpoint.module
    
    # Load state dict
    model.load_state_dict(checkpoint)
    model.eval()
    return model

# Load the model
model = load_model(os.path.join(BASE_DIR, 'mobilenetv2_leaf_disease_final.pth'))

# Image transformations
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_image(image_bytes):
    # Open and preprocess the image
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)  # Create a mini-batch
    
    # Make prediction
    with torch.no_grad():
        output = model(input_batch)
    
    # Get the predicted class
    _, predicted_idx = torch.max(output, 1)
    predicted_class = idx_to_class[predicted_idx.item()]
    
    return predicted_class, output

# Simple remedy mapping (you can expand this with more detailed remedies)
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

def get_remedy(disease_name):
    return REMEDY_MAP.get(disease_name)


def translate_text(text, target_lang):
    """Translate given text to target_lang using Gemini if not English."""
    if target_lang == 'en' or not text:
        return text
    prompt = f"Translate the following agricultural advice into {target_lang}. Keep scientific names or pesticide ingredient names untranslated.\n\n{text}"
    try:
        url = gemini_url()
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return text


def generate_remedy_gemini(disease_name, lang='en'):
    """Query Gemini API for a concise remedy if not in static map."""
    prompt = f"""
    You are an expert plant pathologist. In one or two sentences, provide a practical field-level remedy for the following crop disease so that it is understandable by Indian farmers.
    Return plain text with no bullet points or asterisks.
    Language: {lang}
    Disease: {disease_name}
    """
    try:
        url = gemini_url()
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 200}
        }
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text
    except Exception:
        return "Consult a local agricultural expert for specific treatment options."

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'), static_url_path='/static')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
MANDI_API_KEY = os.getenv('MANDI_API_KEY')


# Serve index.html for root and /index.html
@app.route('/')
@app.route('/index.html')
def serve_index():
    return send_file(os.path.join(BASE_DIR, 'index.html'))


# Serve main.js from root
@app.route('/main.js')
def serve_js():
    return send_file(os.path.join(BASE_DIR, 'main.js'))


# Old /images/ links -> static/images/
@app.route('/images/<path:filename>')
def serve_legacy_images(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'images'), filename)


@app.route('/healthz')
def healthz():
    return jsonify({'ok': True})


# Any other non-API path gets the single-page app.
# Never serve arbitrary files from the project root: that would expose .env and source code.
@app.route('/<path:path>')
def serve_file(path):
    if path.startswith('api/'):
        return "Not found", 404
    return send_file(os.path.join(BASE_DIR, 'index.html'))


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Handle image upload, run inference locally and return prediction & remedy."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    lang = request.form.get('lang', 'en')
    image_file = request.files['image']
    try:
        # Read bytes and run model
        image_bytes = image_file.read()
        predicted_class, logits = predict_image(image_bytes)

        # Confidence
        probabilities = torch.nn.functional.softmax(logits[0], dim=0)
        confidence = float(probabilities.max().item())

        # Remedy text
        remedy = get_remedy(predicted_class)
        if remedy is None:
            remedy = generate_remedy_gemini(predicted_class, lang)
        else:
            remedy = translate_text(remedy, lang)

        return jsonify({
            'class': predicted_class,
            'confidence': confidence,
            'remedy': remedy,
            'lang': lang
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather', methods=['GET'])
def weather():
    """Return a simple description string for current weather.
    Supports either lat/lon or city name. If both are missing it defaults to Delhi."""
    city = request.args.get('city')
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    try:
        if city:
            params = {'q': city, 'appid': OPENWEATHER_API_KEY, 'units': 'metric'}
        elif lat and lon:
            params = {'lat': lat, 'lon': lon, 'appid': OPENWEATHER_API_KEY, 'units': 'metric'}
        else:
            params = {'q': 'Delhi', 'appid': OPENWEATHER_API_KEY, 'units': 'metric'}

        resp = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params, timeout=10)
        data = resp.json()
        city_name = data.get('name') or city or 'your area'
        weather_desc = data['weather'][0]['description']
        temp_c = data['main']['temp']
        weather_str = f"{weather_desc.capitalize()}, {temp_c}°C in {city_name}."
        wind_ms = (data.get('wind') or {}).get('speed')

        return jsonify({
            'weather': weather_str,
            'city': city_name,
            'description': weather_desc,
            'temp': temp_c,
            'feels_like': data['main'].get('feels_like'),
            'humidity': data['main'].get('humidity'),
            'wind_kmh': round(wind_ms * 3.6, 1) if wind_ms is not None else None,
            'icon': data['weather'][0].get('icon'),
        })
    except Exception as e:
        return jsonify({'weather': f'Error: {str(e)}'})

@app.route('/api/mandi', methods=['GET'])
def mandi():
    # Uses data.gov.in AGMARKNET endpoint
    market = request.args.get('market', 'DELHI').upper()
    commodity = request.args.get('commodity', 'Wheat').capitalize()
    try:
        url = (
            'https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070'
            f'?api-key={MANDI_API_KEY}&format=json&filters[market]={market}&filters[commodity]={commodity}&limit=5'
        )
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            records = data.get('records', [])
            if not records:
                return jsonify({'prices': 'No mandi price data found.'})
            # Format price info
            prices = [
                f"{rec['commodity']} in {rec['market']} ({rec['state']}): {rec['modal_price']} ₹/quintal on {rec['arrival_date']}"
                for rec in records
            ]
            keep = ('commodity', 'variety', 'market', 'district', 'state', 'arrival_date', 'min_price', 'max_price', 'modal_price')
            slim = [{k: rec.get(k) for k in keep} for rec in records]
            return jsonify({'prices': '\n'.join(prices), 'records': slim})
        else:
            return jsonify({'prices': 'No data'})
    except Exception as e:
        return jsonify({'prices': f'Error: {str(e)}'})

@app.route('/api/tts', methods=['POST'])
def tts():
    """Return base64 MP3 audio synthesized via gTTS for the given text & lang."""
    data = request.get_json()
    text = data.get('text', '')
    lang = data.get('lang', 'en')
    if not text:
        return jsonify({'error': 'No text'}), 400
    try:
        tts_obj = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts_obj.write_to_fp(fp)
        audio_b64 = base64.b64encode(fp.getvalue()).decode('utf-8')
        return jsonify({'audio': audio_b64})
    except ValueError:
        # gTTS doesn't support the requested language
        return jsonify({'error': 'unsupported_lang'}), 400


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')
    lang = data.get('lang', 'en')
    lat = data.get('lat')
    lon = data.get('lon')
    mandi_info = data.get('mandi', '')
    # Fetch current weather for context (use user location if available)
    weather_context = ''
    try:
        if lat and lon:
            weather_params = {'lat': lat, 'lon': lon, 'appid': OPENWEATHER_API_KEY, 'units': 'metric'}
            weather_resp = requests.get('https://api.openweathermap.org/data/2.5/weather', params=weather_params, timeout=10)
            weather_json = weather_resp.json()
            city = weather_json.get('name', 'your area')
            weather_desc = weather_json['weather'][0]['description']
            weather_temp = weather_json['main']['temp']
            weather_context = f"Current weather in {city}: {weather_desc}, {weather_temp}°C."
        else:
            weather_params = {'q': 'Delhi', 'appid': OPENWEATHER_API_KEY, 'units': 'metric'}
            weather_resp = requests.get('https://api.openweathermap.org/data/2.5/weather', params=weather_params, timeout=10)
            weather_json = weather_resp.json()
            weather_desc = weather_json['weather'][0]['description']
            weather_temp = weather_json['main']['temp']
            weather_context = f"Current weather in Delhi: {weather_desc}, {weather_temp}°C."
    except Exception:
        weather_context = "Weather data unavailable."
    # Compose prompt for Gemini
    prompt = f"""
You are KrishiVaani AI, an Indian agriculture assistant.
• ONLY introduce yourself when the farmer greets you (e.g., "hi", "hello") or explicitly asks who you are.
• For all other queries, answer directly without any self-introduction.
• You may answer questions about crops, crop diseases, pests, weather conditions, mandi/market prices and selling decisions, storage or general agriculture.
Weather: {weather_context}
MandiPrices: {mandi_info}
PreferredLanguage: {lang}

---
### FarmerQuestion
{query}

### Guidelines for YourResponse
• Reply in plain text with no Markdown or bullet asterisks (*).
• Keep it concise and actionable.

### YourResponse
"""
    try:
        url = gemini_url()
        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if resp.status_code == 200:
            reply = resp.json()['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'reply': reply})
        else:
            return jsonify({'reply': 'No reply.'})
    except Exception as e:
        return jsonify({'reply': f'Error: {str(e)}'})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
