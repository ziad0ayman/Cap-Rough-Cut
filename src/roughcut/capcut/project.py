import json
import time
import os
import shutil
from pathlib import Path
from typing import Dict, Any

from .schema import (
    new_uuid, make_video_material, make_segment, make_speed,
    make_canvas, make_placeholder_info, make_sound_channel_mapping,
    make_material_color, make_vocal_separation
)
from .meta import update_root_meta_info, generate_draft_meta_info, generate_draft_settings

# Hardcode the platform block from the user's project
PLATFORM_DATA = {
    "os": "windows",
    "os_version": "10.0.26200",
    "app_id": 359289,
    "app_version": "9.3.0",
    "app_source": "cc",
    "device_id": "23881e6b9d562347871eb4fcd125b7c2",
    "hard_disk_id": "6bfb574a68475aba99740167b8bf9002",
    "mac_address": "2ef00f20b17b20906f3a4fe9541cdf97,77281d7a2009f9746abd0b7679189084"
}

class CapCutProjectGenerator:
    def __init__(self, project_name: str, drafts_dir: str, media_info: dict):
        self.project_name = project_name
        self.root_path = Path(drafts_dir)
        self.output_dir = self.root_path / project_name
        self.media = media_info
        
        self.draft_id = new_uuid()
        self.creation_time = int(time.time())
        self.total_duration_us = 0
        
        self.segments = []
        self.materials = {
            "videos": [],
            "speeds": [],
            "canvases": [],
            "placeholder_infos": [],
            "sound_channel_mappings": [],
            "material_colors": [],
            "vocal_separations": []
        }
        
    def add_keep_region(self, source_start_us: int, duration_us: int, timeline_start_us: int):
        mat_id = new_uuid()
        speed_id = new_uuid()
        canvas_id = new_uuid()
        ph_id = new_uuid()
        scm_id = new_uuid()
        mc_id = new_uuid()
        vs_id = new_uuid()
        
        video_name = os.path.basename(self.media["path"])
        
        self.materials["videos"].append(make_video_material(
            mat_id, self.media["path"], self.media["duration_us"], 
            self.media["width"], self.media["height"], video_name
        ))
        self.materials["speeds"].append(make_speed(speed_id))
        self.materials["canvases"].append(make_canvas(canvas_id))
        self.materials["placeholder_infos"].append(make_placeholder_info(ph_id))
        self.materials["sound_channel_mappings"].append(make_sound_channel_mapping(scm_id))
        self.materials["material_colors"].append(make_material_color(mc_id))
        self.materials["vocal_separations"].append(make_vocal_separation(vs_id))
        
        extra_refs = [speed_id, ph_id, canvas_id, scm_id, mc_id, vs_id]
        seg_id = new_uuid()
        self.segments.append(make_segment(
            seg_id, mat_id, extra_refs, source_start_us, duration_us, timeline_start_us
        ))

    def build_from_edl(self, edl: list):
        timeline_cursor_us = 0
        for region in edl:
            if region.action == "keep":
                src_start_us = int(region.start * 1_000_000)
                dur_us = int((region.end - region.start) * 1_000_000)
                
                self.add_keep_region(src_start_us, dur_us, timeline_cursor_us)
                timeline_cursor_us += dur_us
                
        self.total_duration_us = timeline_cursor_us

    def _build_draft_content(self) -> Dict[str, Any]:
        track_id = new_uuid()
        return {
            "id": self.draft_id,
            "version": 360000,
            "new_version": "183.0.0",
            "name": "",
            "duration": self.total_duration_us,
            "create_time": 0,
            "update_time": 0,
            "fps": self.media["fps"],
            "is_drop_frame_timecode": False,
            "color_space": 0,
            "config": {
                "video_mute": False,
                "record_audio_last_index": 1,
                "extract_audio_last_index": 1,
                "original_sound_last_index": 1,
                "subtitle_sync": True,
                "lyrics_sync": True,
                "voice_change_sync": False,
                "material_save_mode": 0
            },
            "canvas_config": {
                "ratio": "original",
                "width": self.media["width"],
                "height": self.media["height"],
                "background": None
            },
            "tracks": [
                {
                    "id": track_id,
                    "type": "video",
                    "segments": self.segments,
                    "flag": 0,
                    "attribute": 0,
                    "name": "",
                    "is_default_name": True
                }
            ],
            "group_container": None,
            "materials": self.materials,
            "keyframes": {
                "videos": [], "audios": [], "texts": [], "stickers": [],
                "filters": [], "adjusts": [], "handwrites": [], "effects": []
            },
            "keyframe_graph_list": [],
            "platform": PLATFORM_DATA,
            "last_modified_platform": PLATFORM_DATA,
            "mutable_config": None,
            "cover": None,
            "retouch_cover": None,
            "extra_info": None,
            "relationships": [],
            "mixed_track_mode_on": False,
            "render_index_track_mode_on": False,
            "free_render_index_mode_on": False,
            "static_cover_image_path": "",
            "source": "default",
            "time_marks": None,
            "path": "",
            "lyrics_effects": [],
            "uneven_animation_template_info": {
                "composition": "", "content": "", "order": "", "sub_template_info_list": []
            },
            "draft_type": "video",
            "smart_ads_info": {"page_from": "", "routine": "", "draft_url": ""},
            "function_assistant_info": {}
        }

    def save(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. draft_content.json
        draft_content = self._build_draft_content()
        with open(self.output_dir / "draft_content.json", "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False, indent=2)
            
        # 2. draft_meta_info.json
        meta_info = generate_draft_meta_info(
            self.draft_id, self.project_name, str(self.output_dir).replace("\\", "/"),
            str(self.root_path).replace("\\", "/"), self.creation_time, self.total_duration_us
        )
        
        # Populate draft_materials in meta_info with all our imported videos
        # Video is type 0
        imported_videos = []
        for vid in self.materials["videos"]:
            imported_videos.append({
                "id": new_uuid(), # Different ID in meta info usually, but can be new
                "file_Path": vid["path"],
                "extra_info": vid["material_name"],
                "duration": vid["duration"],
                "width": vid["width"],
                "height": vid["height"],
                "metetype": "video",
                "create_time": self.creation_time,
                "import_time": int(time.time()),
                "import_time_ms": int(time.time() * 1_000_000),
                "item_source": 1,
                "type": 0,
                "roughcut_time_range": {"start": 0, "duration": vid["duration"]},
                "sub_time_range": {"start": -1, "duration": -1}
            })
        meta_info["draft_materials"][0]["value"] = imported_videos

        with open(self.output_dir / "draft_meta_info.json", "w", encoding="utf-8") as f:
            json.dump(meta_info, f, ensure_ascii=False, indent=2)
            
        # 3. draft_settings
        settings = generate_draft_settings(self.creation_time, self.total_duration_us)
        with open(self.output_dir / "draft_settings", "w", encoding="utf-8") as f:
            f.write(settings)
            
        # 4. update root_meta_info.json
        root_meta_path = self.root_path / "root_meta_info.json"
        cover_path = f"{str(self.output_dir).replace(chr(92), '/')}/draft_cover.jpg"
        
        # Create a dummy cover image (just a black pixel or copy an existing one if possible)
        # We will just write an empty file for now, CapCut usually regenerates it if corrupted.
        Path(cover_path).touch()
        
        update_root_meta_info(
            root_meta_path, self.draft_id, self.project_name, 
            str(self.output_dir).replace("\\", "/"), cover_path, 
            str(self.root_path).replace("\\", "/"),
            self.creation_time, int(time.time()), self.total_duration_us
        )
        
        print(f"Project '{self.project_name}' generated successfully at {self.output_dir}")
