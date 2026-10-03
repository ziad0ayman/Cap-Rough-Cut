import os
from roughcut.analyzer.media import get_media_info
from roughcut.edl.builder import Region
from roughcut.capcut.project import CapCutProjectGenerator

def test_generate_dummy_project():
    # Use one of the user's files to test
    video_path = r"C:\Users\zezok\Downloads\27.mp4"
    if not os.path.exists(video_path):
        print(f"Skipping, video not found: {video_path}")
        return
        
    print(f"Extracting media info from {video_path}...")
    media_info = get_media_info(video_path)
    print("Media info:", media_info)
    
    drafts_dir = r"C:\Users\zezok\AppData\Local\CapCut\User Data\Projects\com.lveditor.draft"
    project_name = "Automated_Rough_Cut_Test"
    
    print(f"Generating project {project_name}...")
    generator = CapCutProjectGenerator(project_name, drafts_dir, media_info)
    
    # Create a dummy EDL: Keep 0-2s, Cut 2-4s, Keep 4-end
    total_sec = media_info["duration_us"] / 1_000_000
    edl = [
        Region(0.0, 2.0, "keep", "speech"),
        Region(2.0, 4.0, "cut", "silence"),
        Region(4.0, total_sec, "keep", "speech")
    ]
    
    generator.build_from_edl(edl)
    generator.save()
    print("Done! You can now check if it loads in CapCut.")

if __name__ == "__main__":
    test_generate_dummy_project()
