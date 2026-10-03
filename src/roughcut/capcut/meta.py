import json
import time
from pathlib import Path
from typing import Dict, Any

def update_root_meta_info(root_meta_path: Path, draft_id: str, project_name: str, 
                          draft_fold_path: str, cover_path: str, root_path: str, 
                          creation_time: int, modify_time: int, duration_us: int):
    """Adds or updates a project in root_meta_info.json."""
    if not root_meta_path.exists():
        data = {"all_draft_store": [], "draft_ids": 0, "root_path": root_path}
    else:
        with open(root_meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    # Check if project already exists
    existing = next((p for p in data.get("all_draft_store", []) if p.get("draft_id") == draft_id), None)
    
    entry = {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "draft_cloud_last_action_download": False,
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": cover_path,
        "draft_fold_path": draft_fold_path,
        "draft_id": draft_id,
        "draft_is_ai_shorts": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_infinite_canvas_draft": False,
        "draft_is_invisible": False,
        "draft_is_pippit_draft": False,
        "draft_is_web_article_video": False,
        "draft_json_file": f"{draft_fold_path}\\draft_content.json".replace("/", "\\"),
        "draft_name": project_name,
        "draft_new_version": "",
        "draft_root_path": root_path,
        "draft_timeline_materials_size": 0,
        "draft_type": "",
        "draft_web_article_video_enter_from": "",
        "pippit_avatar_url": "",
        "pippit_extra_info": "",
        "pippit_id": "",
        "pippit_user_name": "",
        "streaming_edit_draft_ready": True,
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": int(creation_time * 1_000_000),
        "tm_draft_modified": int(modify_time * 1_000_000),
        "tm_draft_removed": 0,
        "tm_duration": duration_us
    }

    if existing:
        existing.update(entry)
    else:
        data.setdefault("all_draft_store", []).insert(0, entry)
        data["draft_ids"] = len(data["all_draft_store"])
        
    with open(root_meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_draft_meta_info(draft_id: str, project_name: str, draft_fold_path: str,
                             root_path: str, creation_time: int, duration_us: int) -> Dict[str, Any]:
    return {
        "cloud_draft_cover": False,
        "cloud_draft_sync": False,
        "cloud_package_completed_time": "",
        "draft_cloud_capcut_purchase_info": "",
        "draft_cloud_last_action_download": False,
        "draft_cloud_package_type": "",
        "draft_cloud_purchase_info": "",
        "draft_cloud_template_id": "",
        "draft_cloud_tutorial_info": "",
        "draft_cloud_videocut_purchase_info": "",
        "draft_cover": "draft_cover.jpg",
        "draft_deeplink_url": "",
        "draft_enterprise_info": {
            "draft_enterprise_extra": "",
            "draft_enterprise_id": "",
            "draft_enterprise_name": "",
            "enterprise_material": []
        },
        "draft_fold_path": draft_fold_path,
        "draft_id": draft_id,
        "draft_is_ae_produce": False,
        "draft_is_ai_packaging_used": False,
        "draft_is_ai_shorts": False,
        "draft_is_ai_translate": False,
        "draft_is_article_video_draft": False,
        "draft_is_cloud_temp_draft": False,
        "draft_is_from_deeplink": "false",
        "draft_is_infinite_canvas_draft": False,
        "draft_is_invisible": False,
        "draft_is_pippit_draft": False,
        "draft_is_web_article_video": False,
        "draft_materials": [
            {"type": 0, "value": []},
            {"type": 1, "value": []},
            {"type": 2, "value": []},
            {"type": 3, "value": []},
            {"type": 6, "value": []},
            {"type": 7, "value": []},
            {"type": 8, "value": []}
        ],
        "draft_materials_copied_info": [],
        "draft_name": project_name,
        "draft_need_rename_folder": False,
        "draft_new_version": "",
        "draft_removable_storage_device": "",
        "draft_root_path": root_path,
        "draft_segment_extra_info": [],
        "draft_timeline_materials_size_": 0,
        "draft_type": "",
        "draft_web_article_video_enter_from": "",
        "pippit_avatar_url": "",
        "pippit_extra_info": "",
        "pippit_id": "",
        "pippit_user_name": "",
        "tm_draft_cloud_completed": "",
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_modified": 0,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": -1,
        "tm_draft_cloud_user_id": -1,
        "tm_draft_create": int(creation_time * 1_000_000),
        "tm_draft_modified": int(time.time() * 1_000_000),
        "tm_draft_removed": 0,
        "tm_duration": duration_us
    }

def generate_draft_settings(creation_time: int, duration_us: int) -> str:
    modify_time = int(time.time())
    return f"""[General]
draft_create_time={creation_time}
draft_last_edit_time={modify_time}
real_edit_seconds=0
real_edit_keys=0
cloud_last_modify_platform=windows
"""
