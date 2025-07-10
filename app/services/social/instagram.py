from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import requests
from app.models import Media, SocialAccount
from app.config import settings
from app.core.cache import cache_get, cache_set

class InstagramAPI:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.api_version = "v18.0"
        self.base_url = f"https://graph.instagram.com/{self.api_version}"

    async def create_container(self, media_url: str, caption: str) -> Dict:
        """Create a media container for Instagram"""
        url = f"{self.base_url}/media"
        params = {
            "access_token": self.access_token,
            "image_url": media_url,
            "caption": caption
        }
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()

    async def create_carousel_container(self, media_urls: List[str], caption: str) -> Dict:
        """Create a carousel container for multiple media items"""
        url = f"{self.base_url}/media"
        children = []
        
        # Create child containers first
        for media_url in media_urls:
            params = {
                "access_token": self.access_token,
                "image_url": media_url,
                "is_carousel_item": True
            }
            response = requests.post(url, params=params)
            response.raise_for_status()
            children.append(response.json()["id"])

        # Create carousel container
        params = {
            "access_token": self.access_token,
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption
        }
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()

    async def create_reel(self, video_url: str, caption: str, thumbnail_url: Optional[str] = None) -> Dict:
        """Create a reel from video"""
        url = f"{self.base_url}/media"
        params = {
            "access_token": self.access_token,
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption
        }
        if thumbnail_url:
            params["thumbnail_url"] = thumbnail_url

        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()

    async def publish_media(self, container_id: str) -> Dict:
        """Publish media after container is created"""
        url = f"{self.base_url}/media_publish"
        params = {
            "access_token": self.access_token,
            "creation_id": container_id
        }
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()

class InstagramPost:
    def __init__(self, media_items: List[Media], caption: str):
        self.media_items = media_items
        self.caption = caption
        self.container_id = None

    async def create(self, instagram_api: InstagramAPI) -> Dict:
        """Create appropriate post type based on media items"""
        if len(self.media_items) == 1:
            return await self._create_single_post(instagram_api)
        else:
            return await self._create_carousel(instagram_api)

    async def _create_single_post(self, instagram_api: InstagramAPI) -> Dict:
        """Create a single media post"""
        media = self.media_items[0]
        
        if media.file_url.lower().endswith(('.mp4', '.mov')):
            result = await instagram_api.create_reel(
                video_url=media.processed_urls['instagram'],
                caption=self.caption,
                thumbnail_url=media.processed_urls.get('instagram_thumbnail')
            )
        else:
            result = await instagram_api.create_container(
                media_url=media.processed_urls['instagram'],
                caption=self.caption
            )

        self.container_id = result["id"]
        return await instagram_api.publish_media(self.container_id)

    async def _create_carousel(self, instagram_api: InstagramAPI) -> Dict:
        """Create a carousel post with multiple media items"""
        media_urls = [m.processed_urls['instagram'] for m in self.media_items]
        result = await instagram_api.create_carousel_container(
            media_urls=media_urls,
            caption=self.caption
        )
        self.container_id = result["id"]
        return await instagram_api.publish_media(self.container_id)

async def post_to_instagram(db: Session, media_grouping_id: int, caption: str) -> Dict:
    """Main function to handle posting to Instagram"""
    # Get media items from grouping
    media_items = db.query(Media).filter_by(grouping_id=media_grouping_id).all()
    if not media_items:
        raise ValueError("No media items found in grouping")

    # Get Instagram credentials
    account = db.query(SocialAccount).filter_by(
        user_id=media_items[0].user_id,
        platform='instagram'
    ).first()
    if not account:
        raise ValueError("Instagram account not connected")

    # Create and publish post
    instagram_api = InstagramAPI(account.access_token)
    post = InstagramPost(media_items, caption)
    result = await post.create(instagram_api)

    return result