import os
import glob

# Check upload folder
upload_folder = 'static/uploads/products'
print(f"Upload folder: {upload_folder}")
print(f"Folder exists: {os.path.exists(upload_folder)}")

if os.path.exists(upload_folder):
    files = glob.glob(os.path.join(upload_folder, '*'))
    print(f"Files count: {len(files)}")
    
    if files:
        print("Recent files:")
        for f in files[-5:]:
            filename = os.path.basename(f)
            size = os.path.getsize(f)
            print(f"  - {filename} ({size} bytes)")
    else:
        print("No files found")
else:
    print("Upload folder does not exist")
    # Try to create it
    try:
        os.makedirs(upload_folder, exist_ok=True)
        print(f"Created upload folder: {upload_folder}")
    except Exception as e:
        print(f"Failed to create upload folder: {e}")