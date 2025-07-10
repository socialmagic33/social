from PIL import Image
import ffmpeg
from pathlib import Path
import os
from typing import Dict, Tuple
import json
from datetime import datetime
import hashlib

class MediaProcessor:
    PLATFORM_SPECS = {
        'instagram': {
            'image': {'max_size': (1080, 1080), 'formats': ['jpg', 'png']},
            'video': {'max_size': (1080, 1920), 'formats': ['mp4'], 'max_length': 60}
        },
        'facebook': {
            'image': {'max_size': (2048, 2048), 'formats': ['jpg', 'png']},
            'video': {'max_size': (1920, 1080), 'formats': ['mp4'], 'max_length': 240}
        },
        'nextdoor': {
            'image': {'max_size': (2000, 2000), 'formats': ['jpg', 'png']},
            'video': {'max_size': (1920, 1080), 'formats': ['mp4'], 'max_length': 180}
        }
    }

    def __init__(self, upload_dir: str = "uploads", cache_dir: str = "cache"):
        self.upload_dir = Path(upload_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def process_image(self, file_path: str, platform: str) -> Dict[str, str]:
        """Process image for specific platform requirements"""
        img = Image.open(file_path)
        specs = self.PLATFORM_SPECS[platform]['image']
        
        # Generate cache key
        cache_key = self._generate_cache_key(file_path, platform)
        cached_path = self.cache_dir / f"{cache_key}.jpg"

        if cached_path.exists():
            return {
                'processed_path': str(cached_path),
                'thumbnail': str(self.cache_dir / f"{cache_key}_thumb.jpg")
            }

        # Resize if needed
        if img.size[0] > specs['max_size'][0] or img.size[1] > specs['max_size'][1]:
            img.thumbnail(specs['max_size'])

        # Save processed image
        img.save(cached_path, 'JPEG', quality=85)

        # Generate thumbnail
        thumb = img.copy()
        thumb.thumbnail((300, 300))
        thumb.save(self.cache_dir / f"{cache_key}_thumb.jpg", 'JPEG')

        return {
            'processed_path': str(cached_path),
            'thumbnail': str(self.cache_dir / f"{cache_key}_thumb.jpg")
        }

    def process_video(self, file_path: str, platform: str) -> Dict[str, str]:
        """Process video for specific platform requirements"""
        specs = self.PLATFORM_SPECS[platform]['video']
        cache_key = self._generate_cache_key(file_path, platform)
        cached_path = self.cache_dir / f"{cache_key}.mp4"

        if cached_path.exists():
            return {
                'processed_path': str(cached_path),
                'thumbnail': str(self.cache_dir / f"{cache_key}_thumb.jpg")
            }

        # Get video metadata
        probe = ffmpeg.probe(file_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        
        # Calculate new dimensions
        width = int(video_info['width'])
        height = int(video_info['height'])
        new_width, new_height = self._calculate_video_dimensions(
            (width, height), 
            specs['max_size']
        )

        # Process video
        stream = ffmpeg.input(file_path)
        stream = ffmpeg.filter(stream, 'scale', new_width, new_height)
        stream = ffmpeg.output(stream, str(cached_path), 
                             **{'c:v': 'libx264', 'crf': 23, 'preset': 'medium'})
        ffmpeg.run(stream, overwrite_output=True)

        # Generate thumbnail
        thumbnail_path = self.cache_dir / f"{cache_key}_thumb.jpg"
        stream = ffmpeg.input(file_path, ss=1)
        stream = ffmpeg.filter(stream, 'scale', 300, -1)
        stream = ffmpeg.output(stream, str(thumbnail_path), vframes=1)
        ffmpeg.run(stream, overwrite_output=True)

        return {
            'processed_path': str(cached_path),
            'thumbnail': str(thumbnail_path)
        }

    def extract_metadata(self, file_path: str) -> Dict:
        """Extract metadata from media file"""
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            return self._extract_image_metadata(file_path)
        elif file_path.lower().endswith(('.mp4', '.mov')):
            return self._extract_video_metadata(file_path)
        raise ValueError("Unsupported file type")

    def _extract_image_metadata(self, file_path: str) -> Dict:
        img = Image.open(file_path)
        exif = img.getexif() if hasattr(img, 'getexif') else {}
        
        return {
            'dimensions': img.size,
            'format': img.format,
            'mode': img.mode,
            'exif': dict(exif.items()) if exif else {},
            'created_at': datetime.fromtimestamp(os.path.getctime(file_path))
        }

    def _extract_video_metadata(self, file_path: str) -> Dict:
        probe = ffmpeg.probe(file_path)
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        
        return {
            'dimensions': (int(video_stream['width']), int(video_stream['height'])),
            'duration': float(probe['format']['duration']),
            'format': probe['format']['format_name'],
            'codec': video_stream['codec_name'],
            'created_at': datetime.fromtimestamp(os.path.getctime(file_path))
        }

    def _calculate_video_dimensions(
        self, 
        current: Tuple[int, int], 
        max_size: Tuple[int, int]
    ) -> Tuple[int, int]:
        """Calculate new video dimensions maintaining aspect ratio"""
        width, height = current
        max_width, max_height = max_size
        
        if width <= max_width and height <= max_height:
            return width, height
            
        ratio = min(max_width/width, max_height/height)
        return int(width * ratio), int(height * ratio)

    def _generate_cache_key(self, file_path: str, platform: str) -> str:
        """Generate unique cache key based on file content and platform"""
        file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
        return f"{platform}_{file_hash}"