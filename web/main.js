// KrishiVaani AI — front-end logic
// Talks to the Flask API at /api/* (same origin, or proxied by Netlify/Vercel).

const $ = (id) => document.getElementById(id);
const el = {
  lang: $('langSelect'),
  imageInput: $('imageInput'),
  dropZone: $('dropZone'),
  dropEmpty: $('dropEmpty'),
  preview: $('previewImg'),
  analyzeBtn: $('analyzeBtn'),
  clearImgBtn: $('clearImgBtn'),
  verdict: $('verdict'),
  thread: $('thread'),
  suggest: $('suggest'),
  composer: $('composer'),
  textQuery: $('textQuery'),
  voiceBtn: $('voiceBtn'),
  stopBtn: $('stopBtn'),
  weather: $('weather'),
  weatherBtn: $('fetchWeatherBtn'),
  mandi: $('mandi'),
  mandiBtn: $('fetchMandiBtn'),
  market: $('marketSelect'),
  commodity: $('commoditySelect'),
};

const state = {
  lang: localStorage.getItem('kv-lang') || 'en',
  lat: null,
  lon: null,
  mandiText: '',
  recognition: null,
  previewUrl: null,
};

// ---------------- i18n ----------------
const translations = {
  as: {uploadLabel:'পাত বিলাক আপল’ড কৰক', analyzeBtn:'বিশ্লেষণ', askSpeak:'আপোনাৰ প্ৰশ্ন সোধক বা কোৱা', queryPlaceholder:'আপোনাৰ প্ৰশ্ন টাইপ কৰক...', sendBtn:'পঠিয়াওক', speakBtn:'কোৱা', stopBtn:'বন্ধ', listenBtn:'শুনক', weatherHeading:'বতাহ', useLocationBtn:'মোৰ অৱস্থান', mandiHeading:'বাজাৰৰ দাম'},
  gu: {uploadLabel:'પાંદાની ફોટો અપલોડ કરો', analyzeBtn:'વિશ્લેષણ', askSpeak:'તમારો પ્રશ્ન લખો કે બોલો', queryPlaceholder:'તમારો પ્રશ્ન લખો...', sendBtn:'મોકલવું', speakBtn:'બધારવું', stopBtn:'થંભાવો', listenBtn:'સાંભળો', weatherHeading:'હવામાન', useLocationBtn:'મારી જગ્યા', mandiHeading:'મણ્ડી ભાવ'},
  kn: {uploadLabel:'ಎಲೆ ಚಿತ್ರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ', analyzeBtn:'ವಿಶ್ಲೇಷಿಸು', askSpeak:'ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ ಅಥವಾ ಮಾತನಾಡಿ', queryPlaceholder:'ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ...', sendBtn:'ಕಳುಹಿಸಿ', speakBtn:'ಮಾತನಾಡಿ', stopBtn:'ನಿಲ್ಲಿಸಿ', listenBtn:'ಕೆಳಿ', weatherHeading:'ಹವಾಮಾನ', useLocationBtn:'ನನ್ನ ಸ್ಥಾನ', mandiHeading:'ಮಂಡಿ ಬೆಲೆ'},
  ml: {uploadLabel:'ഇല ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക', analyzeBtn:'വിശകലനം', askSpeak:'ചോദ്യമൈ പൊലി അഡോ', queryPlaceholder:'ചോദ്യം ടൈപ്പ് ചെയ്യുക...', sendBtn:'യയക്കുക', speakBtn:'പറയുക', stopBtn:'നിര്‍ത്തുക', listenBtn:'കേള്‍ക്കുക', weatherHeading:'വാതാവസം', useLocationBtn:'എന്റെ സ്ഥലം', mandiHeading:'മണ്ടി വില'},
  mr: {uploadLabel:'पानाचा फोटो अपलोड करा', analyzeBtn:'विश्लेषण', askSpeak:'तुमचा प्रश्न टाइप करा किंवा बोला', queryPlaceholder:'तुमचा प्रश्न टाइप करा...', sendBtn:'पाठवा', speakBtn:'बोला', stopBtn:'थांबा', listenBtn:'ऐका', weatherHeading:'हवामान', useLocationBtn:'माझे स्थान', mandiHeading:'मंडी दर'},
  pa: {uploadLabel:'ਪੱਤੇ ਦੀ ਫੋਟੋ ਅਪਲੋਡ ਕਰੋ', analyzeBtn:'ਵਿਸ਼ਲੇਸ਼ਣ', askSpeak:'ਆਪਣਾ ਪ੍ਰਸ਼ਨ ਲਿਖੋ ਜਾਂ ਬੋਲੋ', queryPlaceholder:'ਆਪਣਾ ਪ੍ਰਸ਼ਨ ਲਿਖੋ...', sendBtn:'ਭੇਜੋ', speakBtn:'ਬੋਲੋ', stopBtn:'ਰੋਕੋ', listenBtn:'ਸੁਣੋ', weatherHeading:'ਮੌਸਮ', useLocationBtn:'ਮੇਰਾ ਸਥਾਨ', mandiHeading:'ਮੰਡੀ ਕੀਮਤ'},
  te: {uploadLabel:'ఆకు ఫోటోను అప్‌లోడ్ చేయండి', analyzeBtn:'విశ్లేషణ', askSpeak:'మీ ప్రశ్నను టైప్ చేయండి లేదా మాట్లాడండి', queryPlaceholder:'మీ ప్రశ్నను టైప్ చేయండి...', sendBtn:'పంపండి', speakBtn:'మాట్లాడు', stopBtn:'ఆపు', listenBtn:'విను', weatherHeading:'వాతావరణం', useLocationBtn:'నా స్థానం', mandiHeading:'మండీ ధరలు'},
  ur: {uploadLabel:'پتے کی تصویر اپ لوڈ کریں', analyzeBtn:'تجزیہ', askSpeak:'اپنا سوال لکھیں یا بولیں', queryPlaceholder:'اپنا سوال لکھیں...', sendBtn:'بھیجیں', speakBtn:'بولیں', stopBtn:'روکیں', listenBtn:'سنیں', weatherHeading:'موسم', useLocationBtn:'میری جگہ', mandiHeading:'منڈی قیمتیں'},
  or: {uploadLabel:'ପତ୍ର ଫୋଟୋ ଅପଲୋଡ୍ କରନ୍ତୁ', analyzeBtn:'bisleshana', askSpeak:'ଆପଣଙ୍କ ପ୍ରଶ୍ନ ଲେଖନ୍ତୁ କିମ୍ବା କୁହନ୍ତୁ', queryPlaceholder:'ପ୍ରଶ୍ନ ଟାଇପ୍ କରନ୍ତୁ...', sendBtn:'ପଠାନ୍ତୁ', speakBtn:'କହନ୍ତୁ', stopBtn:'ଥାଆନ୍ତୁ', listenBtn:'ଶୁଣନ୍ତୁ', weatherHeading:'ପାଣିପାଗ', useLocationBtn:'ମୋ ଅବସ୍ଥାନ', mandiHeading:'ମଣ୍ଡି ଦାମ'},
  hi: {uploadLabel:'पत्ते की फोटो अपलोड करें', analyzeBtn:'विश्लेषण', askSpeak:'अपना प्रश्न लिखें या बोलें', queryPlaceholder:'अपना प्रश्न लिखें...', sendBtn:'भेजें', speakBtn:'बोलें', stopBtn:'रोकें', listenBtn:'सुनें', weatherHeading:'मौसम', useLocationBtn:'मेरा स्थान', mandiHeading:'मंडी भाव'},
  bn: {uploadLabel:'পাতার ছবি আপলোড করুন', analyzeBtn:'বিশ্লেষণ', askSpeak:'আপনার প্রশ্ন লিখুন বা বলুন', queryPlaceholder:'আপনার প্রশ্ন লিখুন...', sendBtn:'পাঠান', speakBtn:'বলুন', stopBtn:'থামুন', listenBtn:'শুনুন', weatherHeading:'আবহাওয়া', useLocationBtn:'আমার অবস্থান', mandiHeading:'মণ্ডি দাম'},
  ta: {uploadLabel:'இலை புகைப்படம் பதிவேற்று', analyzeBtn:'ஆய்வு', askSpeak:'உங்கள் கேள்வியை எழுதுக அல்லது பேசுக', queryPlaceholder:'உங்கள் கேள்வியை எழுதுக...', sendBtn:'அனுப்பு', speakBtn:'பேசு', stopBtn:'நிறுத்து', listenBtn:'கேள்', weatherHeading:'வானிலை', useLocationBtn:'இடம்', mandiHeading:'மண்டி விலை'},
  en: {
    uploadLabel: 'Check a leaf', analyzeBtn: 'Analyze', askSpeak: 'Ask KrishiVaani', queryPlaceholder: 'Type your question...',
    sendBtn: 'Send', speakBtn: 'Speak', stopBtn: 'Stop', listenBtn: 'Listen', weatherHeading: 'Weather',
    useLocationBtn: 'My location', mandiHeading: 'Mandi prices',
    navDiagnose: 'Leaf check', navAsk: 'Ask',
    heroTitle: 'Ask about your crop in the language you think in.',
    heroSub: "Photograph a sick leaf, speak your question, and check today's weather and mandi rates — all in one place.",
    uploadHint: 'One leaf, close up, in daylight works best.', dropTitle: 'Tap to take or choose a photo', dropSub: 'or drag it here',
    clearBtn: 'Clear', cropsLabel: 'Works for', verdictEmpty: 'The diagnosis and remedy will appear here.',
    askHint: 'Answers use your local weather and the mandi prices shown on this page.',
    weatherHint: 'Right now, near you', mandiHint: 'Latest AGMARKNET rates, ₹ per quintal',
    marketLabel: 'Market', cropLabel: 'Crop', footerTag: 'Empowering farmers in every language',
    footerNote: 'Advice is a guide, not a substitute for your local Krishi Vigyan Kendra.',
    remedy: 'What to do', confidence: 'confidence', healthy: 'Healthy', diseased: 'Disease found',
    analyzing: 'Looking closely at the leaf…', humidity: 'Humidity', wind: 'Wind', feels: 'Feels like',
  },
};
// Hindi extras for the new UI strings
Object.assign(translations.hi, {
  uploadLabel: 'पत्ते की जाँच', askSpeak: 'कृषिवाणी से पूछें', navDiagnose: 'पत्ते की जाँच', navAsk: 'पूछें',
  heroTitle: 'अपनी फ़सल के बारे में अपनी भाषा में पूछें।',
  heroSub: 'बीमार पत्ते की फ़ोटो लें, सवाल बोलें, और आज का मौसम व मंडी भाव — सब एक जगह देखें।',
  uploadHint: 'दिन की रोशनी में, एक पत्ता, पास से फ़ोटो लें।', dropTitle: 'फ़ोटो लेने या चुनने के लिए टैप करें', dropSub: 'या यहाँ खींचकर छोड़ें',
  clearBtn: 'हटाएँ', cropsLabel: 'इन फ़सलों के लिए', verdictEmpty: 'जाँच का नतीजा और उपाय यहाँ दिखेंगे।',
  askHint: 'जवाब आपके मौसम और इस पेज के मंडी भाव को ध्यान में रखते हैं।',
  weatherHint: 'अभी, आपके पास', mandiHint: 'AGMARKNET के ताज़ा भाव, ₹ प्रति क्विंटल',
  marketLabel: 'मंडी', cropLabel: 'फ़सल', footerTag: 'हर भाषा में किसानों का साथी',
  footerNote: 'यह सलाह मार्गदर्शन है; ज़रूरत पड़ने पर अपने कृषि विज्ञान केंद्र से संपर्क करें।',
  remedy: 'क्या करें', confidence: 'विश्वास', healthy: 'स्वस्थ', diseased: 'रोग मिला',
  analyzing: 'पत्ते को ध्यान से देखा जा रहा है…', humidity: 'नमी', wind: 'हवा', feels: 'महसूस',
});

const t = (key) => (translations[state.lang] && translations[state.lang][key]) || translations.en[key] || key;

function translateUI() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === 'ur' ? 'rtl' : 'ltr';
  document.querySelectorAll('[data-i18n]').forEach((node) => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((node) => { node.placeholder = t(node.dataset.i18nPlaceholder); });
}

// ---------------- helpers ----------------
const icon = (name) => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const skeleton = '<div class="skel"><i></i><i></i><i></i></div>';

async function api(path, options) {
  const res = await fetch(path, options);
  let data = null;
  try { data = await res.json(); } catch (_) { /* non-JSON */ }
  if (!res.ok && !(data && (data.error || data.reply))) throw new Error(`HTTP ${res.status}`);
  return data || {};
}

// Turn "Tomato__Tomato_YellowLeaf__Curl_Virus" into { crop: "Tomato", name: "Yellow Leaf Curl Virus" }
function prettyDisease(raw) {
  let s = String(raw).replace(/_+/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\s+/g, ' ').trim();
  const crops = ['Pepper bell', 'Potato', 'Tomato', 'Apple', 'Corn', 'Grape', 'Cherry'];
  let crop = crops.find((c) => s.toLowerCase().startsWith(c.toLowerCase())) || s.split(' ')[0];
  let name = s.slice(crop.length).trim();
  if (name.toLowerCase().startsWith(crop.toLowerCase())) name = name.slice(crop.length).trim();
  if (crop === 'Pepper bell') crop = 'Bell pepper';
  name = name ? name.charAt(0).toUpperCase() + name.slice(1) : s;
  return { crop, name, healthy: /healthy/i.test(s) };
}

// ---------------- speech ----------------
let voices = [];
const loadVoices = () => { if ('speechSynthesis' in window) voices = window.speechSynthesis.getVoices() || []; };
if ('speechSynthesis' in window) { loadVoices(); window.speechSynthesis.onvoiceschanged = loadVoices; }

async function speakOut(text) {
  if (!text) return;
  if ('speechSynthesis' in window) {
    loadVoices();
    const voice = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith(state.lang));
    if (voice) {
      const u = new SpeechSynthesisUtterance(text);
      u.voice = voice; u.lang = voice.lang;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
      return;
    }
  }
  try {
    const data = await api('/api/tts', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang: state.lang }),
    });
    if (data.audio) new Audio('data:audio/mp3;base64,' + data.audio).play();
  } catch (e) { console.error('TTS error', e); }
}

function stopVoice() {
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  if (state.recognition) { try { state.recognition.abort(); } catch (_) {} }
  setRecording(false);
}

function setRecording(on) {
  el.voiceBtn.classList.toggle('btn--rec', on);
  el.voiceBtn.classList.toggle('btn--ghost', !on);
  el.voiceBtn.innerHTML = on ? '<span class="pulse"></span>' : icon('mic');
}

function startVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { addMessage('bot', 'Voice input is not supported in this browser. Try Chrome on Android or desktop.'); return; }
  if (state.recognition && el.voiceBtn.classList.contains('btn--rec')) { stopVoice(); return; }
  const rec = new SR();
  rec.lang = state.lang === 'en' ? 'en-IN' : `${state.lang}-IN`;
  rec.interimResults = true;
  rec.onresult = (e) => {
    const text = Array.from(e.results).map((r) => r[0].transcript).join('');
    el.textQuery.value = text;
    if (e.results[e.results.length - 1].isFinal) { setRecording(false); sendQuery(); }
  };
  rec.onerror = () => setRecording(false);
  rec.onend = () => setRecording(false);
  state.recognition = rec;
  setRecording(true);
  rec.start();
}

// ---------------- leaf check ----------------
function setImage(file) {
  if (!file || !file.type.startsWith('image/')) return;
  if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
  state.previewUrl = URL.createObjectURL(file);
  el.preview.src = state.previewUrl;
  el.preview.hidden = false;
  el.dropEmpty.hidden = true;
  el.dropZone.classList.add('has-image');
  el.analyzeBtn.disabled = false;
  el.clearImgBtn.hidden = false;
  state.file = file;
}

function clearImage() {
  if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
  state.previewUrl = null; state.file = null;
  el.imageInput.value = '';
  el.preview.hidden = true; el.preview.removeAttribute('src');
  el.dropEmpty.hidden = false;
  el.dropZone.classList.remove('has-image');
  el.analyzeBtn.disabled = true;
  el.clearImgBtn.hidden = true;
  el.verdict.innerHTML = `<p class="verdict__empty">${esc(t('verdictEmpty'))}</p>`;
}

async function analyze() {
  if (!state.file) return;
  const fd = new FormData();
  fd.append('image', state.file);
  fd.append('lang', state.lang);
  el.analyzeBtn.disabled = true;
  el.verdict.innerHTML = `<p class="verdict__empty">${esc(t('analyzing'))}</p>${skeleton}`;
  try {
    const data = await api('/api/analyze', { method: 'POST', body: fd });
    if (!data.class) throw new Error(data.error || 'No result');
    const d = prettyDisease(data.class);
    const pct = Math.round((data.confidence || 0) * 100);
    el.verdict.innerHTML = `
      <div class="verdict__top">
        <span class="verdict__crop">${esc(d.crop)}</span>
        <span class="badge ${d.healthy ? 'badge--ok' : ''}">${esc(d.healthy ? t('healthy') : t('diseased'))}</span>
      </div>
      <div class="verdict__name">${esc(d.healthy ? t('healthy') : d.name)}</div>
      <div class="meter ${pct < 60 ? 'meter--low' : ''}"><span style="width:0"></span></div>
      <div class="meter__label">${pct}% ${esc(t('confidence'))}</div>
      <div class="verdict__remedy"><h3>${esc(t('remedy'))}</h3><p id="remedyText">${esc(data.remedy)}</p></div>
      <div class="verdict__foot"><button class="btn btn--ghost btn--sm" id="listenRemedy">${icon('speaker')}<span>${esc(t('listenBtn'))}</span></button></div>`;
    requestAnimationFrame(() => { el.verdict.querySelector('.meter > span').style.width = pct + '%'; });
    $('listenRemedy').addEventListener('click', () => speakOut(`${d.healthy ? t('healthy') : d.name}. ${data.remedy}`));
  } catch (e) {
    el.verdict.innerHTML = `<p class="note note--err">Could not analyze the photo: ${esc(e.message)}</p>`;
  } finally {
    el.analyzeBtn.disabled = !state.file;
  }
}

// ---------------- chat ----------------
function addMessage(who, text) {
  if (el.suggest) { el.suggest.remove(); el.suggest = null; }
  const wrap = document.createElement('div');
  wrap.className = `msg msg--${who}`;
  wrap.innerHTML = `<div class="msg__bubble"></div>`;
  const bubble = wrap.firstElementChild;
  if (text === null) bubble.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
  else bubble.textContent = text;
  el.thread.appendChild(wrap);
  el.thread.scrollTop = el.thread.scrollHeight;
  return wrap;
}

function finishBotMessage(wrap, text) {
  wrap.firstElementChild.textContent = text;
  const meta = document.createElement('div');
  meta.className = 'msg__meta';
  meta.innerHTML = `<span>KrishiVaani</span><button type="button">${icon('speaker')}${esc(t('listenBtn'))}</button>`;
  meta.querySelector('button').addEventListener('click', () => speakOut(text));
  wrap.appendChild(meta);
  el.thread.scrollTop = el.thread.scrollHeight;
}

async function sendQuery(evt) {
  if (evt) evt.preventDefault();
  const query = el.textQuery.value.trim();
  if (!query) return;
  el.textQuery.value = '';
  addMessage('user', query);
  const pending = addMessage('bot', null);
  try {
    const data = await api('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, lang: state.lang, lat: state.lat, lon: state.lon, mandi: state.mandiText }),
    });
    finishBotMessage(pending, (data.reply || 'No reply.').trim());
  } catch (e) {
    finishBotMessage(pending, 'Sorry, I could not reach the server. Please try again.');
  }
}

// ---------------- weather ----------------
function farmTip(w) {
  const desc = (w.description || '').toLowerCase();
  if (/rain|drizzle|thunder/.test(desc)) return 'Rain expected — hold off on spraying and fertiliser top-dressing.';
  if (w.wind_kmh != null && w.wind_kmh > 15) return 'Windy — spray drift is likely; spray early morning instead.';
  if (w.temp != null && w.temp >= 35) return 'Hot day — irrigate in the evening to cut evaporation.';
  if (w.humidity != null && w.humidity >= 85) return 'Very humid — watch for fungal spots on leaves.';
  return 'Calm conditions — a good window for spraying or field work.';
}

function renderWeather(w) {
  state.lastWeather = w;
  if (w.temp == null) {
    el.weather.innerHTML = `<p class="note">${esc(w.weather || 'No weather data.')}</p>`;
    return;
  }
  el.weather.innerHTML = `
    <div class="wx">
      <div class="wx__temp">${Math.round(w.temp)}<sup>°C</sup></div>
      <div>
        <div class="wx__desc">${esc(w.description)}</div>
        <div class="wx__city">${icon('pin')}${esc(w.city)}</div>
      </div>
      <dl class="wx__stats">
        <div class="stat"><dt>${esc(t('feels'))}</dt><dd>${w.feels_like != null ? Math.round(w.feels_like) + '°' : '—'}</dd></div>
        <div class="stat"><dt>${esc(t('humidity'))}</dt><dd>${w.humidity != null ? w.humidity + '%' : '—'}</dd></div>
        <div class="stat"><dt>${esc(t('wind'))}</dt><dd>${w.wind_kmh != null ? Math.round(w.wind_kmh) + ' km/h' : '—'}</dd></div>
      </dl>
      <p class="wx__tip">${esc(farmTip(w))}</p>
    </div>`;
}

async function fetchWeather() {
  el.weather.innerHTML = skeleton;
  const qs = state.lat != null ? `?lat=${state.lat}&lon=${state.lon}` : '';
  try { renderWeather(await api('/api/weather' + qs)); }
  catch (e) { el.weather.innerHTML = '<p class="note note--err">Could not load weather.</p>'; }
}

function locateAndFetchWeather() {
  if (!('geolocation' in navigator)) { fetchWeather(); return; }
  navigator.geolocation.getCurrentPosition(
    (pos) => { state.lat = pos.coords.latitude; state.lon = pos.coords.longitude; fetchWeather(); },
    () => fetchWeather(),
    { timeout: 8000, maximumAge: 600000 },
  );
}

// ---------------- mandi ----------------
const fmtINR = (v) => { const n = Number(v); return Number.isFinite(n) ? '₹' + n.toLocaleString('en-IN') : esc(v); };

async function fetchMandi() {
  el.mandi.innerHTML = skeleton;
  const params = new URLSearchParams({ market: el.market.value, commodity: el.commodity.value });
  try {
    const data = await api('/api/mandi?' + params);
    state.mandiText = data.prices || '';
    const rows = Array.isArray(data.records) ? data.records : [];
    if (!rows.length) {
      el.mandi.innerHTML = `<p class="note">${esc(data.prices || 'No mandi price data found.')}<br>Try another market or crop.</p>`;
      return;
    }
    el.mandi.innerHTML = `
      <table class="prices">
        <thead><tr><th>Variety</th><th class="num">Min</th><th class="num">Max</th><th class="num">Modal</th></tr></thead>
        <tbody>${rows.map((r) => `
          <tr>
            <td>${esc(r.variety || r.commodity)}<small>${esc(r.market)} · ${esc(r.arrival_date)}</small></td>
            <td class="num">${fmtINR(r.min_price)}</td>
            <td class="num">${fmtINR(r.max_price)}</td>
            <td class="num modal">${fmtINR(r.modal_price)}</td>
          </tr>`).join('')}
        </tbody>
      </table>`;
  } catch (e) {
    el.mandi.innerHTML = '<p class="note note--err">Could not load mandi prices.</p>';
  }
}

// ---------------- wire up ----------------
el.imageInput.addEventListener('change', () => setImage(el.imageInput.files[0]));
['dragenter', 'dragover'].forEach((ev) => el.dropZone.addEventListener(ev, (e) => { e.preventDefault(); el.dropZone.classList.add('is-over'); }));
['dragleave', 'drop'].forEach((ev) => el.dropZone.addEventListener(ev, () => el.dropZone.classList.remove('is-over')));
el.dropZone.addEventListener('drop', (e) => { e.preventDefault(); setImage(e.dataTransfer.files[0]); });
el.analyzeBtn.addEventListener('click', analyze);
el.clearImgBtn.addEventListener('click', clearImage);

el.composer.addEventListener('submit', sendQuery);
el.voiceBtn.addEventListener('click', startVoice);
el.stopBtn.addEventListener('click', stopVoice);
if (el.suggest) el.suggest.addEventListener('click', (e) => {
  const b = e.target.closest('button[data-q]');
  if (b) { el.textQuery.value = b.dataset.q; sendQuery(); }
});

el.weatherBtn.addEventListener('click', locateAndFetchWeather);
el.mandiBtn.addEventListener('click', fetchMandi);
el.market.addEventListener('change', fetchMandi);
el.commodity.addEventListener('change', fetchMandi);

el.lang.value = state.lang;
el.lang.addEventListener('change', () => {
  state.lang = el.lang.value;
  localStorage.setItem('kv-lang', state.lang);
  translateUI();
  if (state.lastWeather) renderWeather(state.lastWeather);
});

translateUI();
locateAndFetchWeather();
fetchMandi();
