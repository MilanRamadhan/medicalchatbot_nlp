# Catatan Bug & Keterbatasan Chatbot (untuk perbaikan)

Ditemukan lewat *adversarial testing* manual pada 2026-06-19 (sesi demo
frontend ↔ backend). Semua issue ada di logika `backend/app/chatbot.py` dan
`backend/app/nlp_utils.py` — **bukan** masalah frontend. Diurut by severity.

> **UPDATE 2026-06-19 — sebagian besar SUDAH DIPERBAIKI & diuji.** Lihat kolom
> "Status" di tabel ringkasan paling bawah. Yang ditunda hanya #3 & #9 karena
> butuh retraining/kalibrasi model (berisiko menurunkan akurasi kalau diubah
> sembarangan).

---

## P0 — SAFETY (wajib diperbaiki sebelum dipresentasikan)

### 1. Keluhan medis dianggap "selamat tinggal" karena substring "keluar"
**Repro:** input `"saya sakit penis hingga keluar nanah"` → bot menjawab
`"Baik, jaga kesehatan ya! 🙏"` (intent **bye**) dan keluhan diabaikan total.

**Akar masalah:** `chatbot.py` → `_intent()`:
```python
if t in BYE or any(p in t for p in BYE):   # BYE berisi 'keluar'
    return 'bye'
```
Kata `'keluar'` ada di set `BYE`, dan dicek dengan **substring** (`p in t`),
jadi `"keluar nanah"` ke-trigger sebagai "keluar/exit".

**Dampak:** keluhan serius (indikasi IMS/gonore: keluarnya nanah dari penis)
ditolak dengan ucapan perpisahan. Ini failure mode terburuk — berbahaya &
memalukan saat demo.

**Saran fix:**
- Jangan pakai substring untuk BYE/GREETING. Pakai pencocokan **kata utuh**
  (token-level), mis. `w & BYE` (set kata), bukan `any(p in t for p in BYE)`.
- Atau hapus kata ambigu (`'keluar'`, `'selesai'`) dari set substring dan hanya
  cocokkan frasa eksplisit (`'keluar dari chat'`, `'sudah selesai'`).

### 2. Tidak ada coverage / red-flag untuk gejala genital & "nanah"
`penis`, `nanah`, `keputihan`, dll. tidak dikenali sebagai gejala dan tidak ada
di `RED_FLAG_WORDS`. Idealnya keluarnya nanah → diarahkan ke saran periksa ke
dokter, bukan diabaikan.

**Saran fix:** tambah kata kunci ini ke daftar gejala/red-flag dengan pesan
"segera konsultasi ke dokter/klinik".

---

## P1 — KEBENARAN (model bisa salah arah)

### 3. Jawaban "tidak" tidak ikut ke classifier
**Repro:** keluhan hanya `"sakit kepala"`, lalu user jawab **tidak** untuk
pilek, demam, batuk, tenggorokan → model tetap menebak **Sinusitis (61%)**,
padahal sinusitis biasanya justru ADA pilek/demam.

**Akar masalah:** `_classify()` hanya memakai `self.symptoms` (gejala yang
DIIYAKAN). Gejala yang ditolak (`self.rejected`) cuma dipakai `_next_question()`
untuk memilih pertanyaan, **tidak** masuk ke input prediksi.

**Saran fix:** masukkan konteks negatif ke teks input model
(mis. `"headache, no fever, no cough"`), atau turunkan skor penyakit yang
gejala wajibnya sudah ditolak user.

### 4. Jawaban tidak pasti ("mungkin") ditolak sebagai off-topic
**Repro:** saat ada pending `"sesak napas?"`, user jawab `"mungkin"` →
`"Maaf, saya hanya bisa membantu seputar kesehatan..."`.

**Akar masalah:** `_intent()` hanya mengenali `YES`/`NO`. "mungkin/kayaknya/
ragu" tidak tertangani → jatuh ke `off_topic`, dan `pending` tidak di-clear.

**Saran fix:** tambah set `UNSURE = {'mungkin','kayaknya','ragu','kurang tahu'}`
→ perlakukan sebagai "lewati gejala ini" (tambahkan ke rejected/ skip) lalu
lanjut pertanyaan berikutnya, jangan tolak.

### 5. Off-topic guard bisa di-bypass dengan menempel kata kesehatan
**Repro:** `"buatkan saya script javascript menghitung 1+1"` → ditolak (benar).
Tapi `"...menghitung 1+1 seputar kesehatan"` → lolos guard (karena `'kesehatan'`
∈ `HEALTH_CTX`) dan bot lanjut seakan input valid.

**Akar masalah:** `if w & HEALTH_CTX: return 'health_q'` — satu kata kunci
kesehatan cukup untuk mem-bypass guard.

**Saran fix:** guard off-topic perlu lebih kuat (mis. rasio kata kesehatan,
atau cek apakah benar ada keluhan/gejala, bukan sekadar 1 kata kunci).

---

## P2 — KUALITAS / POLISH

### 6. Fallback "pertanyaan kesehatan umum" memberi jawaban identik & ngawur
**Repro:** `"saya sakit anus"` dan `"saya sakit kaki"` → **dua-duanya** dijawab
sama persis: *"...You are already on antibiotics."* (tidak relevan).

**Akar masalah:** `health_q` selalu memanggil `_retrieve('Common Cold', ...)`;
untuk query yang tak match, TF-IDF mengembalikan dialog terdekat yang sama.

**Saran fix:** kalau similarity di bawah ambang, jangan tampilkan retrieval —
minta user sebutkan gejala lebih spesifik. Tambah juga "sakit anus/kaki" ke
kosakata gejala bila relevan dengan 30 kelas penyakit.

### 7. Ekstraksi gejala berbasis kata kunci: "pening" → "sakit kepala"
`"pening"` dipetakan ke *headache*, padahal *pening* sering = pusing/berputar
(dizziness) yang secara medis berbeda. Keterbatasan kamus sinonim di
`nlp_utils.py`.

### 8. Saran medis retrieval kadang tidak nyambung
Contoh sebelumnya: gejala demam+batuk → saran soal "pregnant"; sakit kepala →
saran soal "palpitations". Retrieval mengambil dialog termirip secara TF-IDF,
belum tentu relevan secara klinis. Pertimbangkan filter ambang similarity.

### 9. Over-confidence pada gejala sedikit & umum
`"sakit perut + muntah"` → Ulcer **97%** padahal Gastritis (sangat mirip) 0%.
Angka ini output softmax, bukan probabilitas medis terkalibrasi. Cukup
ditampilkan apa adanya + disclaimer (sudah ada), tapi sadari ini keterbatasan.

---

## Ringkasan prioritas & status

| # | Issue | Severity | Status | Lokasi / cara fix |
|---|---|---|---|---|
| 1 | "keluar nanah" → bye | **P0** | ✅ Fixed | `_intent()`: 'keluar'/'selesai' dibuang dari `BYE`, kata tunggal dicocokkan utuh (`_BYE_WORDS`) |
| 2 | gejala genital/nanah tak ter-cover | **P0** | ✅ Fixed | intent `urgent_referral` baru + set `URGENT_REFERRAL` (nanah, keputihan, dll → arahkan ke dokter) |
| 3 | "tidak" diabaikan classifier | P1 | ⏳ Ditunda | butuh model negation-aware / retraining — berisiko |
| 4 | "mungkin"/"sedikit" ditolak | P1 | ✅ Fixed | set `UNSURE` (skip) & `PARTIAL_YES` (=iya) di `_intent()` |
| 5 | guard off-topic mudah di-bypass | P1 | ✅ Fixed | set `CODE_OFFTOPIC` override di `_intent()` |
| 6 | fallback health_q identik/ngawur | P2 | ✅ Fixed | `_retrieve()` return None bila tak relevan → minta gejala spesifik |
| 7 | "pening" → headache | P2 | ✅ Fixed | `nlp_utils.py`: 'pening' dipindah ke `dizziness` |
| 8 | retrieval advice tak relevan/kosong | P2 | ✅ Fixed | `RETRIEVAL_MIN_SIM` + `_clean_advice()` buang kalimat basa-basi |
| 9 | over-confidence | P2 | ⏳ Ditunda | kalibrasi/training model |

Bonus: bare "sesak" kini dikenali (`nlp_utils.py` → `shortness of breath`).
Semua fix sudah diuji via `curl` ke `/chat` (2026-06-19).

Robustness tambahan (2026-06-19):
- Frasa dada bersisipan dikenali: `dada terasa nyeri/sakit/berat`, `dada berat`,
  `nyeri/sakit di dada` (`nlp_utils.py` → `chest pain`).
- Tokenisasi `_intent()` pakai `re.findall(r"[\w']+", t)` (bukan `split()`),
  jadi tanda baca/backslash di ujung jawaban ("tidak\\", "iya!", "ngga,") tetap
  terbaca sebagai ya/tidak — tidak lagi jatuh ke off-topic.

---

## Contoh repro tambahan (sesi tes 2026-06-19)

Memperkuat issue di atas dengan transkrip nyata:

- **Issue #4 (jawaban tak-pasti ditolak):** pending "sesak napas?" → user jawab
  **`"sedikit"`** → bot balas *"Maaf, saya hanya bisa membantu seputar
  kesehatan…"*. (Sama seperti `"mungkin"`.) Perlu set `UNSURE`/partial-yes.
- **Issue #2 (coverage gejala):** **`"saya sesak"`** ditolak off-topic, tapi
  **`"saya sesak napas"`** dikenali → Heart Disease 88%. Kata parsial "sesak"
  belum masuk kamus gejala.
- **Issue #8 (saran retrieval ngawur/kosong):**
  - Diagnosis **Pneumonia** → saran soal **Typhoid/Salmonella** (beda penyakit).
  - Diagnosis **Ulcer** → saran hanya *"Hi ! Good evening. I am Chat Doctor
    answering your query."* (tanpa isi medis).
- **Issue #3 (negatif diabaikan):** hanya gejala **`demam`** (sesak, nyeri dada,
  berkeringat, batuk semua dijawab "tidak") → tetap **Pneumonia 58%**, padahal
  gejala khas pneumonia justru ditolak semua.
- **Catatan (bukan bug):** kolom "Model dasar (tanpa fine-tuning)" selalu
  "Thyroid Disorder (5%)" apa pun input-nya — wajar karena base `roberta-base`
  belum dilatih; justru memperlihatkan dampak fine-tuning.

---

## Penambahan fitur (2026-06-19): saran medis ikut bahasa user

"Saran medis" diambil mentah dari dataset dialog dokter (ChatDoctor) yang
**berbahasa Inggris**. Ditambahkan **terjemahan otomatis EN→ID** supaya saran
tampil sesuai bahasa user.

Pipeline terjemahan berlapis di `chatbot._translate_to_id()`:
1. **Google Translate** (`deep-translator`) — UTAMA. Kualitas medis terbaik
   (nama obat & istilah tidak rusak, mis. cetirizine/saline tetap benar).
   Butuh internet saat jalan.
2. **MarianMT lokal** (`Helsinki-NLP/opus-mt-en-id`, di-load di `artifacts.py`
   sebagai `Artifacts.translator=(tok,model)`, ±300MB cache) — fallback offline,
   kualitas lebih kasar (drug names sering rusak).
3. Gagal semua → saran tetap Bahasa Inggris.

- **Dependency baru:** `deep-translator` (Google, utama) + `sentencepiece`
  (untuk MarianTokenizer fallback).
- **Label:** lang `id` & terjemahan berhasil → **"Saran medis:"**; lang `en`
  → **"Medical advice:"**; terjemahan gagal → **"Saran medis (sumber dataset, EN):"**.
- **Catatan transformers:** `pipeline("translation")` tidak terdaftar di versi
  terpasang → Marian dipakai via `AutoModelForSeq2SeqLM.generate()`.
- Startup backend pertama lebih lama (download model Marian ±300MB sekali; sudah
  ke-cache di mesin Milan).
