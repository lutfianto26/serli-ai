# SERLI-AI Prototype v1

Prototype Streamlit chatbot AI-SRL untuk membantu siswa SMP memahami konsep fungsi melalui **Plan → Learn → Reflect**, berdasarkan fase SRL Zimmerman.

## Menjalankan lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```

Tanpa API key, aplikasi tetap berjalan dalam **mode prototipe lokal** (respons berbasis aturan sederhana). Agar menggunakan LLM, buat `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "YOUR_KEY"
OPENAI_MODEL = "gpt-4o-mini"
```

> Jangan unggah API key ke GitHub.

## Data
Prototype menyimpan data di SQLite `serli_ai.db` saat aplikasi berjalan: sesi, chat, fase/proses SRL, level scaffolding, topik, timestamp, dan refleksi.

## Catatan v1
- Mathematics anxiety tidak masuk ke chatbot; digunakan di luar sistem untuk klasifikasi subjek.
- Klasifikasi SRL otomatis pada v1 masih rule-based dan harus diperlakukan sebagai anotasi sistem, bukan hasil coding penelitian final.
- Untuk deployment penelitian multi-user, database sebaiknya dipindahkan ke PostgreSQL/Supabase agar persisten.
