from typing import List, Dict
import re
from datetime import datetime

class PostFormatter:
    def __init__(self):
        self.platform_limits = {
            'instagram': {'caption': 2200, 'hashtags': 30},
            'facebook': {'caption': 63206, 'hashtags': 30},
            'nextdoor': {'caption': 1500, 'hashtags': 10}
        }

    def format_post(self, content: Dict, platform: str) -> Dict:
        """Format post content for specific platform"""
        caption = content.get('caption', '')
        hashtags = content.get('hashtags', [])
        
        # Format caption
        formatted_caption = self._format_caption(caption, platform)
        
        # Format hashtags
        formatted_hashtags = self._format_hashtags(hashtags, platform)
        
        # Combine caption and hashtags based on platform
        if platform == 'instagram':
            final_text = f"{formatted_caption}\n\n{formatted_hashtags}"
        else:
            final_text = f"{formatted_caption}\n{formatted_hashtags}"

        return {
            'text': final_text,
            'caption': formatted_caption,
            'hashtags': formatted_hashtags
        }

    def generate_hashtags(self, text: str, additional_tags: List[str] = None) -> List[str]:
        """Generate relevant hashtags from text and additional tags"""
        # Extract keywords from text
        keywords = self._extract_keywords(text)
        
        # Combine with additional tags
        all_tags = set(keywords + (additional_tags or []))
        
        # Format as hashtags
        hashtags = [f"#{tag.lower()}" for tag in all_tags]
        
        return hashtags

    def _format_caption(self, caption: str, platform: str) -> str:
        """Format caption according to platform requirements"""
        max_length = self.platform_limits[platform]['caption']
        
        # Truncate if needed
        if len(caption) > max_length:
            caption = caption[:max_length-3] + '...'
            
        # Platform-specific formatting
        if platform == 'instagram':
            # Add line breaks for readability
            caption = re.sub(r'([.!?])\s+', r'\1\n\n', caption)
        
        return caption.strip()

    def _format_hashtags(self, hashtags: List[str], platform: str) -> str:
        """Format hashtags according to platform requirements"""
        max_tags = self.platform_limits[platform]['hashtags']
        
        # Limit number of hashtags
        hashtags = hashtags[:max_tags]
        
        if platform == 'instagram':
            return '\n'.join(hashtags)
        else:
            return ' '.join(hashtags)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Remove special characters and split into words
        words = re.findall(r'\w+', text.lower())
        
        # Remove common words and short words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        return list(set(keywords))