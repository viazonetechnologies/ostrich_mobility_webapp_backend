from flask import request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql
from local_image_service import local_image_service
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image

def register_product_images_routes(app):
    """Register product image management routes"""
    
    # Configure upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'product_images')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    def ensure_single_primary(cursor, product_id):
        """Ensure only one primary image exists per product"""
        cursor.execute("SELECT id FROM product_images WHERE product_id = %s AND image_type = 'primary' ORDER BY created_at ASC", (product_id,))
        primaries = cursor.fetchall()
        
        if len(primaries) > 1:
            # Keep first, change others to gallery
            for i, primary in enumerate(primaries):
                if i > 0:
                    cursor.execute("UPDATE product_images SET image_type = 'gallery' WHERE id = %s", (primary['id'],))
            
            # Update products table with the kept primary
            cursor.execute("SELECT image_url FROM product_images WHERE id = %s", (primaries[0]['id'],))
            primary_url = cursor.fetchone()['image_url']
            cursor.execute("UPDATE products SET image_url = %s WHERE id = %s", (primary_url, product_id))
    
    @app.route('/api/v1/product-images/<int:product_id>', methods=['GET'])
    @jwt_required()
    def get_product_images_by_id(product_id):
        """Get all images for a specific product"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, product_id, image_url, alt_text, 
                       (image_type = 'primary') as is_primary, 
                       created_at, updated_at
                FROM product_images 
                WHERE product_id = %s
                ORDER BY (image_type = 'primary') DESC, created_at ASC
            """, (product_id,))
            
            images = cursor.fetchall()
            
            # Safety check: ensure no duplicate primaries exist
            primary_images = [img for img in images if img['is_primary']]
            if len(primary_images) > 1:
                # Fix duplicates immediately
                for i, img in enumerate(primary_images):
                    if i > 0:
                        cursor.execute("UPDATE product_images SET image_type = 'gallery' WHERE id = %s", (img['id'],))
                        img['is_primary'] = False
                conn.commit()
            
            conn.close()
            return jsonify(images)
            
        except Exception as e:
            print(f"Get product images error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/product-images/bulk-upload', methods=['POST'])
    @jwt_required()
    def bulk_upload_product_images():
        """Bulk upload images for multiple products"""
        try:
            files = request.files.getlist('images')
            product_ids = request.form.getlist('product_ids')
            
            if not files or not product_ids:
                return jsonify({'error': 'No images or product IDs provided'}), 400
            
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            uploaded_count = 0
            results = []
            
            for i, file in enumerate(files):
                if file.filename and i < len(product_ids):
                    product_id = int(product_ids[i])
                    
                    # Upload image
                    image_url = local_image_service.upload_image(file, 'products')
                    if image_url:
                        # Insert as gallery image
                        cursor.execute("""
                            INSERT INTO product_images (product_id, image_url, image_type, created_at, updated_at)
                            VALUES (%s, %s, 'gallery', NOW(), NOW())
                        """, (product_id, image_url))
                        
                        # Set as primary if no primary exists
                        cursor.execute("SELECT COUNT(*) as count FROM product_images WHERE product_id = %s AND image_type = 'primary'", (product_id,))
                        primary_count = cursor.fetchone()['count']
                        
                        if primary_count == 0:
                            cursor.execute("UPDATE product_images SET image_type = 'primary' WHERE product_id = %s AND image_url = %s", (product_id, image_url))
                            cursor.execute("UPDATE products SET image_url = %s WHERE id = %s", (image_url, product_id))
                        
                        uploaded_count += 1
                        results.append({'product_id': product_id, 'image_url': image_url, 'status': 'success'})
                    else:
                        results.append({'product_id': product_id, 'status': 'failed', 'error': 'Upload failed'})
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'uploaded_count': uploaded_count,
                'total_files': len(files),
                'results': results
            })
            
        except Exception as e:
            print(f"Bulk upload error: {e}")
            return jsonify({'error': 'Bulk upload failed'}), 500
    
    @app.route('/api/v1/product-images/upload/<int:product_id>', methods=['POST'])
    @jwt_required()
    def upload_product_images_by_id(product_id):
        """Upload multiple images for a product"""
        try:
            files = request.files.getlist('images')
            if not files:
                return jsonify({'error': 'No images provided'}), 400
            
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            uploaded_count = 0
            for file in files:
                if file.filename:
                    # Use local image service
                    image_url = local_image_service.upload_image(file, 'products')
                    if image_url:
                        # Insert into product_images table as gallery by default
                        cursor.execute("""
                            INSERT INTO product_images (product_id, image_url, image_type, created_at, updated_at)
                            VALUES (%s, %s, 'gallery', NOW(), NOW())
                        """, (product_id, image_url))
                        
                        # Only update products table if no primary image exists
                        cursor.execute("SELECT COUNT(*) as count FROM product_images WHERE product_id = %s AND image_type = 'primary'", (product_id,))
                        primary_count = cursor.fetchone()['count']
                        
                        if primary_count == 0:
                            # No primary image exists, set this as primary and update products table
                            cursor.execute("UPDATE product_images SET image_type = 'primary' WHERE product_id = %s AND image_url = %s", (product_id, image_url))
                            cursor.execute("UPDATE products SET image_url = %s WHERE id = %s", (image_url, product_id))
                        else:
                            # Primary already exists, ensure no duplicates by checking again
                            cursor.execute("UPDATE product_images SET image_type = 'gallery' WHERE product_id = %s AND image_url = %s", (product_id, image_url))
                        
                        uploaded_count += 1
            
            # Ensure no duplicate primaries exist
            ensure_single_primary(cursor, product_id)
            
            conn.commit()
            conn.close()
            return jsonify({'uploaded_count': uploaded_count})
            
        except Exception as e:
            print(f"Upload images error: {e}")
            return jsonify({'error': 'Failed to upload images'}), 500
    
    @app.route('/api/v1/product-images/<int:image_id>/set-primary', methods=['PUT'])
    @jwt_required()
    def set_primary_image_by_id(image_id):
        """Set an image as primary and update products table"""
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get the product_id and image_url for this image
            cursor.execute("SELECT product_id, image_url FROM product_images WHERE id = %s", (image_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return jsonify({'error': 'Image not found'}), 404
            
            product_id = result['product_id']
            new_primary_url = result['image_url']
            
            # First, remove primary flag from ALL images of this product
            cursor.execute("UPDATE product_images SET image_type = 'gallery' WHERE product_id = %s", (product_id,))
            
            # Then set ONLY this image as primary
            cursor.execute("UPDATE product_images SET image_type = 'primary' WHERE id = %s", (image_id,))
            
            # Update products table with new primary image
            cursor.execute("UPDATE products SET image_url = %s WHERE id = %s", (new_primary_url, product_id))
            
            # Ensure no duplicate primaries exist (safety check)
            ensure_single_primary(cursor, product_id)
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Primary image updated successfully'})
            
        except Exception as e:
            print(f"Set primary image error: {e}")
            return jsonify({'error': 'Failed to set primary image'}), 500
    
    @app.route('/api/v1/product-images/delete/<int:image_id>', methods=['DELETE'])
    @jwt_required()
    def delete_product_image_by_id(image_id):
        """Delete a product image (cannot delete primary images)"""
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get image details
            cursor.execute("SELECT image_url, image_type, product_id FROM product_images WHERE id = %s", (image_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return jsonify({'error': 'Image not found'}), 404
            
            # Prevent deletion of primary images
            if result['image_type'] == 'primary':
                conn.close()
                return jsonify({'error': 'Cannot delete primary image. Use remove option in product form instead.'}), 400
            
            image_url = result['image_url']
            
            # Delete from database
            cursor.execute("DELETE FROM product_images WHERE id = %s", (image_id,))
            
            # Delete physical file
            local_image_service.delete_image(image_url)
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Image deleted successfully'})
            
        except Exception as e:
            print(f"Delete image error: {e}")
            return jsonify({'error': 'Failed to delete image'}), 500
    
    @app.route('/api/v1/product-images/sync-existing', methods=['POST'])
    @jwt_required()
    def sync_existing_images_api():
        """Sync existing product images"""
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            cursor.execute("""
                INSERT INTO product_images (product_id, image_url, is_primary, created_at, updated_at)
                SELECT id, image_url, TRUE, created_at, updated_at 
                FROM products 
                WHERE image_url IS NOT NULL AND image_url != ''
                AND id NOT IN (SELECT DISTINCT product_id FROM product_images)
            """)
            
            synced_count = cursor.rowcount
            conn.commit()
            conn.close()
            return jsonify({'synced_count': synced_count})
            
        except Exception as e:
            return jsonify({'error': 'Failed to sync images'}), 500
    
    @app.route('/api/v1/product-images/remove-primary/<int:product_id>', methods=['DELETE'])
    @jwt_required()
    def remove_primary_image(product_id):
        """Remove primary image from both tables"""
        try:
            conn = get_db()
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get primary image
            cursor.execute("SELECT id, image_url FROM product_images WHERE product_id = %s AND image_type = 'primary'", (product_id,))
            primary_image = cursor.fetchone()
            
            if primary_image:
                # Delete from product_images table
                cursor.execute("DELETE FROM product_images WHERE id = %s", (primary_image['id'],))
                
                # Delete physical file
                local_image_service.delete_image(primary_image['image_url'])
            
            # Remove from products table
            cursor.execute("UPDATE products SET image_url = NULL WHERE id = %s", (product_id,))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Primary image removed successfully'})
            
        except Exception as e:
            print(f"Remove primary image error: {e}")
            return jsonify({'error': 'Failed to remove primary image'}), 500
    
    @app.route('/api/v1/products/<int:product_id>/upload-image', methods=['POST'])
    @jwt_required()
    def upload_and_set_product_image(product_id):
        """Upload image and set as product image"""
        try:
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Check if product exists
            cursor.execute("SELECT id, image_url FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if not product:
                conn.close()
                return jsonify({'error': 'Product not found'}), 404
            
            # Upload new image
            image_url = local_image_service.upload_image(file, 'products')
            if not image_url:
                conn.close()
                return jsonify({'error': 'Failed to upload image'}), 500
            
            # Delete old image if exists
            old_image_url = product.get('image_url')
            if old_image_url and old_image_url != image_url:
                local_image_service.delete_image(old_image_url)
                # Remove old primary image from product_images table
                cursor.execute("DELETE FROM product_images WHERE product_id = %s AND image_type = 'primary'", (product_id,))
            
            # Update product with new image URL
            cursor.execute(
                "UPDATE products SET image_url = %s WHERE id = %s",
                (image_url, product_id)
            )
            
            # Add to product_images table as primary
            cursor.execute("""
                INSERT INTO product_images (product_id, image_url, image_type, created_at, updated_at)
                VALUES (%s, %s, 'primary', NOW(), NOW())
            """, (product_id, image_url))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'message': 'Image uploaded and set successfully',
                'image_url': image_url
            })
            
        except Exception as e:
            print(f"Upload and set image error: {e}")
            return jsonify({'error': 'Failed to upload image'}), 500
    
    @app.route('/api/v1/products/<int:product_id>/remove-image', methods=['DELETE'])
    @jwt_required()
    def remove_product_image(product_id):
        """Remove product image"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get current image URL
            cursor.execute("SELECT image_url FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if not product:
                conn.close()
                return jsonify({'error': 'Product not found'}), 404
            
            image_url = product.get('image_url')
            if image_url:
                # Delete image file
                local_image_service.delete_image(image_url)
                
                # Remove image URL from products table
                cursor.execute(
                    "UPDATE products SET image_url = NULL WHERE id = %s",
                    (product_id,)
                )
                
                # Remove from product_images table
                cursor.execute(
                    "DELETE FROM product_images WHERE product_id = %s AND image_type = 'primary'",
                    (product_id,)
                )
                
                conn.commit()
            
            conn.close()
            return jsonify({'message': 'Image removed successfully'})
            
        except Exception as e:
            print(f"Remove image error: {e}")
            return jsonify({'error': 'Failed to remove image'}), 500
    
    @app.route('/api/v1/products/fix-images', methods=['POST'])
    @jwt_required()
    def fix_product_images():
        """Fix product images with placeholder URLs"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Sample cloud URLs for different product types
            image_mappings = {
                'Motors': 'https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=300',
                'Switches': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300', 
                'Panels': 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=300',
                'Cables': 'https://images.unsplash.com/photo-1594736797933-d0401ba2fe65?w=300'
            }
            
            # Update products with appropriate images
            for category, image_url in image_mappings.items():
                cursor.execute("""
                    UPDATE products p 
                    JOIN product_categories c ON p.category_id = c.id 
                    SET p.image_url = %s 
                    WHERE c.name = %s AND (p.image_url IS NULL OR p.image_url = '')
                """, (image_url, category))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Product images updated successfully'})
            
        except Exception as e:
            print(f"Fix images error: {e}")
            return jsonify({'error': 'Failed to fix images'}), 500