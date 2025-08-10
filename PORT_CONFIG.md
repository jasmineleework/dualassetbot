# Port Configuration

This document defines the standard ports used by the Dual Asset Bot application.

## Standard Ports

| Service | Port | Description |
|---------|------|-------------|
| **Backend API** | `8000` | FastAPI backend server |
| **Frontend Dev** | `3010` | React development server |
| **Frontend Prod** | `3000` | React production build |
| **Redis** | `6379` | Redis cache server (default) |
| **PostgreSQL** | `5432` | PostgreSQL database (default) |

## Environment Configuration

### Backend (.env)
```bash
# API Server Port
API_PORT=8000
```

### Frontend (.env)
```bash
# Backend API URL
REACT_APP_API_URL=http://localhost:8000
# Frontend Dev Server Port
PORT=3010
```

## Starting Services

### Backend
```bash
cd src/main/python
uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd src/main/webapp
npm start  # Will use port 3010 from .env
```

## Important Notes

1. **Always use port 8000 for backend API** - This is the standard port for the FastAPI server
2. **Frontend connects to backend on port 8000** - All API calls should go to `http://localhost:8000`
3. **Frontend dev server runs on port 3010** - To avoid conflicts with other React apps
4. **Never hardcode ports in code** - Always use environment variables

## Troubleshooting

### Port Already in Use
If you see "Port already in use" error:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Connection Refused
If frontend shows "Failed to fetch":
1. Check backend is running on port 8000
2. Check REACT_APP_API_URL is set to `http://localhost:8000`
3. Verify CORS is configured for frontend port (3010)

## Docker Configuration (Future)

When running in Docker:
- Backend: `8000` (mapped to host)
- Frontend: `80` (mapped to host 3010)
- Redis: `6379` (internal only)
- PostgreSQL: `5432` (internal only)