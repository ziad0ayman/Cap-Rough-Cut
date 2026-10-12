# CapRoughCut (CapCut Plugin)

An automated, AI-powered rough cut generator designed specifically for CapCut Desktop. It analyzes raw studio footage, removes bad takes, cuts out crew chatter, trims silences, and generates a native CapCut Draft project automatically.

## Features
* **Studio AI Director Mode:** Uses Gemini 1.5/3.8 Flash to semantically understand the script, drop failed takes/stutters, and stitch together a flawless final chronological sequence.
* **High-Precision Arabic Dialect Support:** Utilizes `faster-whisper` (`large-v2` by default) with exact word-level timestamps to flawlessly transcribe mixed Arabic/English without hallucinations or dropped words.
* **Smart Silence & Filler Removal:** Automatically detect and remove extended silences or filler words.
* **Native CapCut Integration:** Generates a complete `draft_content.json` folder structure that appears natively inside CapCut Desktop.

## Quick Start (No Technical Background Required)

### 🪟 On Windows:
1. Double-click `install_windows.bat` (first time only) to set up everything automatically.
2. Open `.env` in any text editor and add your `GEMINI_API_KEY`:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   ```
3. Double-click `Start_CapRoughCut.bat` to launch the easy web dashboard in your browser!

### 🍎 On macOS:
1. Open `.env` in any text editor and add your `GEMINI_API_KEY`:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   ```
2. Double-click `Start_CapRoughCut.command` to launch the easy web dashboard in your browser!

---

## Manual Installation (Developers & Power Users)

1. Clone this repository:
   ```bash
   git clone https://github.com/ziad0ayman/Cap-Rough-Cut.git
   cd Cap-Rough-Cut
   ```
2. Create a Python 3.10+ virtual environment:
   - **Windows:**
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

## Configuration
Create a `.env` file in the root of the project (copy `.env.example`) and add your API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

### Web Interface:
```bash
python app.py
```

### CLI:
```bash
caproughcut path/to/video.mp4 --mode studio
```

### Modes
* `--mode studio`: Uses Gemini and Whisper to intelligently construct the final take by removing crew chat and outtakes.
* `--mode silence`: Only trims out silences and dead air.
* `--mode both` (or `--mode transcript`): Removes silences and filler words without AI context filtering.

Once the script finishes, simply open CapCut Desktop and you will see a new local draft project waiting for you with the rough cut already applied!
