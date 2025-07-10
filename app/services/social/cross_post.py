from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import Media, SocialAccount
from app.services.social.instagram import post_to_instagram
from app.services.social.facebook import share_to_facebook

class SocialCrossPost:
    def __init__(self, media_grouping_id: int, caption: str, db: Session):
        self.media_grouping_id = media_grouping_id
        self.caption = caption
        self.db = db
        self.platforms = []
        self.results = {}

    def enable_facebook(self):
        """Enable cross-posting to Facebook"""
        self.platforms.append("facebook")

    async def publish(self) -> Dict:
        """Publish content to all enabled platforms"""
        # Always post to Instagram first
        try:
            instagram_result = await post_to_instagram(
                self.db,
                self.media_grouping_id,
                self.caption
            )
            self.results["instagram"] = instagram_result
        except Exception as e:
            self.results["instagram"] = {"error": str(e)}

        # Cross-post to Facebook if enabled
        if "facebook" in self.platforms:
            try:
                fb_result = await share_to_facebook(
                    self.db,
                    self.media_grouping_id,
                    self.caption,
                    instagram_post_id=instagram_result.get("id")
                )
                self.results["facebook"] = fb_result
            except Exception as e:
                self.results["facebook"] = {"error": str(e)}

        return self.results

async def create_social_post(
    db: Session,
    media_grouping_id: int,
    caption: str,
    enable_facebook: bool = True
) -> Dict:
    """Helper function to create and publish social posts"""
    cross_post = SocialCrossPost(media_grouping_id, caption, db)
    
    if enable_facebook:
        cross_post.enable_facebook()
    
    return await cross_post.publish()