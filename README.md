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

The site **asks for the Fernet key** before it decrypts any cover. Paste the key on the unlock screen. Covers stay encrypted on disk; decryption is in memory for that session only. Use **Lock shelf** in the sidebar to forget the key.

CLI helper (does not run in the browser):

```bash
python encrypt_covers.py
```
