import os
import openai
import json
from typing import List, Dict
from sqlalchemy.orm import Session
from app import models


def select_media_for_ai(grouping_id: int, db: Session) -> List[Dict]:
    grouping = db.query(models.MediaGrouping).filter_by(id=grouping_id).first()
    if not grouping:
        raise ValueError("MediaGrouping not found")

    media_items = grouping.media

    before_photos = [m for m in media_items if m.status == "before" and m.file_url.lower().endswith((".jpg", ".jpeg", ".png"))]
    after_photos = [m for m in media_items if m.status == "after" and m.file_url.lower().endswith((".jpg", ".jpeg", ".png"))]
    videos = [m for m in media_items if m.file_url.lower().endswith((".mp4", ".mov", ".webm"))]

    selected_media = before_photos[:2] + after_photos[:2]
    if videos:
        selected_media.append(videos[0])

    prepared_media = []
    for index, media in enumerate(selected_media, start=1):
        prepared_media.append({
            "file_number": index,
            "file_path": media.file_url,
            "status": media.status,
            "description": media.description,
            "notes": media.notes,
            "star_rating": media.star_rating,
            "media_type": "video" if media.file_url.lower().endswith((".mp4", ".mov", ".webm")) else "image",
        })

    return prepared_media


def generate_prompt_json(prepared_media: List[Dict], contractor_info: Dict, jobsite_address: str) -> str:
    prompt_data = {
        "contractor_info": {
            "company_name": contractor_info.get("company_name", ""),
            "values": contractor_info.get("values", ""),
            "specialties": contractor_info.get("specialties", "")
        },
        "jobsite": {
            "address": jobsite_address
        },
        "media_group": [
            {
                "file_number": m["file_number"],
                "status": m["status"],
                "description": m.get("description", ""),
                "notes": m.get("notes", ""),
                "star_rating": m.get("star_rating", 0)
            } for m in prepared_media
        ],
        "output_format": {
            "generated_captions": [
                {
                    "media_refs": [],
                    "text": ""
                }
            ],
            "hashtags": [],
            "post_text": ""
        }
    }

    return json.dumps(prompt_data, indent=2)


def upload_and_send_to_openai(prepared_media: List[Dict], prompt: str) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")

    file_handles = []
    try:
        for item in prepared_media:
            full_path = item["file_path"]
            if not os.path.isfile(full_path):
                raise FileNotFoundError(f"Media file not found: {full_path}")
            file_handles.append(open(full_path, "rb"))

        system_prompt = (
            "You are an expert social media assistant for contractors. "
            "Write captions for this set of media to be used on social media. "
            "Refer to the media by upload order (Photo 1, Photo 2, etc). "
            "Respond using the provided JSON format only. Do not include extra text or headers."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            files=file_handles,
            temperature=0.7,
        )

        return response.choices[0].message.content
    finally:
        for f in file_handles:
            f.close()
