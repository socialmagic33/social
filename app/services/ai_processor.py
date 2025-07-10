import os
import json
from typing import List, Dict
from sqlalchemy.orm import Session
from app import models
from app.config import settings
import openai

def select_media_for_ai(grouping_id: int, db: Session) -> List[Dict]:
    """Select and prepare media for AI processing"""
    grouping = db.query(models.MediaGrouping).filter_by(id=grouping_id).first()
    if not grouping:
        raise ValueError("MediaGrouping not found")

    media_items = grouping.media

    # Categorize media
    before_photos = [m for m in media_items if m.status.value == "before" and m.file_url.lower().endswith((".jpg", ".jpeg", ".png"))]
    after_photos = [m for m in media_items if m.status.value == "after" and m.file_url.lower().endswith((".jpg", ".jpeg", ".png"))]
    progress_photos = [m for m in media_items if m.status.value == "in_progress" and m.file_url.lower().endswith((".jpg", ".jpeg", ".png"))]
    videos = [m for m in media_items if m.file_url.lower().endswith((".mp4", ".mov", ".webm"))]

    # Select best media (prioritize high ratings)
    selected_media = []
    
    # Add best before photos
    before_sorted = sorted(before_photos, key=lambda x: x.star_rating, reverse=True)
    selected_media.extend(before_sorted[:2])
    
    # Add best after photos
    after_sorted = sorted(after_photos, key=lambda x: x.star_rating, reverse=True)
    selected_media.extend(after_sorted[:2])
    
    # Add best progress photo
    if progress_photos:
        progress_sorted = sorted(progress_photos, key=lambda x: x.star_rating, reverse=True)
        selected_media.extend(progress_sorted[:1])
    
    # Add best video if available
    if videos:
        video_sorted = sorted(videos, key=lambda x: x.star_rating, reverse=True)
        selected_media.extend(video_sorted[:1])

    # Prepare media data
    prepared_media = []
    for index, media in enumerate(selected_media, start=1):
        prepared_media.append({
            "file_number": index,
            "file_path": media.file_url,
            "status": media.status.value,
            "description": media.description or "",
            "notes": media.notes or "",
            "star_rating": media.star_rating,
            "media_type": "video" if media.file_url.lower().endswith((".mp4", ".mov", ".webm")) else "image",
        })

    return prepared_media

def generate_prompt_json(prepared_media: List[Dict], contractor_info: Dict, jobsite_address: str) -> str:
    """Generate a structured prompt for AI processing"""
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
                "star_rating": m.get("star_rating", 0),
                "media_type": m.get("media_type", "image")
            } for m in prepared_media
        ],
        "instructions": "Generate engaging social media content that showcases the contractor's work quality and professionalism. Include relevant hashtags and mention the progress or completion status.",
        "output_format": {
            "post_text": "Main caption for the post",
            "hashtags": ["#tag1", "#tag2"],
            "generated_captions": [
                {
                    "media_refs": [1, 2],
                    "text": "Caption describing specific media"
                }
            ]
        }
    }

    return json.dumps(prompt_data, indent=2)

def upload_and_send_to_openai(prepared_media: List[Dict], prompt: str) -> str:
    """Send media and prompt to OpenAI for processing"""
    openai_api_key = settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else None
    
    if not openai_api_key:
        # Return a fallback response if OpenAI is not configured
        return generate_fallback_response(prepared_media, prompt)
    
    try:

        openai.api_key = openai_api_key
        
        # Parse the prompt to get context
        prompt_data = json.loads(prompt)
        contractor_info = prompt_data.get("contractor_info", {})
        jobsite = prompt_data.get("jobsite", {})
        media_group = prompt_data.get("media_group", [])
        
        # Create a text-based prompt since we're storing files in database
        text_prompt = f"""
        Create social media content for {contractor_info.get('company_name', 'a contractor')}.
        
        Company Values: {contractor_info.get('values', 'Quality work')}
        Specialties: {contractor_info.get('specialties', 'General contracting')}
        Jobsite: {jobsite.get('address', 'Current project')}
        
        Media included:
        """
        
        for media in media_group:
            text_prompt += f"\n- {media['media_type'].title()} {media['file_number']}: {media['status']} - {media['description']} (Rating: {media['star_rating']}/5)"
        
        text_prompt += "\n\nGenerate engaging social media content in JSON format with post_text, hashtags, and generated_captions."
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a social media expert for contractors. Create engaging, professional content that showcases quality work. Always respond in valid JSON format."
                },
                {"role": "user", "content": text_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        return response.choices[0].message.content
        
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return generate_fallback_response(prepared_media, prompt)

def generate_fallback_response(prepared_media: List[Dict], prompt: str) -> str:
    """Generate a fallback response when OpenAI is not available"""
    try:
        prompt_data = json.loads(prompt)
        contractor_info = prompt_data.get("contractor_info", {})
        jobsite = prompt_data.get("jobsite", {})
        media_group = prompt_data.get("media_group", [])
    except:
        contractor_info = {"company_name": "Our Team"}
        jobsite = {"address": "the jobsite"}
        media_group = prepared_media

    company_name = contractor_info.get("company_name", "Our Team")
    address = jobsite.get("address", "this project")
    
    # Count media types
    before_count = len([m for m in media_group if m.get("status") == "before"])
    after_count = len([m for m in media_group if m.get("status") == "after"])
    progress_count = len([m for m in media_group if m.get("status") == "in_progress"])
    
    # Generate appropriate caption based on media
    if before_count and after_count:
        post_text = f"Amazing transformation at {address}! Check out the before and after shots of our latest project. {company_name} delivers quality results every time. 💪 #transformation #quality #construction"
    elif after_count:
        post_text = f"Project complete at {address}! Another successful job by {company_name}. We're proud of the quality work our team delivers. ✅ #projectcomplete #quality #construction"
    elif progress_count:
        post_text = f"Great progress at {address}! Our team at {company_name} is working hard to deliver exceptional results. Stay tuned for the final reveal! 🚧 #progress #construction #quality"
    else:
        post_text = f"Exciting work happening at {address}! {company_name} is committed to delivering the highest quality results. #construction #quality #professional"

    hashtags = [
        "#construction", "#contractor", "#quality", "#professional",
        "#renovation", "#building", "#craftsmanship", "#excellence"
    ]

    # Add location-based hashtag if possible
    if "street" in address.lower() or "ave" in address.lower() or "road" in address.lower():
        hashtags.append("#localcontractor")

    response = {
        "post_text": post_text,
        "hashtags": hashtags[:8],  # Limit to 8 hashtags
        "generated_captions": [
            {
                "media_refs": list(range(1, len(media_group) + 1)),
                "text": post_text
            }
        ]
    }

    return json.dumps(response, indent=2)
