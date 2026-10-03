from dataclasses import dataclass
from typing import List, Tuple
from roughcut.analyzer.diarize import DiarizedSegment

@dataclass
class Take:
    text: str
    start: float
    end: float
    take_number: int
    is_best: bool
    group_id: int

def detect_repeated_takes(
    talent_segments: List[DiarizedSegment],
    similarity_threshold: float = 0.65,
    min_segment_words: int = 3,
) -> List[Take]:
    """
    Detects repeated takes by comparing sequential talent segments
    using fuzzy text matching. Keeps the LAST attempt of a repeated sequence.
    """
    from rapidfuzz import fuzz
    import re
    
    if not talent_segments:
        return []
    
    def normalize(text: str) -> str:
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    # Step 1: Build content blocks from consecutive segments
    blocks = []
    current_block_segs = [talent_segments[0]]
    
    for i in range(1, len(talent_segments)):
        gap = talent_segments[i].start - talent_segments[i-1].end
        if gap > 3.0:  # >3s gap = new block
            blocks.append(current_block_segs)
            current_block_segs = [talent_segments[i]]
        else:
            current_block_segs.append(talent_segments[i])
    blocks.append(current_block_segs)
    
    # Step 2: Create raw Take objects
    raw_takes = []
    for block_segs in blocks:
        merged_text = " ".join(s.text for s in block_segs)
        if len(merged_text.split()) < min_segment_words:
            continue
        raw_takes.append(Take(
            text=merged_text,
            start=block_segs[0].start,
            end=block_segs[-1].end,
            take_number=1,
            is_best=True,
            group_id=-1,
        ))
    
    # Step 3: Sequential fuzzy matching
    group_counter = 0
    assigned = [False] * len(raw_takes)
    
    for i in range(len(raw_takes)):
        if assigned[i]:
            continue
            
        norm_i = normalize(raw_takes[i].text)
        group = [i]
        
        # Look ahead up to 5 blocks
        for j in range(i + 1, min(i + 6, len(raw_takes))):
            if assigned[j]:
                continue
            norm_j = normalize(raw_takes[j].text)
            
            score = max(
                fuzz.token_sort_ratio(norm_i, norm_j) / 100.0,
                fuzz.partial_ratio(norm_i, norm_j) / 100.0,
            )
            
            if score >= similarity_threshold:
                group.append(j)
                assigned[j] = True
        
        # Assign group IDs and mark best take
        if len(group) > 1:
            for idx in group:
                raw_takes[idx].group_id = group_counter
                raw_takes[idx].is_best = (idx == group[-1])  # Last is best
                raw_takes[idx].take_number = group.index(idx) + 1
            group_counter += 1
            assigned[i] = True
        else:
            raw_takes[i].group_id = group_counter
            raw_takes[i].is_best = True
            raw_takes[i].take_number = 1
            group_counter += 1
            
    return raw_takes

def get_bad_take_regions(takes: List[Take]) -> List[Tuple[float, float]]:
    """Returns time regions of bad takes (to be cut)."""
    return [(t.start, t.end) for t in takes if not t.is_best]
