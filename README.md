# Portfolio Tracker

FastAPI + React/Vite dashboard for Fidelity portfolio management.

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
DATA_DIR=./data uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend dev server proxies `/api` to `localhost:8000`.

## Deploy to Railway

1. Push to GitHub
2. Create Railway project → deploy from repo
3. Set root directory to `backend`
4. Add a Railway Volume mounted at `/data`
5. Set environment variable: `DATA_DIR=/data`

## Build & Deploy Workflow (same as Market Pulse)

```bash
cd frontend
npm run build          # outputs to backend/static
cd ..
git add -A
git commit -m "your message"
git push
```

## Data Sources

- **Positions**: Export from Fidelity → Accounts → Portfolio Positions → Download CSV
- **History**: Export from Fidelity → Accounts → Account History → Download CSV
  - Run multiple 90-day periods to get full history
  - Upload all CSVs at once — app merges and deduplicates automatically

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Path for persistent history storage (Railway volume) |
| `PORT` | `8000` | Server port (set automatically by Railway) |
