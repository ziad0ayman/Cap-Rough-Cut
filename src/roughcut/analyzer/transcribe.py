from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Word:
    text: str
    start: float
    end: float
    probability: float
    language: str = ""

# Arabic fillers (MSA + common dialects)
AR_FILLERS = {"يعني", "هيك", "طيب", "آه", "إيه", "أه", "امم", "هاه", "والله", "بس"}
# English fillers
EN_FILLERS = {"um", "uh", "like", "you know", "basically", "actually", "so", "well", "right"}
ALL_FILLERS = AR_FILLERS | EN_FILLERS

def clean_word(word: str) -> str:
    """Removes punctuation to properly match filler words."""
    import string
    # Remove basic punctuation
    w = word.strip(string.punctuation + "،؛؟")
    return w.lower()

def transcribe(video_path: str, model_size: str = "large-v3") -> List[Word]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError("faster-whisper is not installed. Run 'pip install faster-whisper'")

    # Set compute_type to float16 for speed if GPU is available, else int8
    # device="auto" automatically selects CUDA if available
    model = WhisperModel(model_size, device="auto", compute_type="default")
    
    # We use VAD filter to ignore purely silent segments and avoid hallucination
    segments, info = model.transcribe(
        video_path,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=300),
    )
    
    words = []
    # Process generator
    for seg in segments:
        # Some versions put language on the segment, some on the info
        lang = getattr(seg, 'language', info.language)
        if seg.words:
            for w in seg.words:
                words.append(Word(
                    text=w.word.strip(),
                    start=w.start,
                    end=w.end,
                    probability=w.probability,
                    language=lang,
                ))
    return words

def find_filler_regions(words: List[Word]) -> List[Tuple[float, float]]:
    """Identify filler word regions to cut based on the AR and EN dictionary."""
    regions = []
    for w in words:
        cleaned = clean_word(w.text)
        if cleaned in ALL_FILLERS:
            regions.append((w.start, w.end))
    return regions
