#!/bin/bash
cd "$(dirname "$0")"

echo "=========================================================="
echo "🎬 مرحباً بك في CapRoughCut (مونتاج تلقائي لـ CapCut) 🚀"
echo "=========================================================="
echo ""

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ لم يتم العثور على البيئة الافتراضية .venv!"
    exit 1
fi

# Run the web app
echo "جاري فتح لوحة التحكم في المتصفح..."
python3 app.py
