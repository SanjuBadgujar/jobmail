# JobMail – Smart Job Application Email Sender

Sends one separate email per recruiter from your own Gmail (official Gmail API, OAuth 2.0, `gmail.send`).

## 1. Google Cloud setup
1. Create a project at https://console.cloud.google.com and enable the **Gmail API**.
2. OAuth consent screen: External, add yourself under **Test users**.
3. Credentials: **OAuth client ID** (Web application). Authorized redirect URI:
   `http://localhost:8000/api/auth/google/callback`
4. Copy the client ID and secret into `.env`.

## 2. Configure
```powershell
copy .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # paste into TOKEN_ENCRYPTION_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"                                   # paste into SECRET_KEY
```

## 3. Run (Windows PowerShell)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
New window:
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173, click **Connect Gmail**. If you used an older version, delete `backend\jobmail.db` once (new columns).

## Tests
`cd backend; pytest` (Gmail is mocked; no real emails are sent).

## Production notes
Set `APP_ENV=production`, a PostgreSQL `DATABASE_URL`, HTTPS URLs for `FRONTEND_URL`, `CORS_ORIGINS` and `GOOGLE_REDIRECT_URI` (also add that URI in Google Cloud), run `uvicorn app.main:app` behind a reverse proxy, and serve `frontend/dist` (`npm run build`) from the same domain.
