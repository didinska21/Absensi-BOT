# Absensi-BOT Telegram

Bot ini digunakan untuk mencatat absensi (cek-in harian) pada daftar airdrop yang kamu ikuti, serta mengingatkan kamu secara otomatis dengan fitur reminder.

## Fitur

- Tambah / hapus airdrop.
- Daftar semua airdrop dan status cek-in harian.
- Statistik login selama seminggu terakhir.
- Reminder otomatis setiap 6 / 8 / 12 / 24 jam.
- Cek-in dan batal cek-in harian.

## Instalasi

1. Clone repository ini:

    ```bash
    git clone https://github.com/didinska21/Absensi-BOT.git
    cd Absensi-BOT
    ```

2. Buat virtual environment (opsional tapi disarankan):

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Buat file `.env` dan isi token dari BotFather:

    ```
    BOT_TOKEN=isi_token_anda_disini
    ```

5. Jalankan bot:

    ```bash
    python bot.py
    ```

## Struktur File

- `bot.py` → File utama bot Telegram.
- `absensi.db` → Database SQLite untuk menyimpan data airdrop dan absensi.
- `.env` → File environment untuk menyimpan token bot secara aman.
- `requirements.txt` → Daftar dependensi Python yang diperlukan.

## Perintah Awal

Ketik `/start` di chat bot untuk memulai.

## Catatan

- Reminder hanya aktif selama bot aktif (selama server tidak mati).
- Database `absensi.db` akan dibuat otomatis saat bot pertama kali dijalankan.
