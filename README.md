# 🤖 Job Application Automation & AI Career Co-Pilot

Sistem otomasi pelamar kerja cerdas (*Autonomous AI Job Applicant & Tracking Ecosystem*) berbasis Python, Google Gemini, Playwright, dan Telegram Bot. Sistem ini mengintegrasikan jalur pelamaran hybrid (Cold Email HRD + Job Portal), screening kecocokan kualifikasi otomatis (skor ATS >= 75%), sinkronisasi real-time ke Google Sheets, anti-scam filter, hingga remote control penuh dari HP via Telegram.

---

## 🚀 Fitur Unggulan

### 1. 📱 100% Mobile Control via Telegram (Tanpa Buka Laptop)
- **Tombol Interaktif (Inline Keyboard)**: Kirim lamaran, sesuaikan CV, dan buat panduan interview langsung dengan satu ketukan tombol di Telegram.
- **Kirim Lamaran Instan (`/apply`)**: Cukup ketik email, PT, dan posisi. AI otomatis membuatkan Cover Letter dan memunculkan tombol konfirmasi kirim di HP.
- **Auto-Apply Portal dari HP (`/portal`)**: Menjalankan bot browser LinkedIn, Glints, atau Jobstreet langsung lewat perintah Telegram.
- **Berburu Loker HRD (`/hunt`)**: Menjelajahi internet untuk mencari posting loker baru dan menyajikan kartu peluang lengkap dengan tombol `[Kirim Lamaran]`.
- **Download Backup (`/backup`)**: Ekspor seluruh database pelamaran dalam format CSV langsung ke chat Telegram Anda.

### 2. 🧠 AI Screening & Deep Qualification Matcher (Google Gemini)
- **Threshold Ketat (>= 75%)**: Hanya melamar lowongan yang benar-benar relevan dengan profil kandidat untuk menghindari spam dan menjaga reputasi akun.
- **Dynamic AI Form Answerer**: Menjawab pertanyaan screening formulir (pengalaman kerja, otorisasi kerja, opsi dropdown/radio) secara otomatis berdasarkan profil CV Anda.
- **Dukungan Dual CV (ID & EN)**: Mendeteksi bahasa pengantar lowongan secara otomatis untuk memilih CV Bahasa Indonesia atau English.

### 3. 🛡️ Keamanan & Anti-Scam Guard
- **Deteksi Loker Bodong / Penipuan**: Secara otomatis menyaring modus travel reimbursement fiktif, biaya registrasi/seragam, dan pencatutan nama BUMN yang memakai email gratisan (`@gmail.com`).
- **Anti-Duplicate Filter**: Mencegah pengiriman lamaran berulang ke perusahaan atau email HRD yang sama.
- **Daily Quota Safety Guard**: Membatasi maksimal 15 lamaran/hari untuk menjaga kesehatan akun dan menghindari spam blacklist.
- **Smart Rate Limiter**: Jeda acak manusia (*human jitter* 3–7 menit) antar-email untuk melindungi domain/reputasi email pengirim.

### 4. 📄 Dokumen Lamaran & Desain Email Berstandar Korporat
- **Professional HTML Email Template**: Format email elegan beraksen navy dengan tipografi modern, highlight kartu kualifikasi, dan tautan portofolio/LinkedIn yang ramah perangkat mobile.
- **Dual-Mode MIME Delivery**: Mengirimkan versi teks polos sekaligus HTML kaya (lolos filter spam email korporat).
- **Generator Dokumen PDF Resmi**:
  - `Surat_Lamaran_<Company>.pdf`: Surat lamaran formal A4 lengkap dengan kop surat dan perihal.
  - `CV_Tailored_<Company>.pdf`: Resume yang di-tailor otomatis dengan menyisipkan *exact keywords* ATS lowongan target.

### 5. 📊 Real-Time Tracker, Analytics, & Auto Follow-Up
- **Sinkronisasi Google Sheets / CSV**: Catat otomatis setiap lamaran (`Applied`, `On Progress`, `Rejected`, `Offering`) lengkap dengan diagram donat di `Sheet2`.
- **Analytics & Win Rate Dashboard**: Menghitung *HR Response Rate*, *Apply-to-Interview Rate*, dan performa per channel.
- **Auto Follow-Up Email**: Mendeteksi lamaran menggantung (> 5 hari kerja) dan menyusun draf email tindak lanjut yang sopan via AI.
- **Autonomous Background Scheduler**: Pemindaian inbox otomatis berkala tiap 2 jam dan ringkasan pagi (*morning briefing*) ke Telegram.
- **Windows Startup Auto-Start**: Bot otomatis aktif di latar belakang saat laptop dinyalakan tanpa jendela terminal.

---

## 📂 Struktur Direktori Proyek

```text
automation-job/
├── .env.example                  # Template kredensial & konfigurasi aman
├── .gitignore                     # Proteksi data pribadi & credentials dari Git
├── requirements.txt              # Daftar dependensi pustaka Python
├── run_bot.bat                   # Launcher bot terminal
├── run_bot_silent.vbs            # Silent background launcher (tanpa jendela CMD)
├── CV_MUHAMMAD BAGJA SATRIO.pdf  # File CV Bahasa Indonesia (Lokal)
├── CV_MUHAMMAD_BAGJA_SATRIO_EN.pdf # File CV English (Lokal)
├── src/
│   ├── main.py                   # Terminal CLI Menu Orchestrator
│   ├── models.py                 # Skema data Pydantic
│   ├── sheets.py                 # Sinkronisasi Google Sheets API / Webhook / Local CSV
│   ├── mailer.py                 # Email dispatcher (SMTP) & inbox scanner (IMAP)
│   ├── classifier.py             # Klasifikasi balasan HRD (Interview, Reject, Offer)
│   ├── cv_selector.py            # Pemilihan CV dinamis & deteksi bahasa
│   ├── ai_assistant.py           # Engine Gemini (Cover Letter & Screening Form)
│   ├── analytics.py              # Perhitungan metrik konversi & dashboard
│   ├── follow_up.py              # Detektor lamaran menggantung (> 5 hari)
│   ├── backup.py                 # Ekspor arsip database CSV bertanda waktu
│   ├── startup.py                # Pemasang Windows Startup otomatis
│   ├── scheduler.py              # Background daemon thread scheduler berkala
│   ├── interview/
│   │   └── prep_kit.py           # Generator panduan wawancara AI
│   ├── matcher/
│   │   └── ai_matcher.py         # Evaluator skor kecocokan kualifikasi ATS
│   ├── notifier/
│   │   ├── telegram.py           # Klien Telegram Push Notification & Inline Buttons
│   │   └── telegram_bot.py       # Two-Way Interactive Remote Control Bot
│   ├── portals/
│   │   ├── base.py               # Playwright persistent context browser
│   │   ├── linkedin.py           # Bot LinkedIn Easy Apply
│   │   ├── glints.py             # Bot Glints Lamar Cepat
│   │   └── jobstreet.py          # Bot Jobstreet Auto Apply
│   ├── scraper/
│   │   ├── email_extractor.py    # Ekstraktor email HRD & filter domain
│   │   └── hr_leads_scraper.py   # Web scraper loker & leads hunting
│   ├── security/
│   │   ├── scam_detector.py      # Filter deteksi penipuan/loker bodong
│   │   └── rate_limiter.py       # Cooldown dinamis pelindung reputasi email
│   ├── tailor/
│   │   ├── cover_letter_pdf.py   # Generator PDF Surat Lamaran Resmi
│   │   └── resume_tailor.py      # Generator PDF CV Tailored ATS Keywords
│   └── templates/
│       └── email_styler.py       # Desain template email HTML modern
└── tests/                        # 53 Unit Tests (Pytest Suite)
```

---

## 🛠️ Panduan Instalasi & Pengaturan

### 1. Prasyarat Sistem
- **Python 3.11+** terpasang di komputer.
- Git & Browser Chromium (otomatis diunduh via Playwright).

### 2. Kloning & Pemasangan Dependensi
```bash
git clone https://github.com/<username>/<repo-name>.git
cd <repo-name>

# Buat virtual environment
python -m venv .venv

# Aktivasi virtual environment (Windows PowerShell)
.venv\Scripts\activate

# Install pustaka
pip install -r requirements.txt

# Unduh browser Playwright
playwright install chromium
```

### 3. Konfigurasi File Lingkungan (`.env`)
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
Buka file `.env` dan lengkapi variabel berikut:
```env
# 1. Kredensial Email (Gunakan Google App Password 16 huruf)
EMAIL_USER=email.anda@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com

# 2. Google Sheets Webhook (URL Apps Script)
GOOGLE_WEBHOOK_URL="https://script.google.com/macros/s/YOUR_APPS_SCRIPT_DEPLOYMENT_ID/exec"

# 3. Google AI Studio API Key (Gemini)
GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere"

# 4. Kredensial Telegram Bot
TELEGRAM_BOT_TOKEN="123456789:AAFJ_YourTelegramBotToken"
TELEGRAM_CHAT_ID="123456789"

# 5. Path CV Lokal (Taruh file PDF Anda di root folder)
CV_ID_PATH="CV_Kandidat.pdf"
CV_EN_PATH="CV_Candidate_EN.pdf"
```

---

## 📱 Panduan Perintah Telegram (Mobile Remote)

Cukup buka chat dengan bot Telegram Anda dan gunakan perintah berikut:

| Perintah | Deskripsi |
|---|---|
| `/help` | Menampilkan panduan seluruh menu perintah |
| `/status` | Ringkasan metrik analitik, total lamaran, dan rasio konversi wawancara |
| `/recent` | Menampilkan 5 lamaran kerja terakhir beserta statusnya |
| `/scan` | Memindai inbox Gmail sekarang untuk mencari balasan HRD terbaru |
| `/followup` | Mengecek daftar lamaran yang menggantung lebih dari 5 hari kerja |
| `/portal` | Memunculkan tombol pilihan auto-apply LinkedIn, Glints, atau Jobstreet |
| `/hunt [posisi]` | Menjelajahi internet mencari lowongan HRD aktif + tombol apply instan |
| `/apply <email> \| <pt> \| <posisi>` | Menyusun lamaran dan memunculkan tombol kirim/tailor di chat |
| `/prep <nama_pt>` | Menyusun panduan latihan wawancara AI lengkap untuk perusahaan target |
| `/backup` | Mengirimkan file dokumen arsip database lamaran (.csv) ke Telegram |

---

## 💻 Penggunaan Lewat Terminal Lokal (Opsional)

Jika ingin menjalankan antarmuka menu CLI di terminal:
```bash
python src/main.py
```
Menu interaktif yang tersedia:
1. **Kirim Cold Email Lamaran** (Review draft, opsi tailor CV, opsi PDF cover letter)
2. **Jalankan Auto-Apply Portal** (LinkedIn / Glints / Jobstreet)
3. **Scan Respon Email & Update Status Sheets**
4. **Lihat Rekap Status Lamaran & Analytics Dashboard**
5. **Web Scraper Email HRD di Internet + AI Matcher**
6. **Auto Follow-Up Lamaran Menggantung (> 5 Hari)**
7. **Jalankan Telegram Bot Remote Control (Listener HP)**

---

## 🧪 Menjalankan Pengujian (Testing Suite)

Seluruh komponen dilengkapi pengujian unit komprehensif (TDD):
```bash
pytest tests/ -v
```
*Hasil: 53 Unit Tests passed (100% verified).*

---

## 🔒 Privasi & Keamanan Data
- Seluruh kredensial sensitif, file PDF CV asli, database kontak HRD, serta riwayat pelamaran dilindungi di `.gitignore` dan **tidak akan pernah terunggah ke repositori publik**.
- Repositori ini aman dibagikan sebagai portofolio open-source tanpa membocorkan data pribadi pengembang.
