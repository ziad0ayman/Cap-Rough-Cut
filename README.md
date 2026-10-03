# CapRoughCut (CapCut Plugin)

An automated, AI-powered rough cut generator designed specifically for CapCut Desktop. It analyzes raw studio footage, removes bad takes, cuts out crew chatter, trims silences, and generates a native CapCut Draft project automatically.

## Features
* **Studio AI Director Mode:** Uses Gemini 1.5/3.8 Flash to semantically understand the script, drop failed takes/stutters, and stitch together a flawless final chronological sequence.
* **High-Precision Arabic Dialect Support:** Utilizes `faster-whisper` (`large-v2` by default) with exact word-level timestamps to flawlessly transcribe mixed Arabic/English without hallucinations or dropped words.
* **Smart Silence & Filler Removal:** Automatically detect and remove extended silences or filler words.
* **Native CapCut Integration:** Generates a complete `draft_content.json` folder structure that appears natively inside CapCut Desktop.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/ziad0ayman/Cap-Rough-Cut.git
   cd Cap-Rough-Cut
   ```
2. Create a Python 3.12 virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install PyTorch with CUDA support (for faster transcription).

## Configuration
Create a `.env` file in the root of the project (you can copy `.env.example`) and add your API keys:
```env
HF_TOKEN=your_huggingface_token
GEMINI_API_KEY=your_gemini_api_key
```

## Usage

Run the CLI tool against any raw video file:

```bash
python -m caproughcut path/to/video.mp4 --mode studio
```

### Modes
* `--mode studio`: Uses Gemini and Whisper to intelligently construct the final take by removing crew chat and outtakes.
* `--mode silence`: Only trims out silences and dead air.
* `--mode transcript`: Removes silences and filler words without AI context filtering.

Once the script finishes, simply open CapCut Desktop and you will see a new local draft project waiting for you with the rough cut already applied!
