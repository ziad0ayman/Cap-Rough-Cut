import os
import subprocess
import tempfile
from pathlib import Path
from roughcut.pipeline import process_video
from roughcut.analyzer.media import get_media_info
from roughcut.analyzer.silence import detect_silence

def test_silence_pipeline_synthetic_video(tmp_path):
    # Create a synthetic video with ffmpeg: 2s tone, 2s silence, 2s tone (6 seconds total)
    video_path = tmp_path / "synthetic_test.mp4"
    drafts_dir = tmp_path / "CapCutDrafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate test video
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=6:r=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-filter_complex", "[1:a][2:a][3:a]concat=n=3:v=0:a=1[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", str(video_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    assert video_path.exists()
    
    # Verify media info
    info = get_media_info(str(video_path))
    assert info["width"] == 320
    assert info["height"] == 240
    assert info["fps"] == 30.0
    
    # Verify silence detection
    silences = detect_silence(str(video_path), noise_db=-30.0, min_duration=0.5)
    assert len(silences) >= 1
    
    # Run full pipeline in silence mode
    project_name = "Test_Synthetic_Project"
    process_video(
        video_path=str(video_path),
        output_dir=str(drafts_dir),
        project_name=project_name,
        mode="silence",
        threshold=-30.0,
        min_silence=0.5
    )
    
    project_folder = drafts_dir / project_name
    assert project_folder.exists()
    assert (project_folder / "draft_content.json").exists()
    assert (project_folder / "draft_meta_info.json").exists()
    assert (project_folder / "draft_settings").exists()
    assert (drafts_dir / "root_meta_info.json").exists()
