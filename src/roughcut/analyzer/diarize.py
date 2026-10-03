from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import gc

@dataclass
class DiarizedWord:
    text: str
    start: float
    end: float
    speaker: str
    probability: float
    language: str = ""

@dataclass 
class DiarizedSegment:
    text: str
    start: float
    end: float
    speaker: str
    words: List[DiarizedWord] = field(default_factory=list)

def diarize_transcript(
    video_path: str,
    hf_token: str,
    model_size: str = "large-v3",
    device: str = "cuda",
    batch_size: int = 4,
    compute_type: str = "int8",
) -> Tuple[List[DiarizedSegment], "pd.DataFrame"]:
    """
    Full WhisperX pipeline: transcribe -> align -> diarize -> assign speakers.
    Returns segments with speaker labels and word-level timestamps.
    """
    import whisperx

    print(f"Loading WhisperX model '{model_size}' on {device} ({compute_type})...")
    # Step 1: Transcribe
    model = whisperx.load_model(model_size, device, compute_type=compute_type, language=None)
    audio = whisperx.load_audio(video_path)
    result = model.transcribe(audio, batch_size=batch_size)
    detected_language = result.get("language", "ar")
    
    print(f"Transcription complete (Language: {detected_language}). Freeing memory...")
    # Free GPU memory before alignment
    del model
    gc.collect()
    if device == "cuda":
        import torch
        torch.cuda.empty_cache()

    # Step 2: Skip whisperx.align because wav2vec2 alignment drops mixed-language (English) words in Arabic text!
    # We will use the original Whisper segments and assign speakers using overlap with Pyannote.

    print("Running speaker diarization on CPU (to avoid GPU OOM)...")
    # Step 3: Speaker diarization — MUST run on CPU.
    import torch
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    
    from whisperx.diarize import DiarizationPipeline
    diarize_model = DiarizationPipeline(
        token=hf_token, device="cpu"
    )
    # Force min_speakers=2: we KNOW there's at least talent + crew
    diarize_segments = diarize_model(
        video_path, min_speakers=2
    )
    
    print("Assigning speakers to segments via overlap...")
    
    # Simple overlap function
    def get_dominant_speaker(seg_start, seg_end, df):
        speaker_durations = {}
        for _, row in df.iterrows():
            # Calculate overlap
            overlap_start = max(seg_start, row['start'])
            overlap_end = min(seg_end, row['end'])
            if overlap_end > overlap_start:
                dur = overlap_end - overlap_start
                speaker_durations[row['speaker']] = speaker_durations.get(row['speaker'], 0) + dur
        if not speaker_durations:
            return "UNKNOWN"
        return max(speaker_durations.items(), key=lambda x: x[1])[0]

    # Convert to our data structures
    segments = []
    for seg in result["segments"]:
        # Assign speaker based on maximum overlap with Pyannote dataframe
        speaker = get_dominant_speaker(seg["start"], seg["end"], diarize_segments)
        
        segments.append(DiarizedSegment(
            text=seg.get("text", "").strip(),
            start=seg["start"],
            end=seg["end"],
            speaker=speaker,
            words=[], # No word-level timestamps since we skipped align
        ))
    
    return segments, diarize_segments

def transcribe_for_ai(
    video_path: str,
    model_size: str = "large-v2",
    device: str = "cuda",
    compute_type: str = "int8",
) -> List[Tuple[float, float, str]]:
    """
    Transcribes audio using faster-whisper (word_timestamps=True) and returns
    fine-grained chunks (e.g. ~3 seconds) for the AI Director to cut precisely.
    Skips Pyannote entirely.
    """
    from faster_whisper import WhisperModel
    import gc
    import torch

    print(f"Loading faster-whisper '{model_size}' on {device} ({compute_type})...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    import whisperx
    audio = whisperx.load_audio(video_path)
    
    print("Transcribing with word-level timestamps...")
    segments, info = model.transcribe(audio, word_timestamps=True, vad_filter=True)
    
    fine_segments = []
    for seg in segments:
        chunk_words = []
        chunk_start = seg.start
        for i, word in enumerate(seg.words):
            chunk_words.append(word.word)
            # Break chunk every ~3 seconds OR at the end of the segment
            if word.end - chunk_start >= 3.0 or i == len(seg.words) - 1:
                text = "".join(chunk_words).strip()
                if text:
                    fine_segments.append((chunk_start, word.end, text))
                if i != len(seg.words) - 1:
                    chunk_start = word.end
                    chunk_words = []
                    
    del model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
        
    return fine_segments
