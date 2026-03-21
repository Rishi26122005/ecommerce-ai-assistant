#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#   ShopAI – Setup Script
#   Run: bash setup.sh
# ═══════════════════════════════════════════════════════

set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   🛍️  ShopAI – Setup                     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Check Python ────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Please install Python 3.9+."
  exit 1
fi
echo "✅ Python3 found: $(python3 --version)"

# ── 2. Virtual environment ─────────────────────────────
if [ ! -d ".venv" ]; then
  echo "🔄 Creating virtual environment…"
  python3 -m venv .venv
fi

source .venv/bin/activate
echo "✅ Virtual environment activated."

# ── 3. Install deps ────────────────────────────────────
echo "🔄 Installing dependencies…"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed."

# ── 4. Check dataset ───────────────────────────────────
if [ ! -f "amazon.csv" ]; then
  echo ""
  echo "⚠️  WARNING: amazon.csv not found in current directory."
  echo "   Please copy your Amazon dataset CSV here as 'amazon.csv'"
  echo "   Expected columns: product_id, product_name, category,"
  echo "   discounted_price, actual_price, discount_percentage,"
  echo "   rating, rating_count, about_product, img_link, product_link"
  echo ""
fi

# ── 5. API Key prompt ──────────────────────────────────
if [ -z "$GEMINI_API_KEY" ]; then
  echo ""
  read -p "🔑 Enter your Gemini API key (or press Enter to skip): " KEY
  if [ -n "$KEY" ]; then
    export GEMINI_API_KEY="$KEY"
    echo "export GEMINI_API_KEY=\"$KEY\"" >> .env
    echo "✅ API key saved to .env"
  else
    echo "⚠️  No API key set. AI recommendations will show a placeholder message."
  fi
fi

# ── 6. Done ────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   🚀 Setup complete!                     ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "To start the app:"
echo "  source .venv/bin/activate"
echo "  python app.py"
echo ""
echo "Then open:  http://localhost:5000"
echo ""
echo "Note: First startup will build embeddings — this takes ~2-5 minutes on CPU."
