import uuid
import os

def new_uuid() -> str:
    return str(uuid.uuid4()).upper()

def make_video_material(mat_id: str, path: str, duration_us: int,
                        width: int, height: int, name: str) -> dict:
    return {
        "id": mat_id,
        "unique_id": "",
        "type": "video",
        "duration": duration_us,
        "path": path.replace("\\", "/"),
        "media_path": "",
        "local_id": "",
        "has_audio": True,
        "reverse_path": "",
        "intensifies_path": "",
        "reverse_intensifies_path": "",
        "intensifies_audio_path": "",
        "cartoon_path": "",
        "width": width,
        "height": height,
        "category_id": "",
        "category_name": "",
        "material_id": "",
        "material_name": name,
        "material_url": "",
        "crop": {
            "upper_left_x": 0.0,
            "upper_left_y": 0.0,
            "upper_right_x": 1.0,
            "upper_right_y": 0.0,
            "lower_left_x": 0.0,
            "lower_left_y": 1.0,
            "lower_right_x": 1.0,
            "lower_right_y": 1.0
        },
        "crop_ratio": "free",
        "audio_fade": None,
        "crop_scale": 1.0,
        "extra_type_option": 0,
        "stable": {
            "stable_level": 0,
            "matrix_path": "",
            "time_range": {"start": 0, "duration": 0}
        },
        "matting": {
            "flag": 0,
            "path": "",
            "interactiveTime": [],
            "has_use_quick_brush": False,
            "strokes": [],
            "has_use_quick_eraser": False,
            "expansion": 0,
            "feather": 0,
            "reverse": False,
            "custom_matting_id": "",
            "enable_matting_stroke": False,
            "is_clould": False,
            "mask_video_path": "",
            "cloud_product_fps": 0.0
        },
        "source": 0,
        "source_platform": 0,
        "formula_id": "",
        "check_flag": 62978047,
        "video_algorithm": {
            "algorithms": [],
            "time_range": None,
            "path": "",
            "gameplay_configs": [],
            "ai_in_painting_config": [],
            "complement_frame_config": None,
            "motion_blur_config": None,
            "deflicker": None,
            "noise_reduction": None,
            "quality_enhance": None,
            "super_resolution": None,
            "ai_background_configs": [],
            "smart_complement_frame": None,
            "aigc_generate": None,
            "aigc_generate_list": [],
            "mouth_shape_driver": None,
            "ai_expression_driven": None,
            "ai_motion_driven": None,
            "image_interpretation": None,
            "story_video_modify_video_config": {
                "task_id": "",
                "is_overwrite_last_video": False,
                "tracker_task_id": "",
                "generate_id": "",
                "generate_card_id": ""
            },
            "skip_algorithm_index": []
        },
        "is_unified_beauty_mode": False,
        "is_set_beauty_mode": False,
        "object_locked": None,
        "smart_motion": None,
        "multi_camera_info": None,
        "freeze": None,
        "picture_from": "none",
        "picture_set_category_id": "",
        "picture_set_category_name": "",
        "team_id": "",
        "local_material_id": "",
        "origin_material_id": "",
        "request_id": "",
        "has_sound_separated": False,
        "is_text_edit_overdub": False,
        "is_ai_generate_content": False,
        "aigc_type": "none",
        "is_copyright": False,
        "aigc_history_id": "",
        "aigc_item_id": "",
        "local_material_from": "",
        "smart_match_info": None,
        "beauty_face_preset_infos": [],
        "beauty_body_preset_id": "",
        "beauty_face_auto_preset": {
            "preset_id": "",
            "name": "",
            "rate_map": "",
            "scene": ""
        },
        "beauty_face_auto_preset_infos": [],
        "beauty_body_auto_preset": None,
        "live_photo_timestamp": -1,
        "live_photo_cover_path": "",
        "content_feature_info": None,
        "corner_pin": None,
        "surface_trackings": [],
        "video_mask_stroke": {
            "resource_id": "",
            "path": "",
            "type": "",
            "color": "",
            "size": 0.0,
            "alpha": 0.0,
            "distance": 0.0,
            "texture": 0.0,
            "horizontal_shift": 0.0,
            "vertical_shift": 0.0
        },
        "video_mask_shadow": {
            "resource_id": "",
            "path": "",
            "color": "",
            "alpha": 0.0,
            "blur": 0.0,
            "distance": 0.0,
            "angle": 0.0
        },
        "pre_applied_vip_materials": [],
        "workflow_node_id": ""
    }

def make_segment(seg_id: str, mat_id: str, extra_refs: list[str],
                 source_start_us: int, duration_us: int,
                 timeline_start_us: int) -> dict:
    return {
        "id": seg_id,
        "source_timerange": {
            "start": source_start_us,
            "duration": duration_us
        },
        "target_timerange": {
            "start": timeline_start_us,
            "duration": duration_us
        },
        "render_timerange": {
            "start": 0,
            "duration": 0
        },
        "desc": "",
        "state": 0,
        "speed": 1.0,
        "is_loop": False,
        "is_tone_modify": False,
        "reverse": False,
        "intensifies_audio": False,
        "cartoon": False,
        "volume": 1.0,
        "last_nonzero_volume": 1.0,
        "clip": {
            "scale": {"x": 1.0, "y": 1.0},
            "rotation": 0.0,
            "transform": {"x": 0.0, "y": 0.0},
            "flip": {"vertical": False, "horizontal": False},
            "alpha": 1.0
        },
        "uniform_scale": {"on": True, "value": 1.0},
        "material_id": mat_id,
        "extra_material_refs": extra_refs,
        "render_index": 0,
        "keyframe_refs": [],
        "enable_lut": True,
        "enable_adjust": True,
        "enable_hsl": False,
        "visible": True,
        "group_id": "",
        "enable_color_curves": True,
        "enable_hsl_curves": True,
        "track_render_index": 0,
        "hdr_settings": {"mode": 1, "intensity": 1.0, "nits": 1000},
        "enable_color_wheels": True,
        "track_attribute": 0,
        "is_placeholder": False,
        "template_id": "",
        "enable_smart_color_adjust": False,
        "template_scene": "default",
        "common_keyframes": [],
        "caption_info": None,
        "responsive_layout": {
            "enable": False,
            "target_follow": "",
            "size_layout": 0,
            "horizontal_pos_layout": 0,
            "vertical_pos_layout": 0
        },
        "enable_color_match_adjust": False,
        "enable_color_correct_adjust": False,
        "enable_adjust_mask": False,
        "raw_segment_id": "",
        "lyric_keyframes": None,
        "enable_video_mask": True,
        "digital_human_template_group_id": "",
        "color_correct_alg_result": "",
        "source": "segmentsourcenormal",
        "enable_mask_stroke": False,
        "enable_mask_shadow": False,
        "enable_color_adjust_pro": False,
        "segment_color_tag": ""
    }

def make_speed(speed_id: str) -> dict:
    return {"id": speed_id, "type": "speed", "mode": 0, "speed": 1.0, "curve_speed": None}

def make_canvas(canvas_id: str) -> dict:
    return {"id": canvas_id, "type": "canvas_color", "color": "", "blur": 0.0,
            "image": "", "album_image": "", "image_id": "", "image_name": "",
            "source_platform": 0, "team_id": ""}

def make_placeholder_info(ph_id: str) -> dict:
    return {"id": ph_id, "type": "placeholder_info", "meta_type": "none",
            "res_path": "", "res_text": "", "error_path": "", "error_text": ""}

def make_sound_channel_mapping(scm_id: str) -> dict:
    return {"id": scm_id, "type": "", "audio_channel_mapping": 0, "is_config_open": False}

def make_material_color(mc_id: str) -> dict:
    return {"id": mc_id, "is_color_clip": False, "is_gradient": False,
            "solid_color": "", "gradient_colors": [], "gradient_percents": [],
            "gradient_angle": 90.0, "width": 0.0, "height": 0.0}

def make_vocal_separation(vs_id: str) -> dict:
    return {"id": vs_id, "type": "vocal_separation", "choice": 0,
            "removed_sounds": [], "time_range": None, "production_path": "",
            "final_algorithm": "", "enter_from": ""}
