from flask import request, jsonify
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql
from cloud_image_service import hostinger_image_service

def register_product_images_page_routes(app):
    """Register product images page routes"""
    
    @app.route('/api/v1/product-images/', methods=['GET'])
    @jwt_required()
    def get_product_images():
        """Get all product images with product details"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT p.id, p.name, p.product_code, p.image_url,
                       c.name as category_name, p.price, p.stock_quantity,
                       p.created_at, p.updated_at
                FROM products p
                LEFT JOIN product_categories c ON p.category_id = c.id
                WHERE p.image_url IS NOT NULL AND p.image_url != ''
                ORDER BY p.updated_at DESC
            """
            
            cursor.execute(query)
            products = cursor.fetchall()
            conn.close()
            
            return jsonify(products)
            
        except Exception as e:
            print(f"Get product images error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/product-images/missing', methods=['GET'])
    @jwt_required()
    def get_products_without_images():
        """Get products that don't have images"""
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT p.id, p.name, p.product_code, 
                       c.name as category_name, p.price, p.stock_quantity
                FROM products p
                LEFT JOIN product_categories c ON p.category_id = c.id
                WHERE p.image_url IS NULL OR p.image_url = ''
                ORDER BY p.name
            """
            
            cursor.execute(query)
            products = cursor.fetchall()
            conn.close()
            
            return jsonify(products)
            
        except Exception as e:
            print(f"Get products without images error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/product-images/bulk-upload', methods=['POST'])
    @jwt_required()
    def bulk_upload_images():
        """Bulk upload images for multiple products"""
        try:
            files = request.files.getlist('images')
            product_ids = request.form.getlist('product_ids')
            
            if not files or not product_ids:
                return jsonify({'error': 'No files or product IDs provided'}), 400
            
            if len(files) != len(product_ids):
                return jsonify({'error': 'Number of files must match number of product IDs'}), 400
            
            conn = get_db()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            results = []
            
            for i, (file, product_id) in enumerate(zip(files, product_ids)):
                try:
                    # Upload image
                    image_url = hostinger_image_service.upload_image(file, 'products')
                    if image_url:
                        # Update product
                        cursor.execute(
                            "UPDATE products SET image_url = %s WHERE id = %s",
                            (image_url, product_id)
                        )
                        results.append({
                            'product_id': product_id,
                            'success': True,
                            'image_url': image_url
                        })
                    else:
                        results.append({
                            'product_id': product_id,
                            'success': False,
                            'error': 'Upload failed'
                        })
                except Exception as e:
                    results.append({
                        'product_id': product_id,
                        'success': False,
                        'error': str(e)
                    })
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'message': 'Bulk upload completed',
                'results': results
            })
            
        except Exception as e:
            print(f"Bulk upload error: {e}")
            return jsonify({'error': 'Bulk upload failed'}), 500
    
    @app.route('/api/v1/product-images/stats', methods=['GET'])
    @jwt_required()
    def get_image_stats():
        """Get product image statistics"""
        try:
            conn = get_db()
            if not conn:
                return jsonify({})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Total products
            cursor.execute("SELECT COUNT(*) as total FROM products")
            total = cursor.fetchone()['total']
            
            # Products with images
            cursor.execute("SELECT COUNT(*) as with_images FROM products WHERE image_url IS NOT NULL AND image_url != ''")
            with_images = cursor.fetchone()['with_images']
            
            # Products without images
            without_images = total - with_images
            
            # Percentage
            percentage = (with_images / total * 100) if total > 0 else 0
            
            conn.close()
            
            return jsonify({
                'total_products': total,
                'with_images': with_images,
                'without_images': without_images,
                'percentage_complete': round(percentage, 1)
            })
            
        except Exception as e:
            print(f"Get image stats error: {e}")
            return jsonify({})