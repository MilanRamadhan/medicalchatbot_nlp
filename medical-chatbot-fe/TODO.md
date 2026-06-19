# Rencana Penyempurnaan Frontend

Catatan UI/UX yang **disepakati tapi belum dikerjakan** (status: planned).
Ditambahkan 2026-06-19. Ranah frontend (`medical-chatbot-fe/`). Untuk bug
logika chatbot lihat `../backend/CHATBOT_ISSUES.md`.

---

## E1 — Ganti panel metrik jadi daftar 30 penyakit (metrik dibuat collapsible)

**Apa:** Kartu "Performa Model — RoBERTa" (akurasi 86.7% vs base 3.6%) saat ini
jadi tampilan utama. Ubah supaya yang utama adalah **daftar 30 penyakit** yang
bisa diklasifikasi chatbot. Metrik akurasi **tetap ada** tapi disembunyikan di
balik toggle/`<details>` "Lihat performa model".

**Kenapa:** Pengguna perlu tahu batas kemampuan chatbot — hanya 30 penyakit ini
— supaya tidak salah harap. Bar akurasi sifatnya akademis/dev-facing, bukan
yang dicari user. (Keputusan: tetap simpan metrik dalam bentuk collapse karena
di PRD §5.2 perbandingan base vs fine-tuned adalah komponen wajib.)

**Catatan implementasi:**
- 30 nama penyakit ada di `outputs/roberta_finetuned/label_mappings.json`
  (`labels_list`): Allergy, Anemia, Anxiety, Arthritis, Asthma, Bronchitis,
  COVID-19, Chronic Kidney Disease, Common Cold, Dementia, Depression,
  Dermatitis, Diabetes, Epilepsy, Food Poisoning, Gastritis, Heart Disease,
  Hypertension, IBS, Influenza, Liver Disease, Migraine, Obesity, Parkinson's,
  Pneumonia, Sinusitis, Stroke, Thyroid Disorder, Tuberculosis, Ulcer.
- **Idealnya backend expose daftar ini** (mis. tambah `diseases:
  artifacts.labels_list` ke response `/metrics`, atau endpoint `GET /diseases`)
  supaya FE selalu sinkron. Sementara backend belum, boleh hardcode 30 nama di
  FE sebagai konstanta.
- Edit `components/ModelMetrics.tsx`: render penyakit sebagai grid chip/tag
  kecil (teal, rapi). Bungkus bar metrik dalam toggle (state `useState` atau
  `<details><summary>Lihat performa model</summary>…</details>`).
- Nama penyakit biarkan bahasa Inggris (konsisten dengan output chatbot, mis.
  "Heart Disease"). Opsional: tambah terjemahan ID kecil di tooltip.
- Jaga tinggi panel tetap ringkas (lihat E2 — frame harus muat 1 layar).

## E2 — Layout chat: tinggi tetap 1 layar, hanya area chat yang scroll

**Apa:** Sekarang saat chat makin panjang, **seluruh halaman ikut memanjang ke
bawah** dan yang discroll halaman penuh. Ubah jadi pola "app shell": tinggi
aplikasi **terkunci setinggi layar**; header + panel penyakit + kontrol +
input **diam**, dan **hanya daftar pesan (ChatWindow) yang scroll** ke dalam.

**Kenapa:** Biar berperilaku seperti aplikasi chat normal (frame tetap, scroll
internal), bukan dokumen yang memanjang.

**Catatan implementasi (file & titik perubahan):**
- `app/page.tsx`: `<main>` sekarang `min-h-screen ... flex-col gap-5`. Ubah jadi
  tinggi terkunci: `h-screen` / `h-[100dvh]` + `overflow-hidden`.
- Section chat sekarang `min-h-[58vh] flex-1 ... overflow-hidden`. Kuncinya:
  beri **`min-h-0`** pada section flex-child ini (`flex-1 min-h-0`) supaya anak
  flexbox boleh menyusut dan memunculkan scroll internal. Tanpa `min-h-0`,
  konten malah mendorong tinggi parent (inilah penyebab halaman memanjang).
- `components/ChatWindow.tsx` sudah `flex-1 overflow-y-auto` — itu yang akan
  jadi satu-satunya area scroll begitu parent-nya tingginya terkunci.
- Pertimbangkan: kalau header + panel 30 penyakit + input terlalu tinggi untuk
  1 layar di laptop kecil, bikin panel penyakit compact (chip rapat) atau
  header sedikit dirampingkan.
- Tes di tinggi viewport kecil (mis. 700px) dan pakai `100dvh` biar aman di
  mobile (address bar).

---

### Status
| ID | Penyempurnaan | Sisi | Status |
|----|---------------|------|--------|
| E1 | Panel 30 penyakit + metrik collapsible | Frontend | ✅ Done (2026-06-19) |
| E2 | Chat fixed-height, scroll internal | Frontend | ✅ Done (2026-06-19) |

**Implementasi E1+E2 (sudah dikerjakan):**
- `lib/diseases.ts` — daftar 30 penyakit (en + gloss id).
- `components/ModelMetrics.tsx` — judul "Bisa mendeteksi 30 penyakit", chip
  penyakit dalam kotak `max-h-[4.75rem]` yang scroll internal; bar metrik
  base-vs-finetuned di balik toggle `Lihat performa model`.
- `app/page.tsx` — `<main>` `h-[100dvh] overflow-hidden`; chat section
  `flex-1 min-h-0`. `components/ChatWindow.tsx` scroller `min-h-0 flex-1`.
  QuickPrompts dipindah ke dalam empty-state ChatWindow (bukan bar terpisah)
  supaya welcome dapat tinggi penuh. Header/ModelMetrics `shrink-0`.
- Verifikasi: page tidak scroll (hanya area chat), auto-scroll ke bawah jalan,
  30 chip tampil, toggle metrik berfungsi, 0 error console.
