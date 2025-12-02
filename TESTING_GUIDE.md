# 🧪 Beginner's Testing Guide: Authentication

Follow these steps exactly to test your new secure login system.

## Step 1: Restart the API (The "Brain")
We need to restart the API so it loads the new security rules.

1.  Find the **Terminal** window where the API is running (it usually says `Uvicorn running...`).
2.  Click inside that window and press **`Ctrl` + `C`** on your keyboard to stop it.
3.  Type this command and press **Enter**:
    ```powershell
    cd C:\Users\91800\.gemini\antigravity\scratch\andon_system\ingress-api
    uvicorn app.main:app --reload --port 8000
    ```
4.  Wait until you see: `[OK] Database initialized` and `Uvicorn running on http://127.0.0.1:8000`.

## Step 2: Open the Dashboard
1.  Open your web browser (Chrome, Edge, etc.).
2.  Go to this address: **[http://localhost:8501](http://localhost:8501)**
3.  **Refresh the page** (F5) to make sure you have the latest version.

## Step 3: Log In
You should now see a **Login Screen** instead of the dashboard.

1.  **Username:** `admin`
2.  **Password:** `admin123`
3.  Click the **"Sign In"** button.

## Step 4: Verify It Works
1.  **Success:** You should be taken to the "Welcome" page.
2.  **Check Sidebar:** Look at the left sidebar. You should see:
    *   👤 **admin**
    *   Role: **admin**
    *   A **"Sign Out"** button.

## Step 5: Test Security (The "Bouncer" Test)
1.  Click the **"Sign Out"** button in the sidebar.
2.  You will be sent back to the Login screen.
3.  Now, try to "sneak in" by clicking **"Executive Summary"** in the sidebar.
4.  **Result:** It should block you and say "Please login from the Home page first." or redirect you to login.

## Troubleshooting
*   **"Connection refused"**: Your API (Step 1) is not running. Check the terminal.
*   **"Invalid username"**: Check that you typed `admin` (lowercase) and `admin123`.
*   **Database error**: Make sure you are using the SQLite setup we configured (it happens automatically).

🎉 **If you can log in and log out, you have successfully built a secure, production-ready system!**
