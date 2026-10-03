import os
from typing import List, Tuple
from dataclasses import dataclass
from pydantic import BaseModel
from google import genai
from google.genai import types
from roughcut.analyzer.diarize import DiarizedSegment

class KeepSegment(BaseModel):
    start: float
    end: float
    reason: str

class EditDecisionList(BaseModel):
    keep_segments: list[KeepSegment]

def get_ai_director_decisions(
    fine_segments: List[Tuple[float, float, str]],
    gemini_key: str
) -> List[Tuple[float, float]]:
    """
    Sends the fine-grained transcript to Gemini to act as an AI director.
    Returns a list of (start, end) tuples of regions to KEEP.
    """
    if not gemini_key:
        raise ValueError("Gemini API key is required for AI Director mode.")

    client = genai.Client(api_key=gemini_key)
    
    # Build transcript for the LLM using the fine-grained timestamps
    transcript_text = "--- RAW STUDIO TRANSCRIPT ---\n"
    for start, end, text in fine_segments:
        if text.strip():
            transcript_text += f"[{start:.1f} - {end:.1f}] {text}\n"

    # Save transcript for debugging
    with open("ai_transcript_debug.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)

    system_instruction = (
        "You are an expert video editor assembling a seamless final cut from a raw studio recording. \n\n"
        "The transcript contains everything spoken in the room: the talent's good takes, their mistakes, and off-topic crew chatter (like 'action', 'stop', or resetting).\n\n"
        "Your objective is to stitch together a single, fluent, continuous take of the talent's message. \n\n"
        "CRITICAL RULES:\n"
        "1. ELIMINATE DUPLICATES & MISTAKES: If the talent messes up and restarts a sentence/phrase, cut out all the failed attempts. Only keep the final, complete take of that phrase.\n"
        "2. REMOVE OFF-TOPIC CHATTER: Completely drop any segments where someone says 'action', 'stop', or off-topic conversation.\n"
        "3. DO NOT MISS ANY SIGNIFICANT WORDS: Make sure your kept regions span the entirety of the good take so no words are chopped.\n"
        "4. OUTPUT TIMESTAMPS: You must output the exact 'start' and 'end' timestamps of the regions you want to KEEP. You may combine contiguous good segments into a single larger keep block (e.g. if [1.0-3.0] and [3.0-5.0] are both good, just output [1.0 - 5.0]).\n\n"
        "Output the list of KEEP regions to form the final, duplicate-free video."
    )

    print("Asking AI Director (Gemini 3.8 Flash) for edit decisions...")
    
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    from google.genai.errors import APIError

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=20),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda retry_state: print(f"API Error (High Demand). Retrying in {retry_state.next_action.sleep}s...")
    )
    def call_gemini():
        return client.models.generate_content(
            model='gemini-3.8-flash',
            contents=transcript_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=EditDecisionList,
                temperature=0.1,
            ),
        )

    response = call_gemini()
    
    # Parse the output
    import json
    result_dict = json.loads(response.text)
    
    # Save the AI response for debugging
    with open("ai_response_debug.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)
    
    keep_regions = []
    print("\n--- AI Director Decisions ---")
    for keep in result_dict.get("keep_segments", []):
        start = float(keep['start'])
        end = float(keep['end'])
        print(f"KEEP [{start:.1f} - {end:.1f}] ({keep['reason']})")
        keep_regions.append((start, end))
    print("-----------------------------\n")
    
    return keep_regions
