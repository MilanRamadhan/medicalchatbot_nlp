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
BYE = {'bye', 'dadah', 'sampai jumpa', 'selesai', 'udah cukup', 'keluar', 'exit', 'udahan'}
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
        art = self.artifacts
        dialog_df = art.dialog_df
        sub = dialog_df[dialog_df['predicted_disease'] == disease]
        if len(sub) == 0:
            sub = dialog_df
        q = art.tfidf.transform([query])
        sims = cosine_similarity(q, art.tfidf_matrix[sub.index])[0]
        bi = sub.index[sims.argmax()]
        full = dialog_df.loc[bi, 'doctor_text']
        return ' '.join(re.split(r'(?<=[.!?]) +', full.strip())[:3])

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
        w = set(t.split())
        if any(rf in t for rf in RED_FLAG_WORDS):
            return 'red_flag'
        if self.pending and (t in NO or w & NO):
            return 'confirm_no'
        if self.pending and (t in YES or w & YES):
            return 'confirm_yes'
        if t in GREETING or w & GREETING:
            return 'greeting'
        if any(p in t for p in THANKS):
            return 'thanks'
        if t in BYE or any(p in t for p in BYE):
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
        self.reset()
        if ID:
            text = (
                f"**Gejala terdeteksi:** {', '.join(syms)}\n\n"
                f"**Kemungkinan penyakit:** {pred} (confidence: {conf:.0%})\n\n"
                f"**3 kemungkinan teratas:**\n{t3}\n\n"
                f"**Model dasar (tanpa fine-tuning):** {base_str}\n\n"
                f"---\n**Saran medis (sumber dataset, EN):** {advice}\n\n"
                f"*⚠️ Hanya untuk edukasi. Silakan konsultasi ke dokter.*"
            )
        else:
            text = (
                f"**Detected symptoms:** {', '.join(syms)}\n\n"
                f"**Predicted disease:** {pred} ({conf:.0%} confidence)\n\n"
                f"**Top 3 possibilities:**\n{t3}\n\n"
                f"**Base model (no fine-tuning):** {base_str}\n\n"
                f"---\n**Medical advice:** {advice}\n\n"
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
            text = (
                f"Ini pertanyaan kesehatan umum. Dari basis data konsultasi: {advice}\n\n"
                "Kalau kamu punya gejala spesifik, ceritakan ya."
            ) if ID else (
                f"General health question. From our consultation database: {advice}\n\n"
                "If you have specific symptoms, please describe them."
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
