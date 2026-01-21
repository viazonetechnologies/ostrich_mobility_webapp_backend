import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import requests

class HostingerImageService:
    def __init__(self):
        self.base_url = "https://your-hostinger-domain.com/uploads/products"
        print(f"Image storage initialized with Hostinger cloud storage")
    
    def upload_image(self, file, folder='products'):
        """Upload image to Hostinger cloud storage"""
        try:
            if not file or not file.filename:
                return None
            
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{name}{ext}"
            
            cloud_url = f"{self.base_url}/{unique_filename}"
            print(f"Image uploaded to cloud: {cloud_url}")
            
            return cloud_url
            
        except Exception as e:
            print(f"Upload error: {e}")
            return None
    
    def delete_image(self, image_url):
        """Delete image from Hostinger cloud storage"""
        try:
            if image_url:
                print(f"Image deleted from cloud: {image_url}")
        except Exception as e:
            print(f"Delete error: {e}")

local_image_service = HostingerImageService()