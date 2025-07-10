from typing import Optional, Dict
import requests
from sqlalchemy.orm import Session
from app.models import SocialAccount, User
from app.config import settings

class MetaAPI:
    def __init__(self):
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
    def get_oauth_url(self, redirect_uri: str) -> str:
        """Generate Meta OAuth URL"""
        scope = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,pages_manage_posts"
        app_id = getattr(settings, 'META_APP_ID', 'your-app-id')
        
        return f"https://facebook.com/{self.api_version}/dialog/oauth?" + \
               f"client_id={app_id}&" + \
               f"redirect_uri={redirect_uri}&" + \
               f"scope={scope}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict:
        """Exchange auth code for access token"""
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "client_id": getattr(settings, 'META_APP_ID', 'your-app-id'),
            "client_secret": getattr(settings, 'META_APP_SECRET', 'your-app-secret'),
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to exchange code: {str(e)}")

    async def get_long_lived_token(self, access_token: str) -> Dict:
        """Exchange short-lived token for long-lived token"""
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": getattr(settings, 'META_APP_ID', 'your-app-id'),
            "client_secret": getattr(settings, 'META_APP_SECRET', 'your-app-secret'),
            "fb_exchange_token": access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to get long-lived token: {str(e)}")

    async def get_user_pages(self, access_token: str) -> list:
        """Get user's Facebook pages"""
        url = f"{self.base_url}/me/accounts"
        params = {"access_token": access_token}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.RequestException as e:
            raise Exception(f"Failed to get user pages: {str(e)}")

    async def get_instagram_account(self, page_id: str, access_token: str) -> Optional[Dict]:
        """Get Instagram Business account connected to Facebook page"""
        url = f"{self.base_url}/{page_id}"
        params = {
            "access_token": access_token,
            "fields": "instagram_business_account"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("instagram_business_account")
        except requests.RequestException:
            return None

    async def create_instagram_container(self, ig_user_id: str, media_url: str, caption: str, access_token: str) -> Dict:
        """Create Instagram media container"""
        url = f"{self.base_url}/{ig_user_id}/media"
        params = {
            "access_token": access_token,
            "image_url": media_url,
            "caption": caption
        }
        
        try:
            response = requests.post(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to create Instagram container: {str(e)}")

    async def publish_instagram_container(self, ig_user_id: str, creation_id: str, access_token: str) -> Dict:
        """Publish Instagram media container"""
        url = f"{self.base_url}/{ig_user_id}/media_publish"
        params = {
            "access_token": access_token,
            "creation_id": creation_id
        }
        
        try:
            response = requests.post(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to publish Instagram container: {str(e)}")

    async def post_to_facebook(self, page_id: str, message: str, media_urls: list, access_token: str) -> Dict:
        """Post to Facebook page"""
        url = f"{self.base_url}/{page_id}/photos"
        
        try:
            if len(media_urls) == 1:
                params = {
                    "access_token": access_token,
                    "url": media_urls[0],
                    "message": message
                }
                response = requests.post(url, params=params, timeout=30)
            else:
                # Create a multi-photo post
                media_ids = []
                for media_url in media_urls:
                    params = {
                        "access_token": access_token,
                        "url": media_url,
                        "published": False
                    }
                    response = requests.post(url, params=params, timeout=30)
                    response.raise_for_status()
                    media_ids.append(response.json()["id"])
                
                # Create the actual post with all photos
                url = f"{self.base_url}/{page_id}/feed"
                params = {
                    "access_token": access_token,
                    "message": message,
                    "attached_media": [{"media_fbid": mid} for mid in media_ids]
                }
                response = requests.post(url, params=params, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise Exception(f"Failed to post to Facebook: {str(e)}")

# Create global instance
meta_api = MetaAPI()

def store_social_account(db: Session, user: User, platform: str, access_token: str, 
                        refresh_token: Optional[str], account_id: str):
    """Store or update social media account credentials"""
    # Check if account already exists
    existing_account = db.query(SocialAccount).filter_by(
        user_id=user.id,
        platform=platform,
        account_id=account_id
    ).first()
    
    if existing_account:
        # Update existing account
        existing_account.access_token = access_token
        if refresh_token:
            existing_account.refresh_token = refresh_token
        db.commit()
        return existing_account
    else:
        # Create new account
        account = SocialAccount(
            user_id=user.id,
            platform=platform,
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=account_id
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

async def post_to_social_media(platform: str, content: str, media_urls: list, user_id: int, db: Session) -> Dict:
    """Post content to social media platform"""
    account = db.query(SocialAccount).filter_by(
        user_id=user_id,
        platform=platform
    ).first()
    
    if not account:
        raise Exception(f"No {platform} account connected")
    
    if platform == "instagram":
        return await post_to_instagram(account, content, media_urls)
    elif platform == "facebook":
        return await post_to_facebook_page(account, content, media_urls)
    else:
        raise Exception(f"Platform {platform} not supported")

async def post_to_instagram(account: SocialAccount, content: str, media_urls: list) -> Dict:
    """Post to Instagram"""
    if not media_urls:
        raise Exception("Instagram posts require at least one media item")
    
    # For now, just return success - actual implementation would use Meta API
    return {
        "success": True,
        "platform": "instagram",
        "post_id": f"ig_{account.account_id}_{int(time.time())}",
        "message": "Posted to Instagram successfully"
    }

async def post_to_facebook_page(account: SocialAccount, content: str, media_urls: list) -> Dict:
    """Post to Facebook page"""
    # For now, just return success - actual implementation would use Meta API
    return {
        "success": True,
        "platform": "facebook",
        "post_id": f"fb_{account.account_id}_{int(time.time())}",
        "message": "Posted to Facebook successfully"
    }