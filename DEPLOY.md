# Panduan Deploy — Frontend (Vercel) + Backend (Hugging Face Spaces)

Arsitektur online:
- **Frontend (Next.js)** → Vercel
- **Backend (FastAPI + model)** → Hugging Face Spaces (Docker)

Urutan: **kerjakan BACKEND dulu** (Bagian A) supaya dapat URL-nya, baru frontend
(Bagian B), lalu sambungkan (Bagian C).

---

## BAGIAN A — Backend ke Hugging Face Spaces

### A1. Buat akun & Space
1. Daftar/masuk di https://huggingface.co
2. Klik **New** → **Space**.
3. Isi: Owner = akunmu, Space name = mis. `medical-chatbot-api`, License bebas,
   **SDK = Docker** (pilih "Blank"), Hardware = **CPU basic (free)**, Visibility = Public.
4. Create Space.

### A2. Siapkan isi Space (di komputer)
Space itu repo Git tersendiri. Isinya harus persis seperti ini:

```
medical-chatbot-api/        (repo Space)
├── Dockerfile              ← dari backend/Dockerfile
├── README.md               ← dari backend/SPACE_README.md (RENAME jadi README.md)
├── requirements.txt        ← dari backend/requirements.txt
├── app/                    ← dari backend/app/  (seluruh folder)
└── outputs/                ← artefak model (lihat daftar di A3)
```

### A3. File artefak yang DIUPLOAD ke `outputs/` (±565 MB)
Hanya file ini yang perlu (sisanya tidak dipakai saat runtime):
```
outputs/
├── metrics.json
├── disease_symptom_stats.json
├── dialog_index.csv                 (±50 MB)
├── tfidf_vectorizer.pkl
├── tfidf_matrix.npz                 (±12 MB)
├── best_checkpoint/
│   ├── config.json
│   └── model.safetensors            (±498 MB)  ← yang besar
└── roberta_finetuned/
    ├── config.json
    ├── label_mappings.json
    ├── tokenizer_config.json
    ├── vocab.json
    ├── merges.txt
    └── special_tokens_map.json
```
> `roberta_finetuned/model.safetensors` TIDAK perlu diupload (sudah dikecualikan
> dari kode) — menghemat ~500 MB.

### A4. Push ke Space (pakai Git + Git LFS)
```bash
# 1) clone repo Space (ganti URL sesuai Space-mu)
git clone https://huggingface.co/spaces/<user>/medical-chatbot-api
cd medical-chatbot-api

# 2) salin file (sesuaikan path sumbernya)
#    - Dockerfile, requirements.txt, app/ dari folder backend/
#    - SPACE_README.md  -> README.md
#    - outputs/ (file-file di A3) dari folder outputs/

# 3) Git LFS untuk file besar
git lfs install
git lfs track "*.safetensors" "*.csv" "*.npz" "*.pkl"
git add .gitattributes

# 4) commit & push  (upload ±565 MB — butuh waktu, sabar)
git add .
git commit -m "Deploy medical chatbot backend"
git push
```
Setelah push, buka halaman Space → tab **Logs**. Tunggu build & startup selesai
(beberapa menit; model dasar + translator akan terunduh sekali).

### A5. Cek backend hidup
Buka: `https://<user>-medical-chatbot-api.hf.space/health`
→ harus muncul `{"status":"ok","artifacts_loaded":true}`.
Catat URL ini, namanya kita sebut **URL_BACKEND**.

### A6. Buka CORS untuk domain Vercel (setelah punya URL Vercel di Bagian B)
Di Space → **Settings** → **Variables and secrets** → tambah Variable:
- Name: `CORS_ORIGINS`
- Value: `https://<nama-app-mu>.vercel.app` (URL frontend dari Bagian B)

Lalu **Restart** Space. (Sementara, sebelum punya URL Vercel, boleh diisi `*`.)

---

## BAGIAN B — Frontend ke Vercel

### B1. Buat akun
Daftar/masuk di https://vercel.com pakai akun GitHub.

### B2. Import project
1. **Add New** → **Project** → pilih repo `medicalchatbot_nlp`.
2. **Root Directory** → set ke `medical-chatbot-fe` (PENTING, karena Next.js ada di subfolder).
3. Framework otomatis terdeteksi **Next.js**.

### B3. Environment Variables (di halaman import, sebelum Deploy)
Tambahkan dua variable:
| Name | Value |
|---|---|
| `NEXT_PUBLIC_USE_MOCK` | `false` |
| `NEXT_PUBLIC_API_URL` | **URL_BACKEND** dari A5 (mis. `https://<user>-medical-chatbot-api.hf.space`) |

### B4. Deploy
Klik **Deploy**. Setelah selesai, dapat URL `https://<nama-app>.vercel.app`.

---

## BAGIAN C — Sambungkan & uji
1. Pastikan `CORS_ORIGINS` di Space (A6) sudah berisi URL Vercel, lalu restart Space.
2. Buka URL Vercel → coba kirim gejala. Kalau balasan muncul, **berhasil online!** 🎉

### Kalau error
- Balasan gagal / "tidak dapat terhubung" → cek `CORS_ORIGINS` (harus sama persis
  dengan URL Vercel, tanpa garis miring di akhir) dan pastikan `/health` backend `ok`.
- Backend lama merespons pertama kali → Space free "tidur" saat idle; request
  pertama membangunkannya (cold start, agak lama). Wajar.
