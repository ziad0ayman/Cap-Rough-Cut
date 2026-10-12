#!/bin/bash
cd "$(dirname "$0")"

source .venv/bin/activate

if [ $# -eq 0 ]; then
    # Interactive CLI mode
    echo "=========================================================="
    echo "🎬 CapRoughCut - أداة المونتاج التلقائي"
    echo "=========================================================="
    echo "1) تشغيل واجهة المتصفح السهلة (موصى به)"
    echo "2) تشغيل سريع عبر سطر الأوامر"
    read -p "اختر (1 أو 2): " choice
    if [ "$choice" == "2" ]; then
        read -p "اسحب ملف الفيديو هنا واضغط Enter: " videopath
        videopath=$(echo "$videopath" | tr -d "'\"")
        echo "جاري المونتاج..."
        caproughcut "$videopath" --mode studio
    else
        python3 app.py
    fi
else
    caproughcut "$@"
fi
