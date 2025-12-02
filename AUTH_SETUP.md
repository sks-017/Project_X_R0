# Authentication Setup Guide

## 🔐 Overview
The Production Control System now supports secure User Authentication with Role-Based Access Control (RBAC).

**Features:**
- User Login/Logout
- JWT Token Authentication
- Password Hashing (Bcrypt)
- Roles: Admin, Manager, Operator

## ⚠️ Database Setup (Docker NOT Required)
Since Docker is not installed, the system has automatically switched to **SQLite** (`prodcontrol.db`) for immediate local persistence.

## 🚀 Setup Instructions

### 1. Create Admin User
We have already created the admin user for you!

**Credentials:**
- **Username:** `admin`
- **Password:** `admin123`

### 2. Restart the API
You MUST restart the API to pick up the new authentication system:

```powershell
# In the API terminal (Ctrl+C to stop, then run:)
uvicorn app.main:app --reload --port 8000
```

### 3. Login
1. Go to the Dashboard: http://localhost:8501
2. You will be redirected to the Login page.
3. Enter `admin` / `admin123`.
4. Success! You now have access to the full system.

### 3. Restart the API
If your API is already running, **restart it** so it connects to the database:

```powershell
# In the API terminal (Ctrl+C to stop, then run:)
uvicorn app.main:app --reload --port 8000
```

### 4. Login
1. Go to the Dashboard: http://localhost:8501
2. You will be redirected to the Login page.
3. Enter `admin` / `admin123`.
4. Success! You now have access to the full system.

## 👥 User Management (API)

You can create more users using the API (Swagger UI):
1. Go to http://localhost:8000/docs
2. Use the `/register` endpoint to create new users.
