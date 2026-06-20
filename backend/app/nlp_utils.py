"""
nlp_utils.py
Logic murni (tanpa I/O / tanpa model) — diporting 1:1 dari notebook:
  - Cell 7  -> SYMPTOMS_28
  - Cell 20 -> SYMPTOM_SYNONYMS, extract_symptoms()
  - Cell 22 -> INDO_KEYWORDS, DISEASE_NAME_HINTS, SYMPTOM_ID, detect_lang_smart()
Tidak ada perubahan logic dari notebook, hanya dirapikan jadi module .py
supaya bisa di-import backend tanpa harus jalankan notebook.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("medical_chatbot.nlp_utils")

# ─────────────────────────────────────────────────────────────────────────
# Cell 7 — daftar 28 gejala yang dikenali model
# ─────────────────────────────────────────────────────────────────────────
SYMPTOMS_28 = [
    'chest pain', 'dizziness', 'sore throat', 'sneezing', 'weight loss', 'blurred vision',
    'nausea', 'vomiting', 'sweating', 'insomnia', 'diarrhea', 'depression', 'weight gain',
    'rash', 'swelling', 'headache', 'fever', 'fatigue', 'abdominal pain', 'muscle pain',
    'back pain', 'runny nose', 'tremors', 'anxiety', 'cough', 'joint pain',
    'shortness of breath', 'appetite loss'
]

# ─────────────────────────────────────────────────────────────────────────
# Cell 20 — sinonim Bahasa Inggris
# ─────────────────────────────────────────────────────────────────────────
SYMPTOM_SYNONYMS = {
    'fever':               ['fever', 'feverish', 'high temperature'],
    'cough':                ['cough', 'coughing'],
    'headache':             ['headache', 'head pain'],
    'dizziness':            ['dizz', 'vertigo', 'lightheaded', 'spinning'],
    'nausea':               ['nausea', 'nauseous', 'nauseated', 'queasy'],
    'vomiting':             ['vomit', 'throwing up', 'threw up'],
    'fatigue':              ['fatigue', 'tired', 'exhausted', 'weakness', 'weak'],
    'shortness of breath':  ['shortness of breath', 'difficulty breath', 'breathless'],
    'chest pain':           ['chest pain', 'chest ache', 'chest tightness'],
    'abdominal pain':       ['abdominal pain', 'stomach pain', 'belly pain', 'stomach ache'],
    'diarrhea':             ['diarrhea', 'loose stool'],
    'rash':                 ['rash', 'skin rash', 'hives'],
    'swelling':             ['swelling', 'swollen', 'edema'],
    'depression':           ['depress', 'hopeless', 'low mood'],
    'anxiety':               ['anxiety', 'anxious', 'worried', 'panic'],
    'insomnia':              ['insomnia', 'trouble sleeping', 'sleepless', 'cannot sleep'],
    'joint pain':            ['joint pain', 'joint ache', 'stiff joint'],
    'muscle pain':           ['muscle pain', 'muscle ache', 'body ache', 'body pain'],
    'back pain':             ['back pain', 'backache', 'lower back'],
    'weight loss':           ['weight loss', 'losing weight', 'lost weight'],
    'weight gain':           ['weight gain', 'gaining weight'],
    'blurred vision':        ['blurred vision', 'blurry vision', 'double vision'],
    'tremors':               ['tremor', 'shaking', 'shiver', 'trembling'],
    'appetite loss':         ['appetite loss', 'loss of appetite', 'no appetite'],
    'sore throat':           ['sore throat', 'throat pain', 'throat ache'],
    'sneezing':              ['sneez'],
    'runny nose':            ['runny nose', 'nasal discharge', 'stuffy nose'],
    'sweating':              ['sweating', 'sweat', 'night sweat'],
}

# ─────────────────────────────────────────────────────────────────────────
# Cell 22 — keyword Bahasa Indonesia (bilingual support)
# ─────────────────────────────────────────────────────────────────────────
INDO_KEYWORDS = {
    'fever':                ['demam', 'panas tinggi', 'badan panas', 'meriang'],
    'cough':                 ['batuk'],
    'headache':              ['sakit kepala', 'kepala sakit', 'nyeri kepala'],
    'dizziness':             ['pusing', 'kepala berputar', 'kliyengan', 'vertigo', 'pening'],
    'nausea':                ['mual', 'eneg', 'enek'],
    'vomiting':              ['muntah'],
    'fatigue':               ['lemas', 'lelah', 'capek', 'kelelahan', 'tidak bertenaga', 'letih'],
    'shortness of breath':   ['sesak napas', 'susah bernapas', 'napas sesak', 'sesak nafas', 'sesak', 'sesek'],
    'chest pain':            ['sakit dada', 'nyeri dada', 'dada sakit', 'dada nyeri'],
    'abdominal pain':        ['sakit perut', 'nyeri perut', 'perut sakit', 'mulas', 'perih lambung'],
    'diarrhea':              ['diare', 'mencret', 'bab cair'],
    'rash':                  ['ruam', 'gatal', 'bintik merah', 'biduran', 'bentol'],
    'swelling':              ['bengkak', 'pembengkakan', 'membengkak'],
    'depression':            ['depresi', 'sedih berkepanjangan', 'putus asa', 'murung'],
    'anxiety':               ['cemas', 'gelisah', 'khawatir', 'panik', 'was-was'],
    'insomnia':              ['susah tidur', 'tidak bisa tidur', 'sulit tidur', 'insomnia', 'sukar tidur'],
    'joint pain':            ['nyeri sendi', 'sakit sendi', 'sendi sakit', 'ngilu sendi'],
    'muscle pain':           ['nyeri otot', 'sakit otot', 'pegal', 'pegal-pegal', 'otot sakit'],
    'back pain':             ['sakit punggung', 'nyeri punggung', 'punggung sakit', 'sakit pinggang'],
    'weight loss':           ['berat badan turun', 'bb turun', 'kurus mendadak', 'berat turun'],
    'weight gain':           ['berat badan naik', 'bb naik', 'gemuk', 'berat naik'],
    'blurred vision':        ['penglihatan kabur', 'mata kabur', 'pandangan kabur', 'buram'],
    'tremors':               ['gemetar', 'tangan gemetar', 'badan gemetar', 'tremor'],
    'appetite loss':         ['tidak nafsu makan', 'nafsu makan hilang', 'tidak mau makan', 'kehilangan nafsu makan'],
    'sore throat':           ['sakit tenggorokan', 'tenggorokan sakit', 'radang tenggorokan', 'nyeri tenggorokan'],
    'sneezing':              ['bersin'],
    'runny nose':            ['pilek', 'hidung meler', 'ingus', 'hidung tersumbat'],
    'sweating':              ['berkeringat', 'keringat berlebih', 'keringat dingin', 'banyak keringat'],
}

# Nama penyakit umum -> gejala representatif (extend, bukan overwrite)
DISEASE_NAME_HINTS = {
    'fever':          ['flu', 'demam berdarah', 'dbd'],
    'cough':          ['flu', 'batuk pilek'],
    'runny nose':     ['flu', 'pilek'],
    'abdominal pain': ['maag', 'asam lambung', 'gerd'],
    'headache':       ['migrain', 'sinusitis'],
    'dizziness':      ['vertigo'],
    'joint pain':     ['rematik', 'asam urat'],
    'anxiety':        ['panic attack'],
}
for _sym, _kws in DISEASE_NAME_HINTS.items():
    INDO_KEYWORDS.setdefault(_sym, []).extend(_kws)

# Gabungkan INDO_KEYWORDS ke SYMPTOM_SYNONYMS (sesuai notebook cell 22)
for _sym, _kws in INDO_KEYWORDS.items():
    if _sym in SYMPTOM_SYNONYMS:
        SYMPTOM_SYNONYMS[_sym].extend(_kws)
    else:
        SYMPTOM_SYNONYMS[_sym] = _kws

# Terjemahan nama gejala (untuk display & follow-up question dalam Bahasa Indonesia)
SYMPTOM_ID = {
    'fever': 'demam', 'cough': 'batuk', 'headache': 'sakit kepala',
    'dizziness': 'pusing', 'nausea': 'mual', 'vomiting': 'muntah',
    'fatigue': 'lemas', 'shortness of breath': 'sesak napas',
    'chest pain': 'nyeri dada', 'abdominal pain': 'sakit perut',
    'diarrhea': 'diare', 'rash': 'ruam/gatal', 'swelling': 'bengkak',
    'depression': 'depresi', 'anxiety': 'cemas/gelisah',
    'insomnia': 'susah tidur', 'joint pain': 'nyeri sendi',
    'muscle pain': 'nyeri otot/pegal', 'back pain': 'sakit punggung',
    'weight loss': 'berat badan turun', 'weight gain': 'berat badan naik',
    'blurred vision': 'penglihatan kabur', 'tremors': 'gemetar',
    'appetite loss': 'tidak nafsu makan', 'sore throat': 'sakit tenggorokan',
    'sneezing': 'bersin', 'runny nose': 'pilek', 'sweating': 'berkeringat',
}


def extract_symptoms(text: str) -> list[str]:
    """Cari gejala dari SYMPTOMS_28 yang disebut di `text` (EN + ID)."""
    text_lower = text.lower()
    found = set()
    for sym, variants in SYMPTOM_SYNONYMS.items():
        for v in variants:
            if v in text_lower:
                found.add(sym)
                break
    return list(found)


# ─────────────────────────────────────────────────────────────────────────
# Deteksi bahasa hybrid: keyword domain dulu, baru fallback ke langdetect
# ─────────────────────────────────────────────────────────────────────────
try:
    from langdetect import detect as _ld_detect, DetectorFactory
    DetectorFactory.seed = 42
    _HAS_LANGDETECT = True
except ImportError:
    _HAS_LANGDETECT = False
    logger.warning(
        "Package 'langdetect' tidak terpasang — deteksi bahasa hanya akan "
        "pakai keyword matching. Tambahkan 'langdetect' di requirements.txt."
    )

_INDO_KW = {
    'saya', 'aku', 'gua', 'gue', 'dan', 'merasa', 'sakit', 'tidak', 'dok', 'kamu', 'iya',
    'engga', 'sejak', 'juga', 'nyeri', 'dada', 'perut', 'kepala', 'gejala', 'demam',
    'pusing', 'mual', 'batuk', 'sesak', 'lemas', 'dengan', 'yang', 'ini', 'itu', 'sudah',
    'apakah', 'kenapa', 'bagaimana', 'tolong', 'bisa', 'mau', 'ingin', 'nih', 'ya',
    'halo', 'hai', 'pagi', 'siang', 'sore', 'malam', 'selamat',
}
_ENG_KW = {
    'i', 'have', 'feel', 'my', 'and', 'the', 'with', 'since', 'also', 'pain', 'fever',
    'cough', 'dizzy', 'sick', 'doctor', 'chest', 'head', 'stomach', 'am', 'is', 'was',
    'do', 'you', 'can', 'what', 'why', 'how', 'please', 'help', 'having', 'been',
}


def detect_lang_smart(text: str, prev: str = 'en') -> tuple[str, str]:
    """Return ('id'|'en', method). Keyword domain dulu, lalu langdetect, lalu prev."""
    t = text.lower()
    words = t.split()
    id_hits = sum(1 for w in words if w in _INDO_KW)
    en_hits = sum(1 for w in words if w in _ENG_KW)
    if id_hits > en_hits and id_hits >= 1:
        return 'id', f'keyword(id={id_hits},en={en_hits})'
    if en_hits > id_hits and en_hits >= 1:
        return 'en', f'keyword(id={id_hits},en={en_hits})'
    if len(words) >= 2 and _HAS_LANGDETECT:
        try:
            return ('id' if _ld_detect(text) == 'id' else 'en'), 'langdetect'
        except Exception:
            return prev, 'fallback'
    return prev, 'too_short'
