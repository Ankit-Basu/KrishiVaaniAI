"""Backend tests. External services (Gemini, OpenWeatherMap, AGMARKNET) are mocked,
so these run offline and need no API keys. Run with:  python -m pytest -q"""
import io
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as server  # noqa: E402


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')


WEATHER_JSON = {
    'name': 'Pune',
    'weather': [{'description': 'light rain', 'icon': '10d'}],
    'main': {'temp': 24.3, 'feels_like': 25.0, 'humidity': 88},
    'wind': {'speed': 3.0},
}
MANDI_JSON = {'records': [{
    'state': 'Delhi', 'district': 'Delhi', 'market': 'Azadpur', 'commodity': 'Tomato', 'variety': 'Hybrid',
    'arrival_date': '27/11/2026', 'min_price': '1200', 'max_price': '2000', 'modal_price': '1600', 'grade': 'FAQ',
}]}


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    for cache in (server.weather_cache, server.mandi_cache, server.translation_cache):
        cache.clear()
    server._hits.clear()
    monkeypatch.setattr(server, 'RATE_LIMIT_PER_MIN', 30)
    yield


@pytest.fixture
def client():
    server.app.config['TESTING'] = True
    return server.app.test_client()


def leaf_jpeg():
    img = Image.new('RGB', (300, 300), (60, 140, 60))
    for x in range(100, 200):
        for y in range(120, 180):
            img.putpixel((x, y), (120, 90, 40))
    buf = io.BytesIO()
    img.save(buf, 'JPEG')
    buf.seek(0)
    return buf


# ---------------------------------------------------------------- site + security
def test_healthz_reports_model_and_key_booleans(client):
    data = client.get('/healthz').get_json()
    assert data['ok'] is True
    assert data['model']['classes'] == 15
    assert set(data['configured']) == {'gemini', 'openweather', 'mandi'}
    assert all(isinstance(v, bool) for v in data['configured'].values())


def test_index_and_assets_served(client):
    res = client.get('/')
    assert res.status_code == 200 and b'KrishiVaani' in res.data
    assert res.headers['X-Content-Type-Options'] == 'nosniff'
    assert client.get('/main.js').status_code == 200
    manifest = client.get('/manifest.webmanifest')
    assert manifest.status_code == 200 and 'manifest+json' in manifest.content_type


@pytest.mark.parametrize('path', ['/.env', '/app.py', '/requirements.txt', '/model/index_to_name.json'])
def test_private_files_are_never_served(client, path):
    res = client.get(path)
    # Unknown paths fall back to the SPA page, never the file itself
    assert b'<!DOCTYPE html>' in res.data
    assert b'GEMINI_API_KEY' not in res.data and b'import torch' not in res.data


def test_path_traversal_blocked(client):
    res = client.get('/..%2fapp.py')
    assert b'import torch' not in res.data


def test_unknown_api_route_is_json_404(client):
    res = client.get('/api/nope')
    assert res.status_code == 404 and res.get_json() == {'error': 'not found'}


# ---------------------------------------------------------------- analyze
def test_analyze_requires_image(client):
    assert client.post('/api/analyze').status_code == 400


def test_analyze_rejects_non_image(client):
    res = client.post('/api/analyze', data={'image': (io.BytesIO(b'not an image'), 'x.jpg')})
    assert res.status_code == 400
    assert 'Traceback' not in res.get_json()['error']


def test_analyze_returns_top3_and_remedy(client):
    res = client.post('/api/analyze', data={'image': (leaf_jpeg(), 'leaf.jpg'), 'lang': 'en'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['class'] in server.idx_to_class.values()
    assert len(data['top']) == 3
    probs = [t['confidence'] for t in data['top']]
    assert probs == sorted(probs, reverse=True) and abs(probs[0] - data['confidence']) < 1e-9
    assert data['confident'] == (data['confidence'] >= server.LOW_CONFIDENCE)
    assert data['remedy'] == server.REMEDY_MAP[data['class']]
    assert isinstance(data['inference_ms'], int)


def test_remedy_translation_is_cached(client, monkeypatch):
    calls = []
    monkeypatch.setattr(server, 'gemini', lambda prompt, **kw: calls.append(prompt) or 'अनुवादित उपाय')
    for _ in range(2):
        data = client.post('/api/analyze', data={'image': (leaf_jpeg(), 'leaf.jpg'), 'lang': 'hi'}).get_json()
        assert data['remedy'] == 'अनुवादित उपाय' and data['lang'] == 'hi'
    assert len(calls) == 1


def test_every_class_has_a_remedy():
    assert set(server.idx_to_class.values()) == set(server.REMEDY_MAP)


# ---------------------------------------------------------------- chat
def test_chat_requires_query(client):
    assert client.post('/api/chat', json={}).status_code == 400


def test_chat_sends_history_and_sanitises_lang(client, monkeypatch):
    seen = {}
    monkeypatch.setattr(server, 'get_weather', lambda *a, **k: {'weather': 'Clear, 30°C in Pune.'})
    monkeypatch.setattr(server, 'gemini', lambda prompt, **kw: seen.setdefault('prompt', prompt) and 'Spray at dawn.')
    res = client.post('/api/chat', json={
        'query': 'And for potatoes?', 'lang': 'xx<script>',
        'history': [{'role': 'user', 'text': 'When should I spray tomatoes?'}, {'role': 'bot', 'text': 'Early morning.'}],
    })
    assert res.get_json()['reply'] == 'Spray at dawn.'
    prompt = seen['prompt']
    assert 'Farmer: When should I spray tomatoes?' in prompt and 'KrishiVaani: Early morning.' in prompt
    assert 'PreferredLanguage: en' in prompt and '<script>' not in prompt
    assert 'Clear, 30°C in Pune.' in prompt


def test_chat_failure_does_not_leak_details(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError('https://generativelanguage.googleapis.com/...?key=SECRET')
    monkeypatch.setattr(server, 'gemini', boom)
    monkeypatch.setattr(server, 'get_weather', boom)
    reply = client.post('/api/chat', json={'query': 'hello'}).get_json()['reply']
    assert 'SECRET' not in reply and 'unavailable' in reply


# ---------------------------------------------------------------- weather + mandi
def test_weather_is_parsed_and_cached(client, monkeypatch):
    calls = []
    monkeypatch.setattr(server.requests, 'get', lambda *a, **k: calls.append(k['params']) or FakeResponse(WEATHER_JSON))
    for lat in ('18.5204', '18.5211'):  # same ~1 km cell -> one upstream call
        data = client.get(f'/api/weather?lat={lat}&lon=73.8567').get_json()
    assert data['city'] == 'Pune' and data['humidity'] == 88 and data['wind_kmh'] == 10.8
    assert len(calls) == 1


def test_weather_failure_returns_friendly_message(client, monkeypatch):
    monkeypatch.setattr(server.requests, 'get', lambda *a, **k: FakeResponse({'cod': 401}, status=401))
    assert client.get('/api/weather?city=Pune').get_json() == {'weather': 'Weather unavailable right now.'}


def test_mandi_records_are_slimmed_and_cached(client, monkeypatch):
    calls = []
    monkeypatch.setattr(server.requests, 'get', lambda *a, **k: calls.append(1) or FakeResponse(MANDI_JSON))
    for _ in range(2):
        data = client.get('/api/mandi?market=delhi&commodity=tomato').get_json()
    rec = data['records'][0]
    assert set(rec) == set(server.MANDI_FIELDS) and rec['modal_price'] == '1600'
    assert 'Tomato in Azadpur' in data['prices']
    assert len(calls) == 1


def test_mandi_failure_is_not_cached(client, monkeypatch):
    monkeypatch.setattr(server.requests, 'get', lambda *a, **k: FakeResponse({}, status=500))
    assert client.get('/api/mandi').get_json()['records'] == []
    monkeypatch.setattr(server.requests, 'get', lambda *a, **k: FakeResponse(MANDI_JSON))
    assert len(client.get('/api/mandi').get_json()['records']) == 1


# ---------------------------------------------------------------- tts + rate limit
def test_tts_requires_text(client):
    assert client.post('/api/tts', json={}).status_code == 400


def test_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setattr(server, 'RATE_LIMIT_PER_MIN', 2)
    monkeypatch.setattr(server, 'gemini', lambda *a, **k: 'ok')
    monkeypatch.setattr(server, 'get_weather', lambda *a, **k: {'weather': 'x'})
    codes = [client.post('/api/chat', json={'query': 'hi'}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
    # a different client IP has its own budget
    res = client.post('/api/chat', json={'query': 'hi'}, headers={'X-Forwarded-For': '10.0.0.9'})
    assert res.status_code == 200
