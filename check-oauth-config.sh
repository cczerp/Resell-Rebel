#!/bin/bash
# Google OAuth Configuration Checker
# Run this to verify your Supabase OAuth setup

echo "🔍 Google OAuth Configuration Checker"
echo "======================================"
echo ""

# Check environment variables
echo "📋 Checking Environment Variables..."
echo ""

if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL is NOT set"
    MISSING=1
else
    echo "✅ SUPABASE_URL is set: $SUPABASE_URL"
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ SUPABASE_ANON_KEY is NOT set"
    MISSING=1
else
    echo "✅ SUPABASE_ANON_KEY is set: ${SUPABASE_ANON_KEY:0:20}..."
fi

if [ -z "$RENDER_EXTERNAL_URL" ]; then
    echo "⚠️  RENDER_EXTERNAL_URL not set (will use current request URL)"
else
    echo "✅ RENDER_EXTERNAL_URL is set: $RENDER_EXTERNAL_URL"
    REDIRECT_URL="$RENDER_EXTERNAL_URL/auth/callback"
fi

echo ""
echo "======================================"
echo ""

if [ -n "$MISSING" ]; then
    echo "❌ MISSING CONFIGURATION"
    echo ""
    echo "Please set the following in Render environment variables:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_ANON_KEY"
    echo ""
    exit 1
fi

echo "✅ Environment variables are configured!"
echo ""
echo "======================================"
echo ""
echo "🔧 NEXT STEP: Configure Supabase Dashboard"
echo ""
echo "Your redirect URL should be:"
if [ -n "$REDIRECT_URL" ]; then
    echo "  📍 $REDIRECT_URL"
else
    echo "  📍 https://your-app.onrender.com/auth/callback"
fi
echo ""
echo "To configure Supabase:"
echo "  1. Go to: https://app.supabase.com"
echo "  2. Select your project"
echo "  3. Go to: Authentication → URL Configuration"
echo "  4. Under 'Redirect URLs', click 'Add URL'"
echo "  5. Add the URL above"
echo "  6. Click Save"
echo ""
echo "Then test Google sign-in!"
echo ""
