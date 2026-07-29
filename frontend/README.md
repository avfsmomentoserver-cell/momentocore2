# Frontend Documentation

## MomentoCore Dashboard

A real-time Next.js dashboard for monitoring trading signals and interacting with AI agents.

### Features

- **Real-Time Signal Monitoring**: WebSocket connection to view live signals
- **Market Status Indicator**: Visual feedback on market conditions (Hot/Warm/Cold)
- **Interactive Charts**: Multiplier and confidence trends using Recharts
- **Signal History**: Recent signals with color-coded cards
- **Agent Integration**: Chat interface for AI agent queries

### Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Real-Time**: WebSocket

### Getting Started

```bash
cd frontend
npm install
npm run dev
```

Access at `http://localhost:3000`

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8765
```

### Component Structure

```
frontend/
├── app/
│   ├── page.tsx          # Main dashboard
│   └── globals.css       # Global styles
├── components/           # Reusable UI components
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

### API Integration

The dashboard connects to:
- **REST API**: `http://localhost:8000/api/v1/` (proxied via next.config.js)
- **WebSocket**: `ws://localhost:8765` (real-time signals)

### Deployment

Build for production:

```bash
npm run build
npm start
```

Docker deployment is handled via the root `docker-compose.yml`.
