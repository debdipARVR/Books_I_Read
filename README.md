# Books I Read

A Streamlit reading companion: visual shelf, daily plan, progress tracking, and analytics.

## Streamlit Community Cloud

- **Entrypoint:** `app.py` (repository root)
- **Branch:** `master`
- **Repo:** [debdipARVR/Books_I_Read](https://github.com/debdipARVR/Books_I_Read)

Deploy from [share.streamlit.io](https://share.streamlit.io): Create app → Yup, I have an app → repository `debdipARVR/Books_I_Read`, branch `master`, main file `app.py`.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Library data lives in `data/library.json`. Cover images in `uploads/covers/` are **Fernet-encrypted** (`.jpg.enc`). The app decrypts them in memory at runtime.

## Cover encryption

1. Put this in `.streamlit/secrets.toml` (local) and in **Streamlit Cloud → App settings → Secrets**:

```toml
FERNET_KEY = "paste-the-key-here"
```

2. Re-encrypt covers after adding plaintext files:

```bash
python encrypt_covers.py
```

Never commit `.streamlit/secrets.toml` or `.streamlit/fernet.key`.
