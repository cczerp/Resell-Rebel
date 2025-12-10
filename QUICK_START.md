# Quick Start - Minimal Login App

## Windows Setup

### Step 1: Install Dependencies

**Option A - Using batch file:**
```cmd
setup_minimal.bat
```

**Option B - Manual install:**
```cmd
pip install Flask flask-login flask-session werkzeug python-dotenv psycopg2-binary supabase httpx cachelib
```

### Step 2: Create `.env` File

Create a file named `.env` in the `resell-rebel` folder with this content:

```env
# Required - Your PostgreSQL database
DATABASE_URL=postgresql://username:password@host:5432/database_name

# Required - Secret key for sessions (change this to a random string)
FLASK_SECRET_KEY=change-this-to-something-random-and-secure

# Optional - For Google OAuth (leave blank to skip Google login)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_REDIRECT_URL=http://localhost:5000/auth/callback
```

**⚠️ IMPORTANT:** You must set a real PostgreSQL DATABASE_URL or the app won't start!

**Don't have PostgreSQL?**
- Install locally: https://www.postgresql.org/download/windows/
- OR use a free cloud database: https://supabase.com (includes PostgreSQL)

### Step 3: Run the App

```cmd
python web_app_minimal.py
```

The app will start on http://localhost:5000

## Linux/Mac Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements-minimal.txt
```

### Step 2: Create `.env` File
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### Step 3: Run the App
```bash
python3 web_app_minimal.py
```

## Testing Login

1. **Open browser:** http://localhost:5000
2. **Register a new account:**
   - Click "Register"
   - Enter username, email, password
   - You'll be logged in automatically
3. **Test logout/login:**
   - Click "Logout"
   - Click "Login"
   - Enter your credentials

## Common Errors

### ❌ "ModuleNotFoundError: No module named 'flask_session'"
**Fix:** Run `pip install flask-session` or `setup_minimal.bat`

### ❌ "DATABASE_URL environment variable is required"
**Fix:** Create `.env` file with DATABASE_URL pointing to PostgreSQL database

### ❌ "ModuleNotFoundError: No module named 'psycopg2'"
**Fix:** Run `pip install psycopg2-binary`

### ❌ "could not connect to server"
**Fix:** Check your DATABASE_URL is correct and PostgreSQL is running

## Debug Endpoints

- http://localhost:5000/debug-config - Shows configuration
- http://localhost:5000/protected - Tests if login is working

## What's Working vs Not Working

Once you run the app, tell me:
1. ✅ Does the app start without errors?
2. ✅ Can you register a new account?
3. ✅ Can you login with username/password?
4. ✅ Does the session persist after page refresh?
5. ✅ Does Google OAuth work (if configured)?

This will help identify exactly what's broken!
