from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Region:
    start: float  # seconds
    end: float
    action: str   # "keep" or "cut"
    reason: str   # "speech", "silence", "filler"

def merge_intervals(intervals: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Merge overlapping intervals."""
    if not intervals:
        return []
    sorted_iv = sorted(intervals)
    merged = [sorted_iv[0]]
    for start, end in sorted_iv[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged

def build_edl(
    total_duration: float,
    silent_regions: list,      # SilentRegion objects
    filler_regions: list,      # (start, end) tuples
    padding: float = 0.15,     # Keep padding around speech (in seconds)
    min_keep_duration: float = 0.3,  # Don't keep tiny fragments
) -> List[Region]:
    # Collect all cut intervals
    cut_intervals = []
    for sr in silent_regions:
        cut_intervals.append((sr.start, sr.end))
    cut_intervals.extend(filler_regions)
    
    # Merge overlapping cuts
    cut_intervals = merge_intervals(cut_intervals)
    
    # Apply padding (shrink cuts to preserve speech edges)
    padded_cuts = []
    for start, end in cut_intervals:
        s = start + padding
        e = end - padding
        if e > s:
            padded_cuts.append((s, e))
    
    # Build keep regions (inverse of cuts)
    regions = []
    cursor = 0.0
    for cut_start, cut_end in padded_cuts:
        if cut_start > cursor:
            keep_dur = cut_start - cursor
            if keep_dur >= min_keep_duration:
                regions.append(Region(cursor, cut_start, "keep", "speech"))
            else:
                # If too small to keep, just merge it into the cut
                pass
        regions.append(Region(cut_start, cut_end, "cut", "silence/filler"))
        cursor = cut_end
    
    # Final keep region
    if cursor < total_duration:
        keep_dur = total_duration - cursor
        if keep_dur >= min_keep_duration:
            regions.append(Region(cursor, total_duration, "keep", "speech"))
    
    return regions

def build_edl_from_keeps(total_duration: float, keep_regions: List[Tuple[float, float]], padding: float = 0.30) -> List[Region]:
    """Builds an EDL directly from AI-approved keep regions, with padding to prevent edge clipping."""
    # Ensure they are sorted and merged
    keep_regions = merge_intervals(keep_regions)
    
    # Step 1: Add padding to all keep regions and merge them so contiguous clips become one seamless clip without razor cuts
    padded_keeps = []
    for start, end in keep_regions:
        s = max(0.0, start - padding)
        e = min(total_duration, end + padding)
        padded_keeps.append((s, e))
        
    padded_keeps = merge_intervals(padded_keeps)
    
    # Step 2: Build the EDL
    regions = []
    cursor = 0.0
    for s, e in padded_keeps:
        if s > cursor:
            regions.append(Region(cursor, s, "cut", "AI decision: cut"))
        regions.append(Region(s, e, "keep", "AI decision: keep"))
        cursor = e
        
    # Final cut region if there's remaining time
    if cursor < total_duration:
        regions.append(Region(cursor, total_duration, "cut", "AI decision: cut"))
        
    return regions
