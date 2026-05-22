# Frontend — Sales and analytics agent

Next.js 14 chat UI. Talks only to local FastAPI (`NEXT_PUBLIC_API_BASE_URL`).

## Run

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000/chat

If the API runs on port 8001:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```
