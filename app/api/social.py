from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps.auth import get_current_user
from app.services.social import meta_api, store_social_account
from app.models import User, SocialAccount
from urllib.parse import urlencode
from app.config import settings
from typing import List

router = APIRouter()

@router.get("/meta/auth")
async def meta_auth(request: Request):
    """Initiate Meta OAuth flow"""
    redirect_uri = f"{settings.BASE_URL}/api/social/meta/callback"
    auth_url = meta_api.get_oauth_url(redirect_uri)
    return {"auth_url": auth_url}

@router.get("/meta/callback")
async def meta_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle Meta OAuth callback"""
    redirect_uri = f"{settings.BASE_URL}/api/social/meta/callback"
    
    try:
        # Exchange code for access token
        token_data = await meta_api.exchange_code(code, redirect_uri)
        access_token = token_data["access_token"]
        
        # Get long-lived token
        long_lived_token = await meta_api.get_long_lived_token(access_token)
        
        # Get user's Facebook pages
        pages = await meta_api.get_user_pages(long_lived_token["access_token"])
        
        if not pages:
            raise HTTPException(status_code=400, detail="No Facebook pages found")
        
        # Store Facebook page access
        for page in pages:
            store_social_account(
                db,
                current_user,
                "facebook",
                page["access_token"],
                None,
                page["id"]
            )
            
            # Check for Instagram account
            instagram = await meta_api.get_instagram_account(
                page["id"],
                page["access_token"]
            )
            
            if instagram:
                store_social_account(
                    db,
                    current_user,
                    "instagram",
                    page["access_token"],
                    None,
                    instagram["id"]
                )
        
        return {"message": "Social accounts connected successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect accounts: {str(e)}")

@router.get("/accounts")
async def list_social_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's connected social accounts"""
    accounts = db.query(SocialAccount).filter_by(user_id=current_user.id).all()
    return [
        {
            "id": account.id,
            "platform": account.platform,
            "account_id": account.account_id,
            "connected_at": account.created_at
        }
        for account in accounts
    ]

@router.post("/disconnect")
async def disconnect_social_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disconnect a social media account"""
    account = db.query(SocialAccount).filter_by(
        id=account_id,
        user_id=current_user.id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account disconnected successfully"}

@router.post("/test-post")
async def test_social_post(
    platform: str,
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test posting to a social platform"""
    account = db.query(SocialAccount).filter_by(
        user_id=current_user.id,
        platform=platform
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail=f"No {platform} account connected")
    
    # This would integrate with actual social media APIs
    # For now, just return success
    return {
        "message": f"Test post would be sent to {platform}",
        "content": message,
        "platform": platform
    }