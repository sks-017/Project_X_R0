# Quick Start Guide - Database Setup

## Option 1: Local PostgreSQL (Recommended for Development)

### Step 1: Install PostgreSQL
**Windows:**
1. Download from: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set for `postgres` user

**Mac:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Step 2: Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create user and database
CREATE USER prodcontrol WITH PASSWORD 'prodcontrol123';
CREATE DATABASE prodcontrol OWNER prodcontrol;
\c prodcontrol
CREATE EXTENSION IF NOT EXISTS timescaledb;
\q

# Run initialization script
psql -U prodcontrol -d prodcontrol -f database/init.sql
```

### Step 3: Configure .env
```bash
# Copy example file
cp .env.example .env

# Edit .env (use any text editor)
DATABASE_URL=postgresql://prodcontrol:prodcontrol123@localhost:5432/prodcontrol
```

### Step 4: Test Connection
```bash
cd ingress-api
python -c "from app.database import check_db_connection; print(check_db_connection())"
```

---

## Option 2: Docker Compose (Easiest - Production Ready)

### Step 1: Install Docker Desktop
- Windows/Mac: https://www.docker.com/products/docker-desktop/
- Linux: `sudo apt install docker.io docker-compose`

### Step 2: Start Everything
```bash
# From project root
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 3: Access Services
- **Database:** localhost:5432
- **API:** http://localhost:8000
- **Dashboard:** http://localhost:8501

### Step 4: Stop Everything
```bash
docker-compose down
```

---

## Verify Installation

### Check Database Tables
```bash
psql -U prodcontrol -d prodcontrol
\dt
```

You should see:
```
 equipment
 telemetry
 users
 alerts
 audit_log
```

### Check Default Data
```sql
SELECT * FROM equipment;
SELECT * FROM users;
```

### Test API Health
```bash
curl http://localhost:8000/health
```

---

## Default Credentials
**Admin User:**
- Username: `admin`
- Password: `admin123`
- ⚠️ **CHANGE THIS IN PRODUCTION!**

---

## Troubleshooting

### PostgreSQL won't start
```bash
# Check if already running
sudo systemctl status postgresql

# Restart
sudo systemctl restart postgresql
```

### Cannot connect
```bash
# Check PostgreSQL is listening
sudo netstat -plntu | grep 5432

# Edit pg_hba.conf to allow local connections
# Location: /etc/postgresql/14/main/pg_hba.conf
# Add: host all all 127.0.0.1/32 md5
```

### Docker issues
```bash
# Stop all containers
docker-compose down -v

# Remove volumes and start fresh
docker volume rm andon_system_postgres_data
docker-compose up -d
```

---

## Next Steps
1. ✅ Database is running
2. Start the API: `cd ingress-api && uvicorn app.main:app --reload`
3. Start the gateway: `cd edge && python gateway.py`
4. Start the dashboard: `cd dashboard && streamlit run Home.py`
