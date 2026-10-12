import http.server
import json
import os
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment
load_dotenv()

# Ensure SSL cert for macOS
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

from roughcut.cli import get_default_drafts_dir

PORT = 5055
HOST = "127.0.0.1"

# Shared state for background tasks
task_state = {
    "running": False,
    "status": "idle",
    "progress_message": "",
    "logs": [],
    "last_result": None,
    "error": None
}

def log(msg: str):
    print(msg)
    task_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    task_state["progress_message"] = msg

def run_pipeline_thread(video_path, project_name, output_dir, mode, whisper_model, threshold, min_silence, padding):
    task_state["running"] = True
    task_state["status"] = "processing"
    task_state["logs"] = []
    task_state["error"] = None
    task_state["last_result"] = None

    try:
        log("بدء معالجة الفيديو...")
        log(f"الفيديو: {video_path}")
        log(f"الوضع المختار: {mode}")

        from roughcut.pipeline import process_video, process_studio_video

        # Reload .env in case user updated it
        load_dotenv(override=True)
        final_gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        final_hf_token = os.environ.get("HF_TOKEN", "").strip()

        if mode == "studio":
            if not final_gemini_key and not final_hf_token:
                raise ValueError("وضع المخرج الذكي (Studio) يتطلب إضافة مفتاح GEMINI_API_KEY داخل ملف .env أولاً.")
            
            log("تشغيل المخرج الذكي (Studio Mode)...")
            process_studio_video(
                video_path=video_path,
                output_dir=output_dir,
                hf_token=final_hf_token or None,
                project_name=project_name or None,
                whisper_model=whisper_model,
                padding=padding,
                threshold=threshold,
                min_silence=min_silence,
                gemini_key=final_gemini_key or None
            )
        else:
            log(f"تشغيل وضع ({mode})...")
            process_video(
                video_path=video_path,
                output_dir=output_dir,
                project_name=project_name or None,
                mode=mode,
                threshold=threshold,
                min_silence=min_silence,
                whisper_model=whisper_model,
                padding=padding
            )

        log("✅ اكتمل المونتاج بنجاح! تم إنشاء مسودة المشروع داخل CapCut.")
        task_state["status"] = "success"
        task_state["last_result"] = {
            "output_dir": output_dir,
            "project_name": project_name or Path(video_path).stem + "_CapRoughCut"
        }
    except Exception as e:
        err_msg = str(e)
        log(f"❌ حدث خطأ: {err_msg}")
        task_state["status"] = "error"
        task_state["error"] = err_msg
    finally:
        task_state["running"] = False

class WebUIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress routine HTTP request logging to keep console clean
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/status":
            env_path = Path(".env")
            load_dotenv(override=True)
            has_gemini = bool(os.environ.get("GEMINI_API_KEY", "").strip())
            has_hf = bool(os.environ.get("HF_TOKEN", "").strip())
            
            data = {
                "running": task_state["running"],
                "status": task_state["status"],
                "progress_message": task_state["progress_message"],
                "logs": task_state["logs"],
                "error": task_state["error"],
                "last_result": task_state["last_result"],
                "default_output_dir": get_default_drafts_dir(),
                "has_gemini": has_gemini,
                "has_hf": has_hf
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8")) if body else {}

        if parsed.path == "/api/browse_video":
            chosen_path = ""
            if sys.platform == "darwin":
                try:
                    cmd = [
                        "osascript", "-e",
                        'POSIX path of (choose file with prompt "اختر ملف الفيديو" of type {"public.movie", "mp4", "mov", "mkv", "avi"})'
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0:
                        chosen_path = res.stdout.strip()
                except Exception:
                    pass
            elif sys.platform == "win32":
                try:
                    ps_cmd = (
                        "Add-Type -AssemblyName System.Windows.Forms; "
                        "$dlg = New-Object System.Windows.Forms.OpenFileDialog; "
                        "$dlg.Filter = 'Video Files (*.mp4;*.mov;*.mkv;*.avi)|*.mp4;*.mov;*.mkv;*.avi|All Files (*.*)|*.*'; "
                        "$dlg.Title = 'اختر ملف الفيديو'; "
                        "if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $dlg.FileName }"
                    )
                    res = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        capture_output=True, text=True
                    )
                    if res.returncode == 0:
                        chosen_path = res.stdout.strip()
                except Exception:
                    pass
                if not chosen_path:
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        root.wm_attributes("-topmost", 1)
                        chosen_path = filedialog.askopenfilename(
                            filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi"), ("All files", "*.*")]
                        )
                        root.destroy()
                    except Exception:
                        pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"path": chosen_path}).encode("utf-8"))

        elif parsed.path == "/api/open_capcut":
            out_dir = payload.get("output_dir", "")
            try:
                if sys.platform == "darwin":
                    subprocess.run(["open", "-a", "CapCut"], check=False)
                    if out_dir and os.path.exists(out_dir):
                        subprocess.run(["open", out_dir], check=False)
                elif sys.platform == "win32":
                    if out_dir and os.path.exists(out_dir):
                        os.startfile(out_dir)
                    common_paths = [
                        os.path.expandvars(r"%LOCALAPPDATA%\CapCut\Apps\CapCut.exe"),
                        os.path.expandvars(r"%PROGRAMFILES%\CapCut\CapCut.exe"),
                        os.path.expandvars(r"%PROGRAMFILES(X86)%\CapCut\CapCut.exe"),
                    ]
                    for cp in common_paths:
                        if os.path.exists(cp):
                            os.startfile(cp)
                            break
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

        elif parsed.path == "/api/start":
            if task_state["running"]:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "هناك عملية قيد التنفيذ حالياً"}).encode("utf-8"))
                return

            video_path = payload.get("video_path", "").strip()
            if not video_path or not os.path.exists(video_path):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "ملف الفيديو غير موجود أو المسار غير صحيح"}).encode("utf-8"))
                return

            project_name = payload.get("project_name", "").strip()
            output_dir = payload.get("output_dir", "").strip() or get_default_drafts_dir()
            mode = payload.get("mode", "studio")
            whisper_model = payload.get("whisper_model", "large-v2")
            threshold = float(payload.get("threshold", -30.0))
            min_silence = float(payload.get("min_silence", 1.5 if mode == "studio" else 0.5))
            padding = float(payload.get("padding", 0.3 if mode == "studio" else 0.15))

            t = threading.Thread(
                target=run_pipeline_thread,
                args=(video_path, project_name, output_dir, mode, whisper_model, threshold, min_silence, padding),
                daemon=True
            )
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

HTML_PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CapRoughCut - مونتاج تلقائي بالذكاء الاصطناعي</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0c0f17;
      --card-bg: #151b28;
      --card-border: #232d42;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #10b981;
      --danger: #ef4444;
      --text: #f3f4f6;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Cairo', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; padding: 24px 16px; }
    .container { max-width: 820px; margin: 0 auto; }
    
    .header { text-align: center; margin-bottom: 28px; }
    .header h1 { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .header p { color: var(--text-muted); font-size: 0.98rem; margin-top: 6px; }

    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 22px; margin-bottom: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    .card-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    .form-group { margin-bottom: 18px; }
    label { display: block; font-size: 0.9rem; font-weight: 600; margin-bottom: 6px; color: #cbd5e1; }
    .help-text { font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }
    
    .input-row { display: flex; gap: 8px; }
    input[type="text"], input[type="password"], select {
      flex: 1; background: #0f1420; border: 1px solid var(--card-border); border-radius: 10px; padding: 12px 14px; color: #fff; font-size: 0.95rem; outline: none; transition: border-color 0.2s;
    }
    input[type="text"]:focus, input[type="password"]:focus, select:focus { border-color: var(--primary); }

    .btn {
      background: var(--primary); color: #fff; border: none; border-radius: 10px; padding: 12px 20px; font-weight: 700; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-size: 0.95rem;
    }
    .btn:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .btn-secondary { background: #1e293b; color: #e2e8f0; border: 1px solid var(--card-border); }
    .btn-secondary:hover { background: #334155; }
    .btn-accent { background: #059669; }
    .btn-accent:hover { background: #047857; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

    .mode-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
    .mode-option {
      background: #0f1420; border: 2px solid var(--card-border); border-radius: 12px; padding: 14px; cursor: pointer; transition: all 0.2s; position: relative;
    }
    .mode-option:hover { border-color: #3b82f6; }
    .mode-option.active { border-color: #3b82f6; background: rgba(59, 130, 246, 0.08); }
    .mode-title { font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 6px; }
    .mode-desc { font-size: 0.8rem; color: var(--text-muted); margin-top: 6px; line-height: 1.4; }
    .badge { background: #2563eb; color: #fff; font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; margin-right: 6px; }

    .accordion-toggle {
      background: none; border: none; color: var(--text-muted); width: 100%; text-align: right; cursor: pointer; font-size: 0.9rem; font-weight: 600; display: flex; justify-content: space-between; align-items: center; padding: 8px 0;
    }
    .accordion-content { display: none; margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--card-border); }
    .accordion-content.open { display: block; }

    .log-box {
      background: #090c13; border: 1px solid #1c2438; border-radius: 10px; padding: 14px; height: 180px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #a5f3fc; line-height: 1.6; direction: ltr; text-align: left;
    }

    .status-banner {
      padding: 14px 18px; border-radius: 12px; margin-bottom: 18px; display: none; align-items: center; justify-content: space-between;
    }
    .status-banner.success { display: flex; background: rgba(16, 185, 129, 0.15); border: 1px solid #059669; color: #34d399; }
    .status-banner.error { display: flex; background: rgba(239, 68, 68, 0.15); border: 1px solid #dc2626; color: #f87171; }

    .spinner {
      border: 3px solid rgba(255, 255, 255, 0.2); border-top: 3px solid #fff; border-radius: 50%; width: 18px; height: 18px; animation: spin 0.8s linear infinite; display: inline-block;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎬 CapRoughCut</h1>
      <p>الأداة الذكية لتقطيع وتجهيز مسودة فيديو CapCut أوتوماتيكياً</p>
    </div>

    <!-- Status Banner -->
    <div id="statusBanner" class="status-banner">
      <div id="statusText"></div>
      <button id="openCapcutBtn" class="btn btn-accent btn-sm" onclick="openCapCut()" style="display:none;">فتح CapCut 🚀</button>
    </div>

    <!-- Main Card -->
    <div class="card">
      <div class="card-title">📁 اختيار الفيديو</div>
      <div class="form-group">
        <label>ملف الفيديو المراد مونتاجه:</label>
        <div class="input-row">
          <input type="text" id="videoPath" placeholder="اسحب الملف هنا أو اضغط 'استعراض'..." />
          <button type="button" class="btn btn-secondary" onclick="browseVideo()">📂 استعراض...</button>
        </div>
        <div class="help-text">يدعم صيغ MP4, MOV, MKV وغيرها.</div>
      </div>

      <div class="form-group">
        <label>اسم المشروع في CapCut (اختياري):</label>
        <input type="text" id="projectName" placeholder="تلقائي (بنفس اسم الفيديو)" />
      </div>
    </div>

    <!-- Mode Selector Card -->
    <div class="card">
      <div class="card-title">⚙️ وضع المونتاج الذكي</div>
      <div class="mode-cards">
        <div class="mode-option active" onclick="setMode('studio', this)">
          <div class="mode-title">
            <span>🎬 المخرج الذكي (AI Director)</span>
            <span class="badge">الأفضل</span>
          </div>
          <div class="mode-desc">
            يستخدم Gemini لفهم الكلام وحذف الإعادات الفاشلة، التأتأة، وسوالف الكواليس وترك أفضل نسخة كاملة.
          </div>
        </div>

        <div class="mode-option" onclick="setMode('silence', this)">
          <div class="mode-title">
            <span>🔇 قص الصمت فقط</span>
          </div>
          <div class="mode-desc">
            سريع جداً! يقوم بقص الوقفات الطويلة وفترات السكوت بدون معالجة لغوية.
          </div>
        </div>

        <div class="mode-option" onclick="setMode('both', this)">
          <div class="mode-title">
            <span>✂️ قص الصمت واللزمات</span>
          </div>
          <div class="mode-desc">
            يقص فترات الصمت بالإضافة لكلمات الحشو مثل (امم، يعني، آه، umm، like).
          </div>
        </div>
      </div>
    </div>

    <!-- Settings Card -->
    <div class="card">
      <button type="button" class="accordion-toggle" onclick="toggleSettings()">
        <span>⚙️ إعدادات المسار وحالة الذكاء الاصطناعي</span>
        <span id="accIcon">▼</span>
      </button>
      <div id="settingsContent" class="accordion-content">
        <div class="form-group">
          <label>حالة مفتاح الذكاء الاصطناعي (Gemini):</label>
          <div id="geminiStatus" style="font-size: 0.9rem; padding: 12px; background: #0f1420; border-radius: 8px; border: 1px solid var(--card-border);">
            جاري الفحص...
          </div>
          <div class="help-text">يتم قراءة المفتاح تلقائياً من ملف <code>.env</code> (GEMINI_API_KEY).</div>
        </div>

        <div class="form-group">
          <label>مجلد مسودات CapCut (تم التعرف عليه تلقائياً):</label>
          <input type="text" id="draftsDir" />
        </div>
      </div>
    </div>

    <!-- Start Action -->
    <div style="text-align: center; margin-bottom: 24px;">
      <button id="startBtn" class="btn" style="width: 100%; padding: 16px; font-size: 1.15rem;" onclick="startCut()">
        <span id="startBtnText">🚀 ابدأ المونتاج التلقائي</span>
      </button>
    </div>

    <!-- Live Logs -->
    <div class="card">
      <div class="card-title">
        <span>📜 سجل العمليات المباشر</span>
      </div>
      <div id="logBox" class="log-box">في انتظار بدء المونتاج...</div>
    </div>
  </div>

  <script>
    let selectedMode = 'studio';
    let pollInterval = null;

    function setMode(mode, el) {
      selectedMode = mode;
      document.querySelectorAll('.mode-option').forEach(card => card.classList.remove('active'));
      el.classList.add('active');
    }

    function toggleSettings() {
      const content = document.getElementById('settingsContent');
      const icon = document.getElementById('accIcon');
      content.classList.toggle('open');
      icon.textContent = content.classList.contains('open') ? '▲' : '▼';
    }

    async function loadStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (data.default_output_dir && !document.getElementById('draftsDir').value) {
          document.getElementById('draftsDir').value = data.default_output_dir;
        }

        const geminiEl = document.getElementById('geminiStatus');
        if (data.has_gemini) {
          geminiEl.innerHTML = '<span style="color: #34d399; font-weight: 700;">✅ مفتاح Gemini موجود في ملف .env وجاهز للاستخدام.</span>';
        } else {
          geminiEl.innerHTML = '<span style="color: #fbbf24; font-weight: 700;">⚠️ مفتاح Gemini غير موجود في ملف .env. (لوضع المخرج الذكي، أضف مفتاحك في ملف <code>.env</code>).</span>';
        }

        if (data.running) {
          setRunningUI(true);
          updateLogs(data.logs);
        }
      } catch(e) {
        console.error(e);
      }
    }

    async function browseVideo() {
      try {
        const res = await fetch('/api/browse_video', { method: 'POST' });
        const data = await res.json();
        if (data.path) {
          document.getElementById('videoPath').value = data.path;
        }
      } catch (e) {
        alert("تعذر فتح مستعرض الملفات.");
      }
    }

    async function startCut() {
      const video_path = document.getElementById('videoPath').value.trim();
      if (!video_path) {
        alert("يرجى اختيار ملف الفيديو أولاً.");
        return;
      }

      const project_name = document.getElementById('projectName').value.trim();
      const output_dir = document.getElementById('draftsDir').value.trim();

      setRunningUI(true);
      hideBanner();

      const res = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path,
          project_name,
          output_dir,
          mode: selectedMode
        })
      });

      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "حدث خطأ أثناء البدء");
        setRunningUI(false);
        return;
      }

      pollLogs();
    }

    function setRunningUI(isRunning) {
      const btn = document.getElementById('startBtn');
      const text = document.getElementById('startBtnText');
      btn.disabled = isRunning;
      if (isRunning) {
        text.innerHTML = '<span class="spinner"></span> جاري المونتاج والمعالجة...';
      } else {
        text.innerText = '🚀 ابدأ المونتاج التلقائي';
      }
    }

    function updateLogs(logs) {
      if (!logs || !logs.length) return;
      const box = document.getElementById('logBox');
      box.innerText = logs.join('\\n');
      box.scrollTop = box.scrollHeight;
    }

    function pollLogs() {
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(async () => {
        try {
          const res = await fetch('/api/status');
          const data = await res.json();
          updateLogs(data.logs);

          if (!data.running) {
            clearInterval(pollInterval);
            setRunningUI(false);
            if (data.status === 'success') {
              showBanner("success", "🎉 تم تجهيز مشروع CapCut بنجاح! افتح برنامج CapCut وستجد المسودة جاهزة.", true);
            } else if (data.status === 'error') {
              showBanner("error", "❌ حدث خطأ: " + (data.error || "خطأ غير معروف"), false);
            }
          }
        } catch(e) {
          console.error(e);
        }
      }, 1000);
    }

    function showBanner(type, message, showCapcut) {
      const banner = document.getElementById('statusBanner');
      const text = document.getElementById('statusText');
      const btn = document.getElementById('openCapcutBtn');
      banner.className = 'status-banner ' + type;
      text.innerText = message;
      btn.style.display = showCapcut ? 'inline-flex' : 'none';
      banner.style.display = 'flex';
    }

    function hideBanner() {
      document.getElementById('statusBanner').style.display = 'none';
    }

    async function openCapCut() {
      const output_dir = document.getElementById('draftsDir').value.trim();
      await fetch('/api/open_capcut', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ output_dir })
      });
    }

    window.onload = loadStatus;
  </script>
</body>
</html>
"""

def main():
    server = http.server.ThreadingHTTPServer((HOST, PORT), WebUIHandler)
    url = f"http://{HOST}:{PORT}"
    print("=" * 60)
    print(f"🚀 CapRoughCut Web UI شغال بنجاح على الرابط:")
    print(f"👉 {url}")
    print("=" * 60)
    
    # Open browser automatically after half a second
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nتم إيقاف التطبيق.")
        server.server_close()

if __name__ == "__main__":
    main()
