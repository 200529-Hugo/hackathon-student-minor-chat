const chat = document.querySelector('#chat');
const results = document.querySelector('#results');
const input = document.querySelector('#message');
const mic = document.querySelector('#mic');
const statusEl = document.querySelector('#status');
const note = document.querySelector('#speech-note');
const voiceSelect = document.querySelector('#voice');
const voiceNote = document.querySelector('#voice-note');
const testVoice = document.querySelector('#test-voice');
const sessionId = crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random();
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;
let recognition = null;
let busy = false;
let speaking = false;
let dutchVoices = [];
let selectedVoiceKey = '';
let speechRequest = 0;

function status(value) { statusEl.textContent = value; }
function bubble(who, value) {
  const box = document.createElement('div'); box.className = `bubble ${who}`;
  const label = document.createElement('div'); label.className = 'bubble-label';
  label.textContent = who === 'agent' ? 'Minorly' : 'JIJ';
  box.append(label, document.createTextNode(value)); chat.append(box);
  chat.scrollTop = chat.scrollHeight;
}
function voiceKey(voice) { return `${voice.voiceURI}|${voice.name}|${voice.lang}`; }
function refreshVoices() {
  if (!synth) {
    voiceSelect.disabled = true; testVoice.disabled = true;
    voiceNote.textContent = 'Deze browser ondersteunt voorlezen niet.';
    return;
  }
  const available = synth.getVoices();
  dutchVoices = available.filter(voice => /^nl(?:[-_]|$)/i.test(voice.lang));
  const previous = selectedVoiceKey || voiceSelect.value;
  voiceSelect.replaceChildren();
  if (!dutchVoices.length) {
    const option = document.createElement('option');
    option.textContent = available.length ? 'Geen Nederlandse stem beschikbaar' : 'Stemmen laden...';
    voiceSelect.append(option); voiceSelect.disabled = true; testVoice.disabled = true;
    voiceNote.textContent = available.length ? 'Installeer een Nederlandse systeemstem en herlaad de pagina.' : '';
    return;
  }
  for (const voice of dutchVoices) {
    const option = document.createElement('option');
    option.value = voiceKey(voice); option.textContent = `${voice.name} (${voice.lang})`;
    voiceSelect.append(option);
  }
  const preferred = dutchVoices.find(v => voiceKey(v) === previous)
    || dutchVoices.find(v => v.lang.toLowerCase().replace('_', '-') === 'nl-nl')
    || dutchVoices[0];
  selectedVoiceKey = voiceKey(preferred);
  voiceSelect.value = selectedVoiceKey;
  voiceSelect.disabled = false; testVoice.disabled = false;
  voiceNote.textContent = '';
}
function stopSpeaking() {
  // Een wachtende stemselectie mag na een nieuw bericht niet alsnog starten.
  speechRequest++;
  synth?.cancel(); speaking = false; mic.disabled = !Recognition;
}
async function dutchVoice() {
  refreshVoices();
  if (!dutchVoices.length && synth) {
    // Sommige browsers leveren de stemmen pas na het voiceschanged-event.
    await new Promise(resolve => {
      const done = () => { clearTimeout(timer); synth.removeEventListener('voiceschanged', done); resolve(); };
      const timer = setTimeout(done, 1500);
      synth.addEventListener('voiceschanged', done);
    });
    refreshVoices();
  }
  return dutchVoices.find(v => voiceKey(v) === voiceSelect.value) || null;
}
async function speak(value) {
  if (!synth) { status('Klaar'); return; }
  const currentRequest = ++speechRequest;
  const voice = await dutchVoice();
  if (currentRequest !== speechRequest) return;
  if (!voice) { status('Klaar'); return; } // Geen stille terugval naar een Engelse stem.
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(value);
  utterance.voice = voice; utterance.lang = voice.lang; utterance.rate = 1;
  speaking = true; mic.disabled = true; status('Spreken...');
  utterance.onend = () => { speaking = false; mic.disabled = !Recognition; status('Klaar'); };
  utterance.onerror = () => {
    speaking = false; mic.disabled = !Recognition; status('Klaar');
    voiceNote.textContent = 'Voorlezen is niet gelukt. Kies eventueel een andere Nederlandse stem.';
  };
  synth.speak(utterance);
}
voiceSelect.addEventListener('change', () => { selectedVoiceKey = voiceSelect.value; });
testVoice.addEventListener('click', () => { stopSpeaking(); speak('Hallo, ik ben Minorly. Zo klinkt deze stem.'); });
if (synth) synth.addEventListener('voiceschanged', refreshVoices);
refreshVoices();
function render(items) {
  results.replaceChildren();
  document.querySelector('#count').textContent = `${items.length} ${items.length === 1 ? 'match' : 'matches'}`;
  if (!items.length) {
    const empty = document.createElement('div'); empty.className = 'empty';
    empty.innerHTML = '<div class="empty-icon">✳</div><h3>Nog geen matches.</h3><p>Beantwoord de vragen om passende minoren te ontdekken.</p>';
    results.append(empty); return;
  }
  for (const item of items) {
    const m = item.minor, card = document.createElement('article'); card.className = 'card';
    const top = document.createElement('div'); top.className = 'card-top';
    const names = document.createElement('div');
    const h = document.createElement('h3'); h.textContent = m.name;
    const inst = document.createElement('span'); inst.className = 'institution'; inst.textContent = m.institution || 'Instelling onbekend';
    names.append(h, inst);
    const score = document.createElement('span'); score.className = 'score'; score.textContent = `${item.score}/100 punten`;
    top.append(names, score); card.append(top);
    const reasons = document.createElement('ul'); reasons.className = 'reasons';
    for (const reason of item.reasons) { const li = document.createElement('li'); li.textContent = reason; reasons.append(li); }
    card.append(reasons);
    const details = document.createElement('div'); details.className = 'details';
    for (const detail of [m.location, m.study_mode, m.language, m.credits ? `${m.credits} EC` : null]) {
      if (detail) { const span = document.createElement('span'); span.textContent = detail; details.append(span); }
    }
    card.append(details);
    if (m.url && /^https:\/\/(www\.|acceptatie\.)?kiesopmaat\.nl\//.test(m.url)) {
      const link = document.createElement('a'); link.href = m.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.textContent = 'Bekijk op Kies op Maat ↗'; card.append(link);
    }
    results.append(card);
  }
}
async function send(value) {
  value = value.trim(); if (!value || busy) return;
  if (recognition) recognition.stop();
  stopSpeaking();
  busy = true; status('Verwerken...'); input.value = ''; bubble('user', value);
  try {
    const response = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({session_id:sessionId,message:value})});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json(); bubble('agent', data.reply); render(data.recommendations); speak(data.reply);
  } catch { bubble('agent', 'Er ging iets mis. Probeer het nog eens.'); status('Klaar'); }
  finally { busy = false; input.focus(); }
}
document.querySelector('#send').addEventListener('click', () => send(input.value));
input.addEventListener('keydown', e => { if (e.key === 'Enter') send(input.value); });
document.querySelector('#reset').addEventListener('click', async () => {
  if (recognition) recognition.stop(); stopSpeaking();
  try { await fetch('/api/reset', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({session_id:sessionId})}); }
  catch { note.textContent = 'Reset kon de server niet bereiken. Probeer opnieuw.'; return; }
  chat.replaceChildren(); render([]); bubble('agent', 'Hallo, ik ben Minorly, een AI-assistent die je helpt bij het ontdekken van een minor. Deel liever geen gevoelige persoonsgegevens. Welke opleiding volg je nu?'); status('Klaar');
});
if (Recognition) {
  // Spraakherkenning begint alleen na een klik; tekstinvoer blijft altijd werken.
  recognition = new Recognition(); recognition.lang = 'nl-NL'; recognition.continuous = false; recognition.interimResults = false;
  recognition.onresult = event => { input.value = event.results[0][0].transcript; status('Klaar'); send(input.value); };
  recognition.onend = () => { mic.classList.remove('listening'); if (!busy && !speaking) status('Klaar'); };
  recognition.onerror = () => { mic.classList.remove('listening'); status('Klaar'); note.textContent = 'Spraakherkenning is niet gelukt. Gebruik het tekstveld.'; };
  mic.addEventListener('click', () => { if (busy || speaking) return; stopSpeaking(); recognition.start(); mic.classList.add('listening'); status('Luisteren...'); });
} else { mic.disabled = true; note.textContent = 'Deze browser ondersteunt geen spraakherkenning. Typ je antwoord hieronder.'; }
bubble('agent', 'Hallo, ik ben Minorly, een AI-assistent die je helpt bij het ontdekken van een minor. Deel liever geen gevoelige persoonsgegevens. Welke opleiding volg je nu?');
