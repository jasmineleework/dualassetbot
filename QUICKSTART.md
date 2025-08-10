# 🚀 Quick Start Guide

## Prerequisites
- Python 3.9+
- Node.js 14+
- Redis (optional, for caching)

## 🎯 Quick Start (Recommended)

### Option 1: Start Everything at Once
```bash
./start-all.sh
```
This will start both backend and frontend automatically.

### Option 2: Start Services Separately

#### Start Backend
```bash
./start-backend.sh
# OR manually:
cd src/main/python
python3 -m uvicorn api.main:app --port 8080
```

#### Start Frontend (in a new terminal)
```bash
./start-frontend.sh
# OR manually:
cd src/main/webapp
npm start
```

## 🌐 Access the Application

Once both services are running:
- **Frontend**: http://localhost:3010
- **Backend API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs

## ⚠️ Common Issues

### "Failed to fetch" Error
This usually means the backend is not running. Make sure:
1. Backend is running on port 8080
2. Check backend logs for any errors
3. Verify `.env` file has `REACT_APP_API_URL=http://localhost:8080`

### Port Already in Use
If port 8080 or 3010 is already in use:
- Backend: Change port in `src/main/python/core/config.py`
- Frontend: Change port in `src/main/webapp/.env`

### Missing Dependencies
- Python: `pip install -r src/main/python/requirements.txt`
- Node.js: `cd src/main/webapp && npm install`

## 📝 Configuration

### Backend Configuration
Edit `.env` in project root:
```env
API_PORT=8080
DATABASE_URL=sqlite:///./data/dual_asset_bot.db
BINANCE_USE_TESTNET=False
```

### Frontend Configuration
Edit `src/main/webapp/.env`:
```env
REACT_APP_API_URL=http://localhost:8080
PORT=3010
```

## 🔍 Health Check

Verify services are running:
```bash
# Check backend
curl http://localhost:8080/health

# Check frontend
curl http://localhost:3010
```

## 💡 Tips

1. **First Time Setup**: Run `./start-all.sh` which will install dependencies automatically
2. **Development**: Backend auto-reloads on file changes with `--reload` flag
3. **Logs**: Check terminal output for detailed error messages
4. **API Testing**: Visit http://localhost:8080/docs for interactive API documentation

## 🆘 Need Help?

If you encounter issues:
1. Check both backend and frontend terminal logs
2. Ensure all ports are correct (8080 for backend, 3010 for frontend)
3. Verify your `.env` files are configured correctly
4. Try restarting both services