# Production Control System - Quick Start

## 🚀 Start Without Database (Simple)

```bash
# Terminal 1: Start API
cd ingress-api
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Gateway (data simulator)
cd edge
python gateway.py

# Terminal 3: Start Dashboard
cd dashboard
streamlit run Home.py
```

Access dashboard: http://localhost:8501

---

## 🗄️ Start With Database (Production Mode)

### Option 1: Docker (Easiest - All-in-One)

```bash
# Make sure Docker Desktop is running
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Access:
# - Dashboard: http://localhost:8501
# - API: http://localhost:8000
# - Database: localhost:5432
```

### Option 2: Local PostgreSQL

#### Step 1: Install PostgreSQL
- Windows: https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql@14`
- Linux: `sudo apt install postgresql`

#### Step 2: Create Database
```bash
# Windows (PowerShell)
psql -U postgres
CREATE USER prodcontrol WITH PASSWORD 'prodcontrol123';
CREATE DATABASE prodcontrol OWNER prodcontrol;
\q

# Run initialization
cd database
psql -U prodcontrol -d prodcontrol -f init.sql
```

#### Step 3: Configure Environment
```bash
# Copy template
copy .env.example .env

# Edit .env file
DATABASE_URL=postgresql://prodcontrol:prodcontrol123@localhost:5432/prodcontrol
```

#### Step 4: Install Dependencies
```bash
cd ingress-api
pip install -r requirements.txt
pip install sqlalchemy psycopg2-binary python-dotenv
```

#### Step 5: Start Services
```bash
# Terminal 1: API
cd ingress-api
uvicorn app.main:app --reload

# Terminal 2: Gateway
cd edge
python gateway.py

# Terminal 3: Dashboard
cd dashboard
streamlit run Home.py
```

---

## ✅ Verify Installation

### Check API Health
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "api": "up"
}
```

### Check Equipment List
```bash
curl http://localhost:8000/api/v1/equipment
```

### Check Telemetry
```bash
curl http://localhost:8000/api/v1/telemetry/latest
```

### View Historical Data
```bash
curl http://localhost:8000/api/v1/telemetry/history/IMM-01?hours=24
```

---

## 🛠️ Troubleshooting

### API won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F
```

### Database connection fails
```bash
# Check PostgreSQL is running
# Windows: Services → PostgreSQL
# Linux: sudo systemctl status postgresql

# Test connection
psql -U prodcontrol -d prodcontrol

# If "role does not exist"
psql -U postgres
CREATE USER prodcontrol WITH PASSWORD 'prodcontrol123';
CREATE DATABASE prodcontrol OWNER prodcontrol;
```

### Docker issues
```bash
# Stop and remove
docker-compose down -v

# Rebuild
docker-compose build --no-cache

# Start again
docker-compose up -d
```

---

## 📊 What's Different With Database?

**Before (In-Memory):**
- ❌ Data lost on restart
- ❌ No historical trends
- ❌ Limited to ~100MB RAM

**After (PostgreSQL):**
- ✅ Data persists forever
- ✅ Historical analysis (24 hours, 7 days, 6 months)
- ✅ Scales to millions of records
- ✅ Production-ready
- ✅ Automatic fallback if DB down

---

## 🎯 Next Steps

1. **Try it out:** Run with Docker or local PostgreSQL
2. **Check dashboard:** See data persisting across restarts
3. **Query history:** Use new `/history` endpoint
4. **Add authentication:** Next phase (user login)
5. **Deploy to customer:** You're production-ready!

---

## 📝 Default Credentials

**Database:**
- User: `prodcontrol`
- Password: `prodcontrol123`
- Database: `prodcontrol`

**Admin User (future):**
- Username: `admin`
- Password: `admin123`
- ⚠️ **CHANGE IN PRODUCTION!**
