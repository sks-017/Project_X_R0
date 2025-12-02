# 🚀 System Startup Guide (Cold Start)

Since you have no terminals open, follow these steps to start the entire system from scratch.

You will need **3 separate Terminal windows**.

---

## 🖥️ Terminal 1: The API (Brain)
This handles data and security. It must run first.

1.  Open a new Terminal (PowerShell).
2.  Copy and paste this command:
    ```powershell
    cd C:\Users\91800\.gemini\antigravity\scratch\andon_system\ingress-api
    uvicorn app.main:app --reload --port 8000
    ```
3.  **Wait** until you see: `Uvicorn running on http://127.0.0.1:8000`

---

## 📊 Terminal 2: The Dashboard (UI)
This is what you see in the browser.

1.  Open a **SECOND** Terminal window.
2.  Copy and paste this command:
    ```powershell
    cd C:\Users\91800\.gemini\antigravity\scratch\andon_system\dashboard
    streamlit run Home.py
    ```
3.  Your browser should open automatically to `http://localhost:8501`.

---

## 📡 Terminal 3: The Gateway (Data)
This simulates machine data sending to the system.

1.  Open a **THIRD** Terminal window.
2.  Copy and paste this command:
    ```powershell
    cd C:\Users\91800\.gemini\antigravity\scratch\andon_system\edge
    python gateway.py
    ```
3.  You should see: `Sending telemetry for IMM-01...`

---

## 🔐 Log In
Now go to your browser (**http://localhost:8501**).

*   **Username:** `admin`
*   **Password:** `admin123`

You're in! 🚀
