@echo off
echo ========================================
echo Installing Minimal Login App Dependencies
echo ========================================
echo.

echo Installing Python packages...
pip install Flask flask-login flask-session werkzeug python-dotenv psycopg2-binary supabase httpx cachelib

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create a .env file with DATABASE_URL and FLASK_SECRET_KEY
echo 2. Run: python web_app_minimal.py
echo.
pause
