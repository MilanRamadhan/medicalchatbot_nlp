"""
chatbot.py
Class MedicalChatbot — diporting dari notebook Cell 34, dengan satu
perubahan penting: model/tokenizer/data TIDAK lagi diambil dari variabel
global notebook, tapi dari objek `Artifacts` yang di-inject lewat
constructor. Ini supaya backend bisa load artifact sekali di startup
dan dipakai bersama oleh banyak instance MedicalChatbot (1 instance / sesi).

Layers: intent detection, off-topic guard, state manager,
        symptom gathering, health Q&A, red-flag detection.
"""

from __future__ import annotations

import re
from typing import Optional

import torch
from sklearn.metrics.pairwise import cosine_similarity

from .artifacts import Artifacts
from .nlp_utils import SYMPTOMS_28, SYMPTOM_ID, extract_symptoms, detect_lang_smart

CONFIDENCE_THRESHOLD = 0.70
MAX_TURNS = 5
# Di bawah ambang kemiripan ini, dialog hasil retrieval dianggap tidak relevan
# (jangan ditampilkan sebagai "saran medis").
RETRIEVAL_MIN_SIM = 0.06

# Kalimat pembuka basa-basi yang sering muncul di dataset dialog dokter
# ("Hi", "Thanks for your question", "I am Chat Doctor ...") — dibuang dari
# saran medis supaya yang tersisa hanya konten yang berguna.
_ADVICE_FILLER_RE = re.compile(
    r'^(hi|hello|hey|dear|thanks?|thank you|welcome|good (morning|afternoon|evening|day)|'
    r'i am (a )?chat ?doctor|i understand|i can understand|i have (gone|reviewed|read)|'
    r'greetings|noted|ok|okay)\b',
    re.I,
)

GREETING = {
    'halo', 'hai', 'hi', 'hello', 'hey', 'pagi', 'siang', 'sore', 'malam',
    'assalamualaikum', 'permisi', 'selamat', 'help', 'tolong',
}
YES = {
    'iya', 'ya', 'ada', 'benar', 'betul', 'yoi', 'yup', 'yes', 'yep', 'y', 'iyaa',
    'betul dok', 'ada dok', 'iya dok', 'ho oh', 'hooh', 'yoa',
}
NO = {
    'tidak', 'ngga', 'nggak', 'enggak', 'gak', 'engga', 'no', 'nope', 'tdk', 'bukan',
    'ga', 'gada', 'tidak ada', 'ga ada', 'engga dok', 'enggak dok',
}
THANKS = {'terima kasih', 'makasih', 'thanks', 'thank you', 'thx', 'tengkyu', 'makasi', 'trims'}
BYE = {'bye', 'dadah', 'sampai jumpa', 'udah cukup', 'sudah cukup', 'exit', 'udahan'}
# CATATAN: 'keluar' & 'selesai' SENGAJA tidak dimasukkan — keduanya ambigu
# dengan keluhan medis (mis. "keluar nanah", "menyelesaikan") dan dulu memicu
# false-match substring yang berbahaya. Kata tunggal dicocokkan utuh di
# _intent() (lihat _BYE_WORDS), frasa multi-kata sebagai substring.
_BYE_WORDS = {b for b in BYE if ' ' not in b}
_BYE_PHRASES = {b for b in BYE if ' ' in b}
HEALTH_CTX = {
    'sakit', 'nyeri', 'gejala', 'penyakit', 'dokter', 'obat', 'demam', 'sehat',
    'kesehatan', 'badan', 'tubuh', 'sick', 'pain', 'disease', 'doctor', 'medicine',
    'health', 'hurt', 'feel', 'rasa', 'merasa', 'keluhan', 'mengalami', 'kondisi',
    'flu', 'pilek', 'batuk', 'meriang', 'masuk angin', 'virus', 'infeksi', 'radang',
    'alergi', 'mual', 'pusing', 'lemas', 'capek', 'diare', 'sembuh',
}
# Red-flag: gejala/kata yang butuh perhatian darurat
RED_FLAG_WORDS = {
    'pingsan', 'tidak sadar', 'kejang', 'pendarahan hebat', 'sesak berat',
    'nyeri dada hebat', 'sulit bernapas', 'unconscious', 'seizure', 'severe bleeding',
}
# Jawaban tidak-pasti / parsial untuk pertanyaan ya/tidak. Dulu jatuh ke
# off_topic. 'sedikit/agak' = "iya" lemah (gejala ada); 'mungkin/ragu' = skip.
PARTIAL_YES = {
    'sedikit', 'agak', 'dikit', 'lumayan', 'kadang', 'kadang-kadang',
    'kadang kadang', 'sesekali', 'rada', 'sedikit sih',
}
UNSURE = {
    'mungkin', 'kurang tau', 'kurang tahu', 'ga tau', 'gak tau', 'nggak tau',
    'tidak tau', 'tidak tahu', 'entah', 'tidak yakin', 'ragu', 'kayaknya',
    'kurang yakin',
}
# Keluhan yang perlu segera diperiksa dokter (bukan darurat 119, tapi jangan
# diabaikan / dianggap off-topic). Dicocokkan sebagai substring.
URGENT_REFERRAL = {
    'nanah', 'keputihan', 'keluar darah', 'muntah darah', 'bab berdarah',
    'benjolan', 'kencing berdarah', 'kencing darah',
}
# Permintaan non-medis yang umum dipakai untuk menembus guard off-topic
# (mis. "buatkan script ... seputar kesehatan").
CODE_OFFTOPIC = {
    'javascript', 'python', 'php', 'html', 'css', 'sql', 'script', 'kode',
    'coding', 'program', 'pemrograman', 'matematika', 'terjemahkan', 'translate',
}


class MedicalChatbot:
    def __init__(self, artifacts: Artifacts, lang_mode: str = 'auto'):
        self.artifacts = artifacts
        self.lang_mode = lang_mode  # 'auto' | 'id' | 'en'
        self.symptoms: list[str] = []
        self.rejected: list[str] = []
        self.pending: Optional[str] = None
        self.turn = 0
        self.lang = 'en'

    def reset(self) -> None:
        self.symptoms = []
        self.rejected = []
        self.pending = None
        self.turn = 0  # NOTE: bahasa TIDAK direset agar konsisten dalam sesi

    # ── classification (RoBERTa) ──
    def _classify(self, mdl, syms):
        if mdl is None:
            return None, [], 0.0
        text = ', '.join(sorted(syms)) if syms else ''
        if not text:
            return None, [], 0.0
        art = self.artifacts
        enc = art.tokenizer(
            text, return_tensors='pt', max_length=art.max_len,
            truncation=True, padding='max_length',
        )
        with torch.no_grad():
            logits = mdl(
                enc['input_ids'].to(art.device),
                enc['attention_mask'].to(art.device),
            ).logits
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
        idx3 = probs.argsort()[-3:][::-1]
        top3 = [(art.id2label[int(i)], float(probs[i])) for i in idx3]
        return top3[0][0], top3, float(probs[idx3[0]])

    # ── retrieval (TF-IDF) ──
    def _retrieve(self, disease, query):
        """Ambil saran dari dialog termirip. Return None kalau tidak ada yang
        cukup relevan (di bawah ambang) atau isinya cuma basa-basi."""
        art = self.artifacts
        dialog_df = art.dialog_df
        sub = dialog_df[dialog_df['predicted_disease'] == disease]
        if len(sub) == 0:
            sub = dialog_df
        q = art.tfidf.transform([query])
        sims = cosine_similarity(q, art.tfidf_matrix[sub.index])[0]
        best = int(sims.argmax())
        if sims[best] < RETRIEVAL_MIN_SIM:
            return None  # tidak ada dialog yang cukup relevan dengan keluhan
        bi = sub.index[best]
        full = dialog_df.loc[bi, 'doctor_text']
        return self._clean_advice(full)

    @staticmethod
    def _clean_advice(text):
        """Buang kalimat pembuka basa-basi, ambil maksimal 3 kalimat berisi.
        Return None kalau setelah dibersihkan tidak ada konten."""
        sents = re.split(r'(?<=[.!?]) +', str(text).strip())
        meaningful = [
            s for s in sents
            if not _ADVICE_FILLER_RE.match(s.strip()) and len(s.strip()) >= 8
        ]
        advice = ' '.join(meaningful[:3]).strip()
        return advice or None

    def _translate_to_id(self, text):
        """Terjemahkan EN->ID (best-effort). Prioritas kualitas:
          1) Google Translate (deep-translator) — terbaik utk istilah medis &
             nama obat, tapi butuh internet.
          2) Model lokal MarianMT — fallback offline (kualitas lebih kasar).
          3) None — saran tetap Bahasa Inggris.
        """
        if not text:
            return None

        # 1) Google Translate
        try:
            from deep_translator import GoogleTranslator

            out = GoogleTranslator(source='en', target='id').translate(text)
            if out and out.strip():
                return out.strip()
        except Exception:  # noqa: BLE001
            pass  # lanjut ke fallback offline

        # 2) MarianMT lokal (kalau translator artifact tersedia)
        tr = getattr(self.artifacts, 'translator', None)
        if tr:
            try:
                tok, mdl = tr
                art = self.artifacts
                enc = tok(
                    text, return_tensors='pt', truncation=True, max_length=512,
                ).to(art.device)
                with torch.no_grad():
                    gen = mdl.generate(**enc, max_length=512, num_beams=1)
                out = tok.batch_decode(gen, skip_special_tokens=True)
                if out and out[0].strip():
                    return out[0].strip()
            except Exception:  # noqa: BLE001
                pass

        return None

    def _next_question(self, top3):
        if not top3:
            return None
        stats = self.artifacts.disease_symptom_stats
        d1 = top3[0][0]
        d2 = top3[1][0] if len(top3) > 1 else d1
        s1 = stats.get(d1, {})
        s2 = stats.get(d2, {})
        best, score = None, -1
        for sym in SYMPTOMS_28:
            if sym in self.symptoms or sym in self.rejected:
                continue
            sc = s1.get(sym, 0) - s2.get(sym, 0)
            if sc > score:
                score, best = sc, sym
        return best

    # ── intent detection ──
    def _intent(self, text):
        t = text.lower().strip()
        # Tokenisasi pakai regex kata (bukan split spasi) supaya tanda baca /
        # backslash di ujung tidak merusak pencocokan, mis. "tidak\\" / "iya!"
        # tetap terbaca sebagai "tidak" / "iya".
        w = set(re.findall(r"[\w']+", t))
        if any(rf in t for rf in RED_FLAG_WORDS):
            return 'red_flag'
        if any(u in t for u in URGENT_REFERRAL):
            return 'urgent_referral'
        # Jawaban atas pertanyaan follow-up (hanya saat ada pending).
        # 'tidak'/'mungkin'/'ragu' -> skip; 'iya'/'sedikit'/'agak' -> punya gejala.
        if self.pending and (t in NO or w & NO or t in UNSURE or (w & UNSURE)):
            return 'confirm_no'
        if self.pending and (t in YES or w & YES or t in PARTIAL_YES or (w & PARTIAL_YES)):
            return 'confirm_yes'
        # Permintaan non-medis yang menempel kata kesehatan -> tetap off-topic.
        if (w & CODE_OFFTOPIC) and not extract_symptoms(text):
            return 'off_topic'
        if t in GREETING or w & GREETING:
            return 'greeting'
        if any(p in t for p in THANKS):
            return 'thanks'
        # Bye: kata tunggal dicocokkan utuh (hindari 'keluar' di "keluar nanah");
        # frasa multi-kata dicocokkan sebagai substring.
        if (w & _BYE_WORDS) or any(p in t for p in _BYE_PHRASES):
            return 'bye'
        if extract_symptoms(text):
            return 'symptom'
        if w & HEALTH_CTX:
            return 'health_q'
        return 'off_topic'

    def _diagnose(self, ID):
        art = self.artifacts
        pred, top3, conf = self._classify(art.model, self.symptoms)
        pb, _, cb = self._classify(art.base_model, self.symptoms)
        advice = self._retrieve(pred, ' '.join(self.symptoms))
        syms = [SYMPTOM_ID.get(s, s) for s in self.symptoms] if ID else list(self.symptoms)
        base_str = f"{pb} ({cb:.0%})" if pb else "—"
        t3 = '\n'.join([f"  {i + 1}. {d} — {p:.0%}" for i, (d, p) in enumerate(top3)])
        result = {
            "predicted_disease": pred,
            "confidence": conf,
            "top3": [{"disease": d, "probability": p} for d, p in top3],
            "base_model_prediction": pb,
            "base_model_confidence": cb,
            "advice": advice,
            "symptoms": list(self.symptoms),
        }
        # Blok saran hanya ditampilkan kalau retrieval menghasilkan konten relevan.
        # Saat bahasa = ID, saran (yang asalnya EN) diterjemahkan; kalau translator
        # tidak tersedia, fallback ke teks Inggris dengan label "(EN)".
        advice_local = self._translate_to_id(advice) if (advice and ID) else None
        advice_id = (
            f"---\n**Saran medis:** {advice_local}\n\n"
            if advice_local
            else (f"---\n**Saran medis (sumber dataset, EN):** {advice}\n\n" if advice else "")
        )
        advice_en = f"---\n**Medical advice:** {advice}\n\n" if advice else ""

        self.reset()
        if ID:
            text = (
                f"**Gejala terdeteksi:** {', '.join(syms)}\n\n"
                f"**Kemungkinan penyakit:** {pred} (confidence: {conf:.0%})\n\n"
                f"**3 kemungkinan teratas:**\n{t3}\n\n"
                f"**Model dasar (tanpa fine-tuning):** {base_str}\n\n"
                f"{advice_id}"
                f"*⚠️ Hanya untuk edukasi. Silakan konsultasi ke dokter.*"
            )
        else:
            text = (
                f"**Detected symptoms:** {', '.join(syms)}\n\n"
                f"**Predicted disease:** {pred} ({conf:.0%} confidence)\n\n"
                f"**Top 3 possibilities:**\n{t3}\n\n"
                f"**Base model (no fine-tuning):** {base_str}\n\n"
                f"{advice_en}"
                f"*⚠️ Educational purposes only. Please consult a real doctor.*"
            )
        return text, result

    # ── main ──
    def chat(self, user_input: str):
        """Return (reply_text: str, diagnosis: dict|None)."""
        self.turn += 1
        if self.lang_mode in ('id', 'en'):
            self.lang = self.lang_mode
        else:  # auto
            self.lang, _m = detect_lang_smart(user_input, prev=self.lang)
        ID = self.lang == 'id'

        intent = self._intent(user_input)

        if intent == 'red_flag':
            self.turn -= 1
            text = (
                "🚨 Gejala yang kamu sebutkan bisa menandakan kondisi DARURAT. "
                "Segera hubungi IGD terdekat atau layanan darurat 119. "
                "Jangan tunda!"
            ) if ID else (
                "🚨 Your symptoms may indicate an EMERGENCY. "
                "Please contact emergency services immediately. Don't wait!"
            )
            return text, None

        if intent == 'urgent_referral':
            self.turn -= 1
            text = (
                "Keluhan yang kamu sebutkan sebaiknya **diperiksa langsung oleh "
                "dokter/tenaga medis** untuk pemeriksaan lebih lanjut. Jangan "
                "ditunda ya, dan hindari mengobati sendiri."
            ) if ID else (
                "The symptom you mentioned should be **examined by a doctor** "
                "for proper evaluation. Please don't delay, and avoid "
                "self-medication."
            )
            return text, None

        if intent == 'greeting':
            self.turn -= 1
            text = (
                "Halo! Saya asisten kesehatan berbasis AI. Ceritakan keluhan atau "
                "gejala yang kamu rasakan, misalnya: \"saya demam dan batuk sejak 2 hari\"."
            ) if ID else (
                "Hello! I'm an AI health assistant. Describe your symptoms, e.g. "
                "\"I have fever and cough for 2 days\"."
            )
            return text, None

        if intent == 'off_topic':
            self.turn -= 1
            text = (
                "Maaf, saya hanya bisa membantu seputar **kesehatan dan gejala penyakit**. "
                "Coba ceritakan keluhan yang kamu rasakan ya."
            ) if ID else (
                "Sorry, I can only help with **health and symptoms**. "
                "Please describe what you're feeling."
            )
            return text, None

        if intent == 'thanks':
            self.turn -= 1
            text = "Sama-sama! Semoga lekas sembuh. Ada keluhan lain?" if ID else \
                "You're welcome! Get well soon. Any other symptoms?"
            return text, None

        if intent == 'bye':
            self.reset()
            text = "Baik, jaga kesehatan ya! 🙏" if ID else "Take care! 🙏"
            return text, None

        if intent == 'confirm_yes':
            if self.pending and self.pending not in self.symptoms:
                self.symptoms.append(self.pending)
            self.pending = None
        if intent == 'confirm_no':
            if self.pending:
                self.rejected.append(self.pending)
                if self.pending in self.symptoms:
                    self.symptoms.remove(self.pending)
            self.pending = None

        for s in extract_symptoms(user_input):
            if s in self.rejected:
                continue  # jangan tambah lagi gejala yang baru saja ditolak
            if s not in self.symptoms:
                self.symptoms.append(s)

        if intent == 'health_q' and not self.symptoms:
            self.turn -= 1
            advice = self._retrieve('Common Cold', user_input)  # general retrieval
            if advice:
                if ID:
                    shown = self._translate_to_id(advice) or advice
                    text = (
                        f"{shown}\n\n"
                        "Kalau kamu punya gejala spesifik, ceritakan ya."
                    )
                else:
                    text = (
                        f"From our consultation database: {advice}\n\n"
                        "If you have specific symptoms, please describe them."
                    )
            else:
                text = (
                    "Boleh ceritakan gejala spesifik yang kamu rasakan? "
                    "Misalnya demam, batuk, nyeri dada, atau mual."
                ) if ID else (
                    "Could you describe the specific symptoms you feel? "
                    "For example fever, cough, chest pain, or nausea."
                )
            return text, None

        if not self.symptoms:
            text = (
                "Saya belum menangkap gejala spesifik. Coba sebutkan apa yang dirasakan "
                "— misal demam, mual, nyeri dada?"
            ) if ID else (
                "I didn't catch specific symptoms. Try naming what you feel."
            )
            return text, None

        pred, top3, conf = self._classify(self.artifacts.model, self.symptoms)
        should = (
            conf >= CONFIDENCE_THRESHOLD
            or len(self.symptoms) >= 5
            or self.turn >= MAX_TURNS
        )

        if should:
            return self._diagnose(ID)

        nxt = self._next_question(top3)
        self.pending = nxt
        syms = [SYMPTOM_ID.get(s, s) for s in self.symptoms] if ID else list(self.symptoms)
        if nxt:
            ns = SYMPTOM_ID.get(nxt, nxt) if ID else nxt
            text = (
                f"Sudah dicatat: **{', '.join(syms)}**.\n\n"
                f"Untuk mempersempit diagnosis — apakah kamu juga mengalami **{ns}**?"
            ) if ID else (
                f"Noted: **{', '.join(syms)}**.\n\nDo you also experience **{ns}**?"
            )
            return text, None
        return self._diagnose(ID)
