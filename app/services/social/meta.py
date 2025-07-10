from typing import Dict, Optional
import requests
from app.config import settings

class MetaAPI:
    def __init__(self):
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
    def get_oauth_url(self, redirect_uri: str) -> str:
        """Generate Meta OAuth URL"""
        scope = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,pages_manage_posts"
        return f"https://facebook.com/{self.api_version}/dialog/oauth?" + \
               f"client_id={settings.META_APP_ID}&" + \
               f"redirect_uri={redirect_uri}&" + \
               f"scope={scope}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict:
        """Exchange auth code for access token"""
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "code": code,
            "redirect_uri": redirect_uri
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_long_lived_token(self, access_token: str) -> Dict:
        """Exchange short-lived token for long-lived token"""
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": access_token
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_user_pages(self, access_token: str) -> list:
        """Get user's Facebook pages"""
        url = f"{self.base_url}/me/accounts"
        params = {"access_token": access_token}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()["data"]

    async def get_instagram_account(self, page_id: str, access_token: str) -> Optional[Dict]:
        """Get Instagram Business account connected to Facebook page"""
        url = f"{self.base_url}/{page_id}"
        params = {
            "access_token": access_token,
            "fields": "instagram_business_account"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("instagram_business_account")

meta_api = MetaAPI()