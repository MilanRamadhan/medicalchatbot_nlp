# Backend — Medical Chatbot API

Backend FastAPI yang membungkus class `MedicalChatbot` dari
`medical_chatbot_utama.ipynb` jadi 3 endpoint REST yang dikonsumsi
frontend Next.js: `/chat`, `/reset`, `/metrics` (+ bonus `/health`).

## 1. Struktur folder

```
medicalchatbot_nlp/
├── medical_chatbot_utama.ipynb
├── outputs/                       ← sudah ada di repo + file dari Drive
│   ├── metrics.json
│   ├── disease_symptom_stats.json
│   ├── tfidf_vectorizer.pkl
│   ├── dialog_index.csv           ← DOWNLOAD dari Drive
│   ├── tfidf_matrix.npz           ← DOWNLOAD dari Drive
│   ├── best_checkpoint/
│   │   ├── config.json, tokenizer_config.json, ...
│   │   └── model.safetensors      ← DOWNLOAD dari Drive
│   └── roberta_finetuned/
│       ├── config.json, label_mappings.json, ...
│       └── model.safetensors      ← DOWNLOAD dari Drive
└── backend/                       ← folder baru ini
    ├── app/
    │   ├── __init__.py
    │   ├── nlp_utils.py            (Cell 7, 20, 22)
    │   ├── artifacts.py            (Cell 35/37 — load model & data)
    │   ├── chatbot.py              (Cell 33/34 — class MedicalChatbot)
    │   ├── schemas.py              (Pydantic request/response)
    │   └── main.py                 (FastAPI app + endpoint)
    └── requirements.txt
```

> Catatan path: `backend/app/artifacts.py` membaca artifact dari
> `<root_repo>/outputs/...` secara otomatis (relatif terhadap lokasi file,
> bukan terhadap current working directory) — jadi tidak masalah kamu
> jalankan `uvicorn` dari folder mana pun, selama struktur folder di atas
> tidak diubah. Kalau mau override, set env var `MEDCHATBOT_ROOT`.

## 2. Download artifact dari Google Drive

Sebelum jalan, download 4 file ini dari folder Drive (link sudah ada di
catatan kamu) dan taruh di lokasi berikut — **jangan tertukar** dua file
`model.safetensors` yang namanya sama tapi isinya beda:

| File | Taruh di |
|---|---|
| `model.safetensors` (untuk model fine-tuned/prediksi) | `outputs/best_checkpoint/model.safetensors` |
| `model.safetensors` (untuk yang menyimpan tokenizer) | `outputs/roberta_finetuned/model.safetensors` |
| `dialog_index.csv` | `outputs/dialog_index.csv` |
| `tfidf_matrix.npz` | `outputs/tfidf_matrix.npz` |

## 3. Install & jalankan

```bash
cd backend
python -m venv venv && source venv/bin/activate   # opsional tapi disarankan
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

Pertama kali jalan, server akan mencoba download `roberta-base` dari
Hugging Face Hub (untuk kolom "model dasar tanpa fine-tuning" di hasil
diagnosis) — butuh koneksi internet sekali saja, setelah itu di-cache.
Kalau gagal/tidak ada internet, server tetap jalan normal, cuma kolom
perbandingan itu kosong.

Cek server sudah siap:
```bash
curl http://localhost:8000/health
# {"status":"ok","artifacts_loaded":true,"detail":null}
```

Kalau `artifacts_loaded: false`, baca field `detail` — biasanya artinya
ada file dari Drive yang belum kamu taruh di tempat yang benar (lihat
langkah 2).

## 4. Endpoint

### `POST /chat`
Request:
```json
{ "message": "saya demam dan batuk sejak 2 hari", "session_id": null, "lang_mode": "auto" }
```
- `session_id`: kosongkan (atau `null`) di pesan pertama — backend akan
  generate dan mengembalikannya. Kirim balik `session_id` yang sama di
  setiap pesan berikutnya supaya chatbot "ingat" konteks percakapan
  (gejala yang sudah disebut, giliran bertanya, dst).
- `lang_mode`: `"auto"` (default, deteksi otomatis ID/EN per pesan),
  atau paksa `"id"` / `"en"`.

Response:
```json
{
  "session_id": "3f1c9a2e-...",
  "reply": "Sudah dicatat: **fever, cough**.\n\nDo you also experience **fatigue**?",
  "format": "markdown",
  "lang": "en",
  "state": {
    "symptoms": ["fever", "cough"],
    "rejected_symptoms": [],
    "pending_confirmation": "fatigue",
    "turn": 1
  },
  "diagnosis": null
}
```
- `format: "markdown"` → field `reply` berisi markdown (`**bold**`, dst).
  Render di React dengan `react-markdown`.
- `diagnosis` hanya terisi (bukan `null`) saat chatbot sudah memutuskan
  untuk memberi diagnosis akhir — isinya data terstruktur
  (`predicted_disease`, `confidence`, `top3`, dst) supaya frontend bisa
  bikin card/chart sendiri tanpa harus parsing markdown.

### `POST /reset`
Request: `{ "session_id": "3f1c9a2e-..." }`
Reset state percakapan (gejala yang terkumpul dihapus), tapi bahasa yang
terdeteksi sebelumnya tetap dipakai untuk konsistensi — sama seperti
behavior di notebook aslinya.

### `GET /metrics`
```json
{
  "base": { "accuracy": 0.0356, "f1_macro": 0.0035 },
  "finetuned": { "accuracy": 0.8668, "f1_macro": 0.8662, "precision_macro": 0.8753, "recall_macro": 0.8664 },
  "num_classes": 30,
  "num_dialogs": 12345
}
```
Semua angka desimal asli (bukan string), aman langsung dipakai di
chart/tabel React.

### `GET /health`
Cek cepat status server & artifact — enak dipanggil saat frontend mount,
sebelum tampilkan UI chat.

## 5. Kenapa state disimpan per-`session_id`?

Notebook aslinya cuma punya satu `bot = MedicalChatbot()` global (cocok
untuk demo Gradio satu pengguna). Begitu dibungkus jadi REST API yang
bisa diakses banyak tab/user sekaligus dari Next.js, satu instance
global akan bikin gejala user A tercampur ke sesi user B. Makanya
backend ini simpan satu `MedicalChatbot` per `session_id` di dictionary
in-memory (`SESSIONS` di `main.py`). Cukup untuk skala tugas akhir; kalau
nanti perlu persist antar-restart server, gampang diganti jadi Redis/DB.

## 6. Testing cepat tanpa frontend

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "saya demam dan pusing"}'
```
