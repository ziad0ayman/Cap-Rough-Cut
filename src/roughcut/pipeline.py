import os
from roughcut.analyzer.media import get_media_info
from roughcut.analyzer.silence import detect_silence
from roughcut.analyzer.transcribe import transcribe, find_filler_regions
from roughcut.analyzer.diarize import diarize_transcript
from roughcut.analyzer.speakers import identify_talent, get_crew_regions, get_talent_segments
from roughcut.analyzer.takes import detect_repeated_takes, get_bad_take_regions
from roughcut.edl.builder import build_edl
from roughcut.capcut.project import CapCutProjectGenerator

def process_video(
    video_path: str,
    output_dir: str,
    project_name: str = None,
    mode: str = "both",
    threshold: float = -30.0,
    min_silence: float = 0.5,
    whisper_model: str = "large-v3",
    remove_fillers: bool = True,
    padding: float = 0.15
):
    """Standard processing pipeline (no diarization)."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    if not project_name:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        project_name = f"{base_name}_RoughCut"

    print(f"[{project_name}] Extracting media info...")
    media_info = get_media_info(video_path)
    total_sec = media_info["duration_us"] / 1_000_000.0

    silent_regions = []
    if mode in ["silence", "both"]:
        print(f"[{project_name}] Detecting silence (threshold={threshold}dB, min={min_silence}s)...")
        silent_regions = detect_silence(video_path, noise_db=threshold, min_duration=min_silence)
        print(f"[{project_name}] Found {len(silent_regions)} silent regions.")

    filler_regions = []
    if mode in ["transcript", "both"]:
        print(f"[{project_name}] Transcribing video with model '{whisper_model}'...")
        words = transcribe(video_path, model_size=whisper_model)
        print(f"[{project_name}] Transcribed {len(words)} words.")
        
        if remove_fillers:
            filler_regions = find_filler_regions(words)
            print(f"[{project_name}] Found {len(filler_regions)} filler words to remove.")

    print(f"[{project_name}] Building Edit Decision List (EDL)...")
    edl = build_edl(
        total_duration=total_sec,
        silent_regions=silent_regions,
        filler_regions=filler_regions,
        padding=padding
    )
    
    _generate_and_save(project_name, output_dir, media_info, edl, total_sec)

def process_studio_video(
    video_path: str,
    output_dir: str,
    hf_token: str,
    project_name: str = None,
    whisper_model: str = "large-v2",
    similarity_threshold: float = 0.65,
    remove_fillers: bool = True,
    padding: float = 0.30,
    threshold: float = -30.0,
    min_silence: float = 1.5,
    gemini_key: str = None,
):
    """Studio processing pipeline (diarization + smart take detection)."""
    if not hf_token:
        raise ValueError("Hugging Face token (--hf-token) is required for studio mode.")
        
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    if not project_name:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        project_name = f"{base_name}_StudioCut"

    print(f"[{project_name}] Extracting media info...")
    media_info = get_media_info(video_path)
    total_sec = media_info["duration_us"] / 1_000_000.0
    
    print(f"[{project_name}] Starting Studio AI Analysis Pipeline...")
    
    if gemini_key:
        print(f"[{project_name}] Enabling AI Director Mode (Gemini)...")
        from roughcut.analyzer.diarize import transcribe_for_ai
        from roughcut.analyzer.llm import get_ai_director_decisions
        from roughcut.edl.builder import build_edl_from_keeps
        
        # Skip Pyannote diarization! The AI can understand context natively.
        fine_segments = transcribe_for_ai(video_path, model_size=whisper_model)
        keep_regions = get_ai_director_decisions(fine_segments, gemini_key)
        
        # We can use a smaller padding now because we have precise word timestamps!
        ai_padding = max(padding, 0.3)
        print(f"[{project_name}] Applying {ai_padding}s safe padding to cuts...")
        edl = build_edl_from_keeps(total_sec, keep_regions, padding=ai_padding)
    else:
        segments, diarize_df = diarize_transcript(video_path, hf_token, model_size=whisper_model)
        
        talent_id = identify_talent(diarize_df)
        crew_regions = get_crew_regions(diarize_df, talent_id)
        print(f"[{project_name}] Found {len(crew_regions)} crew interruptions to cut.")
        
        print(f"[{project_name}] Using standard heuristic take detection (no AI Director)...")
        talent_segs = get_talent_segments(segments, talent_id)
        takes = detect_repeated_takes(talent_segs, similarity_threshold)
        bad_take_regions = get_bad_take_regions(takes)
        
        bad_take_count = sum(1 for t in takes if not t.is_best)
        print(f"[{project_name}] Found {bad_take_count} bad takes to cut.")
        
        silent_regions = detect_silence(video_path, noise_db=threshold, min_duration=min_silence)
        print(f"[{project_name}] Found {len(silent_regions)} silent regions to cut.")
        
        filler_regions = []
        if remove_fillers:
            from roughcut.analyzer.transcribe import find_filler_regions, Word
            talent_words = []
            for seg in talent_segs:
                for w in seg.words:
                    talent_words.append(Word(
                        text=w.text, start=w.start, end=w.end, 
                        probability=w.probability, language=w.language
                    ))
            filler_regions = find_filler_regions(talent_words)
            print(f"[{project_name}] Found {len(filler_regions)} filler words to remove.")

        print(f"[{project_name}] Building unified Edit Decision List (EDL)...")
        all_cuts = filler_regions + crew_regions + bad_take_regions
        edl = build_edl(total_sec, silent_regions, all_cuts, padding)
    
    _generate_and_save(project_name, output_dir, media_info, edl, total_sec)

def _generate_and_save(project_name, output_dir, media_info, edl, total_sec):
    cut_count = sum(1 for r in edl if r.action == "cut")
    keep_time = sum(r.end - r.start for r in edl if r.action == "keep")
    print(f"[{project_name}] EDL built: {cut_count} cuts. Kept {keep_time:.2f}s out of {total_sec:.2f}s.")

    print(f"[{project_name}] Generating CapCut project...")
    generator = CapCutProjectGenerator(project_name, output_dir, media_info)
    generator.build_from_edl(edl)
    generator.save()
    
    print(f"[{project_name}] Done! Open '{project_name}' in CapCut.")
