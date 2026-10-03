import subprocess
import re
from dataclasses import dataclass
from typing import List

@dataclass
class SilentRegion:
    start: float  # seconds
    end: float
    duration: float

def detect_silence(
    video_path: str,
    noise_db: float = -30.0,
    min_duration: float = 0.5,
) -> List[SilentRegion]:
    """
    Runs FFmpeg silencedetect and returns a list of SilentRegion objects.
    """
    cmd = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=n={noise_db}dB:d={min_duration}",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    regions = []
    starts = re.findall(r"silence_start: ([\d.]+)", result.stderr)
    ends = re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", result.stderr)
    
    for s, (e, d) in zip(starts, ends):
        regions.append(SilentRegion(float(s), float(e), float(d)))
        
    return regions
