import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import requests
from PIL import Image
import io

class HostingerImageService:
    def __init__(self):
        # Hostinger configuration
        self.base_url = os.getenv('HOSTINGER_DOMAIN', 'http://localhost:8002')
        self.upload_path = '/public_html/uploads/products/'
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        
    def validate_image(self, file):
        """Validate image file"""
        try:
            # Check file size
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if size > self.max_file_size:
                return False, "File size too large (max 5MB)"
            
            # Validate image format
            try:
                img = Image.open(file)
                img.verify()
                file.seek(0)  # Reset after verify
                return True, "Valid image"
            except Exception:
                return False, "Invalid image format"
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def resize_image(self, file, max_width=800, max_height=600):
        """Resize image to optimize for web"""
        try:
            img = Image.open(file)
            
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Calculate new dimensions
            width, height = img.size
            if width > max_width or height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return output
        except Exception as e:
            print(f"Image resize error: {e}")
            return file
    
    def upload_image(self, file, folder='products'):
        """Upload image to local storage and return URL"""
        try:
            # Validate image
            is_valid, message = self.validate_image(file)
            if not is_valid:
                print(f"Image validation failed: {message}")
                return None
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            new_filename = f"{timestamp}_{unique_id}_{name}.jpg"  # Always save as JPG
            
            # Create upload directory
            upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', folder)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Resize and optimize image
            resized_file = self.resize_image(file)
            
            # Save file
            file_path = os.path.join(upload_dir, new_filename)
            with open(file_path, 'wb') as f:
                f.write(resized_file.read())
            
            # Return public URL
            return f"{self.base_url}/static/uploads/{folder}/{new_filename}"
            
        except Exception as e:
            print(f"Image upload error: {e}")
            return None
    
    def delete_image(self, image_url):
        """Delete image from Hostinger"""
        try:
            # Extract filename from URL
            filename = image_url.split('/')[-1]
            folder = image_url.split('/')[-2]
            
            file_path = os.path.join(os.getcwd(), 'static', 'uploads', folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Image delete error: {e}")
            return False

# Initialize service
hostinger_image_service = HostingerImageService()