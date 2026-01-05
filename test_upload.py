@app.route('/api/v1/products/<int:product_id>/images', methods=['POST'])
@token_required
def add_product_image(product_id, current_user):
    print(f"Upload request received for product {product_id}")
    print(f"Request files: {list(request.files.keys())}")
    print(f"Request form: {dict(request.form)}")
    print(f"Content type: {request.content_type}")
    
    try:
        # Handle multiple files
        if not request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        uploaded_images = []
        
        for key in request.files:
            file = request.files[key]
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    continue
                
                # Generate unique filename
                file_ext = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save file
                file.save(file_path)
                image_url = f"/static/uploads/products/{unique_filename}"
                
                # Save to database
                try:
                    with get_db_connection() as conn:
                        if conn is not None:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO product_images (product_id, image_url, filename, alt_text, display_order, is_primary)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (product_id, image_url, unique_filename, file.filename, len(uploaded_images) + 1, False))
                            conn.commit()
                except Exception as db_error:
                    print(f"Database save failed: {db_error}")
                
                uploaded_images.append({
                    "image_url": image_url,
                    "filename": unique_filename
                })
        
        return jsonify({
            "success": True,
            "uploaded_count": len(uploaded_images),
            "images": uploaded_images
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500