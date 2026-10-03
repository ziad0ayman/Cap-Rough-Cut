from collections import defaultdict
from typing import List, Tuple
from roughcut.analyzer.diarize import DiarizedSegment

def identify_talent(diarize_df) -> str:
    """
    Identifies the talent (on-camera speaker) from raw diarization data.
    Heuristic: The talent is the speaker with the MOST total speaking time.
    """
    speaker_time = defaultdict(float)
    for _, row in diarize_df.iterrows():
        duration = row['end'] - row['start']
        speaker_time[row['speaker']] += duration
    
    if not speaker_time:
        return "UNKNOWN"
    
    talent = max(speaker_time, key=speaker_time.get)
    
    # Print summary
    print("\n--- Speaker Analysis ---")
    total = sum(speaker_time.values())
    for spk, t in sorted(speaker_time.items(), key=lambda x: -x[1]):
        role = "- TALENT (On-Camera)" if spk == talent else "  (Crew/Off-Camera)"
        print(f"  {spk}: {t:.1f}s ({t/total*100:.0f}%) {role}")
    print("------------------------\n")
    
    return talent

def get_crew_regions(diarize_df, talent_id: str) -> List[Tuple[float, float]]:
    """Returns time regions where crew (non-talent) is speaking from raw audio."""
    regions = []
    for _, row in diarize_df.iterrows():
        if row['speaker'] != talent_id:
            regions.append((row['start'], row['end']))
    return regions

def get_talent_segments(segments: List[DiarizedSegment], 
                        talent_id: str) -> List[DiarizedSegment]:
    """Returns only the talent's speech segments, in chronological order."""
    return [s for s in segments if s.speaker == talent_id]
