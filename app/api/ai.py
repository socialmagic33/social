from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps.auth import get_current_user
from app import models
from app.services.ai_processor import (
    select_media_for_ai,
    generate_prompt_json,
    upload_and_send_to_openai
)
from app.services.post_scheduler import create_post_from_grouping
from app.schemas.post import PostOut
import json

router = APIRouter()

@router.post("/generate-caption/{grouping_id}")
def generate_caption_for_grouping(
    grouping_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Step 1: Fetch the grouping
    grouping = db.query(models.MediaGrouping).filter_by(id=grouping_id).first()
    if not grouping:
        raise HTTPException(status_code=404, detail="MediaGrouping not found")

    # Ensure it belongs to the user
    if grouping.jobsite.owner.id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this grouping")

    # Step 2: Select the media
    try:
        prepared_media = select_media_for_ai(grouping_id, db)
        if not prepared_media:
            raise HTTPException(status_code=400, detail="No valid media available for caption generation")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to prepare media: {str(e)}")

    # Step 3: Prepare the prompt
    contractor_info = {
        "company_name": current_user.company_name or "Your Company",
        "values": current_user.values or "Quality work and customer satisfaction",
        "specialties": current_user.specialties or "General contracting"
    }
    jobsite_address = grouping.jobsite.address
    
    try:
        prompt = generate_prompt_json(prepared_media, contractor_info, jobsite_address)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")

    # Step 4: Send to OpenAI (if API key is configured)
    try:
        ai_response = upload_and_send_to_openai(prepared_media, prompt)
        parsed = json.loads(ai_response)
    except Exception as e:
        # Fallback to basic caption if AI fails
        ai_response = json.dumps({
            "post_text": f"Great progress at {jobsite_address}! Check out our latest work. #construction #progress #quality",
            "hashtags": ["#construction", "#progress", "#quality", "#contractor"],
            "generated_captions": [
                {
                    "media_refs": [1, 2],
                    "text": f"Exciting progress at {jobsite_address}! Our team is delivering quality work."
                }
            ]
        })
        parsed = json.loads(ai_response)

    # Step 5: Store response in grouping
    grouping.generated_caption = parsed.get("post_text", "Check out our latest work!")
    db.commit()

    # Step 6: Auto-create post linked to grouping and jobsite
    post = create_post_from_grouping(grouping, current_user, db)
    post.jobsite_id = grouping.jobsite_id
    db.commit()

    return {
        "message": "Caption generated successfully",
        "output": parsed,
        "post_id": post.id
    }

@router.get("/process-jobsite/{jobsite_id}")
def process_jobsite_media(
    jobsite_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Process all media for a jobsite and create groupings"""
    # Verify jobsite ownership
    jobsite = db.query(models.Jobsite).filter_by(
        id=jobsite_id,
        user_id=current_user.id
    ).first()
    if not jobsite:
        raise HTTPException(status_code=404, detail="Jobsite not found")

    # Get ungrouped media for this jobsite
    ungrouped_media = db.query(models.Media).filter(
        models.Media.jobsite_id == jobsite_id,
        models.Media.grouping_id.is_(None)
    ).all()

    if not ungrouped_media:
        raise HTTPException(status_code=400, detail="No ungrouped media found")

    # Create a new grouping
    grouping = models.MediaGrouping(
        jobsite_id=jobsite_id,
        generated_caption="Processing..."
    )
    db.add(grouping)
    db.flush()

    # Group media by status and quality
    before_media = [m for m in ungrouped_media if m.status.value == "before" and m.star_rating >= 3]
    after_media = [m for m in ungrouped_media if m.status.value == "after" and m.star_rating >= 3]
    progress_media = [m for m in ungrouped_media if m.status.value == "in_progress" and m.star_rating >= 4]

    # Select best media for grouping (max 5 items)
    selected_media = []
    selected_media.extend(before_media[:2])  # Up to 2 before photos
    selected_media.extend(after_media[:2])   # Up to 2 after photos
    selected_media.extend(progress_media[:1]) # Up to 1 progress item

    if not selected_media:
        # If no high-quality media, take the best available
        selected_media = sorted(ungrouped_media, key=lambda x: x.star_rating, reverse=True)[:3]

    # Assign media to grouping
    for media in selected_media:
        media.grouping_id = grouping.id

    db.commit()
    db.refresh(grouping)

    return {
        "message": "Media processed successfully",
        "grouping_id": grouping.id,
        "media_count": len(selected_media)
    }