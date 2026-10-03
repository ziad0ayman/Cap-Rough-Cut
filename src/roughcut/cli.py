import argparse
import os
import sys

from roughcut.pipeline import process_video, process_studio_video

def main():
    parser = argparse.ArgumentParser(
        prog="roughcut",
        description="Automatic rough cut generator for CapCut Desktop (Silence & Transcript-based)"
    )
    parser.add_argument("input", help="Video file or directory of videos")
    parser.add_argument("-n", "--name", help="Project name (default: auto-generated based on filename)")
    parser.add_argument("-o", "--output",
        default=os.path.expandvars(r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft"),
        help="CapCut drafts directory")
    
    # Modes
    parser.add_argument("--mode", choices=["silence", "transcript", "both", "studio"],
        default="both", help="Detection mode (default: both)")
    
    # Studio mode config
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"),
        help="Hugging Face token for speaker diarization (required for --mode studio)")
    parser.add_argument("--gemini-key", default=os.environ.get("GEMINI_API_KEY"),
        help="Gemini API Key for AI Director mode (optional)")
    parser.add_argument("--similarity", type=float, default=0.65,
        help="Take similarity threshold 0.0-1.0 (default: 0.65)")
    
    # Silence config
    parser.add_argument("--threshold", type=float, default=-30.0,
        help="Silence threshold in dB (default: -30)")
    parser.add_argument("--min-silence", type=float, default=0.5,
        help="Minimum silence duration in seconds (default: 0.5)")
    
    # Transcript config
    parser.add_argument("--whisper-model", default="large-v2",
        help="Whisper model (tiny/base/small/medium/large-v2/large-v3). Default is large-v2 for optimal Arabic dialect support.")
    parser.add_argument("--no-fillers", action="store_true",
        help="Don't remove filler words (um, uh, يعني, etc.)")
    
    # Editing config
    parser.add_argument("--padding", type=float, default=0.15,
        help="Padding around cuts in seconds to avoid clipping words (default: 0.15)")
    
    args = parser.parse_args()
    
    # Studio mode uses more conservative defaults if user didn't override
    if args.mode == "studio":
        # Only override if user didn't explicitly pass these flags
        if "--min-silence" not in sys.argv:
            args.min_silence = 1.5   # Studio footage has natural pauses
        if "--padding" not in sys.argv:
            args.padding = 0.30      # More breathing room around cuts
    
    if args.mode == "studio" and not args.hf_token:
        print("Error: --hf-token is required for 'studio' mode. Set the HF_TOKEN environment variable or pass it directly.")
        sys.exit(1)
    
    # Validate output dir
    if not os.path.exists(args.output):
        print(f"Warning: Output directory '{args.output}' does not exist. Creating it.")
        os.makedirs(args.output, exist_ok=True)
        
    input_path = args.input
    
    if os.path.isdir(input_path):
        # Batch mode
        video_files = [f for f in os.listdir(input_path) if f.lower().endswith(('.mp4', '.mov', '.mkv', '.avi'))]
        if not video_files:
            print(f"No video files found in '{input_path}'")
            sys.exit(1)
            
        print(f"Found {len(video_files)} videos. Starting batch processing...")
        for vf in video_files:
            full_path = os.path.join(input_path, vf)
            _run_pipeline(full_path, args, project_name=None)
    else:
        # Single file
        _run_pipeline(input_path, args, project_name=args.name)

def _run_pipeline(input_path, args, project_name):
    try:
        if args.mode == "studio":
            process_studio_video(
                input_path, args.output, hf_token=args.hf_token, project_name=project_name,
                whisper_model=args.whisper_model, similarity_threshold=args.similarity,
                remove_fillers=not args.no_fillers, padding=args.padding,
                threshold=args.threshold, min_silence=args.min_silence,
                gemini_key=args.gemini_key
            )
        else:
            process_video(
                input_path, args.output, project_name=project_name,
                mode=args.mode, threshold=args.threshold, min_silence=args.min_silence,
                whisper_model=args.whisper_model, remove_fillers=not args.no_fillers,
                padding=args.padding
            )
    except Exception as e:
        print(f"Error processing '{input_path}': {e}")

if __name__ == "__main__":
    main()
