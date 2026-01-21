from flask import jsonify, request
from flask_jwt_extended import jwt_required
from database import get_db
import pymysql

def register_regions_routes(app):
    
    @app.route('/api/v1/regions/', methods=['GET', 'POST'])
    @jwt_required()
    def handle_regions():
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify([])
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT r.*, CONCAT(u.first_name, ' ', u.last_name) as manager_name
                    FROM regions r
                    LEFT JOIN users u ON r.manager_id = u.id
                    ORDER BY r.created_at DESC
                """)
                regions = cursor.fetchall()
                conn.close()
                
                return jsonify(regions)
            except Exception as e:
                print(f"Get regions error: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                
                if not data.get('name'):
                    return jsonify({'error': 'Region name is required'}), 400
                if not data.get('state'):
                    return jsonify({'error': 'State is required'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor()
                
                # Generate code if not provided
                code = data.get('code')
                if not code:
                    cursor.execute("SELECT COUNT(*) as count FROM regions")
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    code = f"REG{count + 1:03d}"
                
                cursor.execute("""
                    INSERT INTO regions (name, code, state, country, manager_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    data['name'],
                    code,
                    data['state'],
                    data.get('country', 'India'),
                    data.get('manager_id'),
                    data.get('is_active', True)
                ))
                
                region_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return jsonify({'id': region_id, 'message': 'Region created successfully'}), 201
            except Exception as e:
                print(f"Create region error: {e}")
                return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/regions/<int:region_id>', methods=['GET', 'PUT', 'DELETE'])
    @jwt_required()
    def handle_single_region(region_id):
        if request.method == 'GET':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT r.*, CONCAT(u.first_name, ' ', u.last_name) as manager_name
                    FROM regions r
                    LEFT JOIN users u ON r.manager_id = u.id
                    WHERE r.id = %s
                """, (region_id,))
                region = cursor.fetchone()
                conn.close()
                
                if not region:
                    return jsonify({'error': 'Region not found'}), 404
                
                return jsonify(region)
            except Exception as e:
                print(f"Get region error: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'PUT':
            try:
                data = request.get_json()
                
                if not data.get('name'):
                    return jsonify({'error': 'Region name is required'}), 400
                if not data.get('state'):
                    return jsonify({'error': 'State is required'}), 400
                
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE regions 
                    SET name = %s, code = %s, state = %s, country = %s, 
                        manager_id = %s, is_active = %s
                    WHERE id = %s
                """, (
                    data['name'],
                    data.get('code', ''),
                    data['state'],
                    data.get('country', 'India'),
                    data.get('manager_id'),
                    data.get('is_active', True),
                    region_id
                ))
                
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Region updated successfully'})
            except Exception as e:
                print(f"Update region error: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'DELETE':
            try:
                conn = get_db()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor()
                cursor.execute("DELETE FROM regions WHERE id = %s", (region_id,))
                conn.commit()
                conn.close()
                
                return jsonify({'message': 'Region deleted successfully'})
            except Exception as e:
                print(f"Delete region error: {e}")
                return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/regions/managers', methods=['GET'])
    def get_managers():
        try:
            conn = get_db()
            if not conn:
                return jsonify([])
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id, username, first_name, last_name, role
                FROM users
                WHERE role = 'regional_officer'
                ORDER BY first_name
            """)
            managers = cursor.fetchall()
            conn.close()
            
            return jsonify(managers)
        except Exception as e:
            print(f"Get managers error: {e}")
            return jsonify([])
    
    @app.route('/api/v1/regions/filters', methods=['GET'])
    @jwt_required()
    def get_filter_options():
        try:
            conn = get_db()
            if not conn:
                return jsonify({'states': [], 'countries': [], 'managers': []})
            
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Get unique states
            cursor.execute("SELECT DISTINCT state FROM regions WHERE state IS NOT NULL ORDER BY state")
            states = [row['state'] for row in cursor.fetchall()]
            
            # Get unique countries
            cursor.execute("SELECT DISTINCT country FROM regions WHERE country IS NOT NULL ORDER BY country")
            countries = [row['country'] for row in cursor.fetchall()]
            
            # Get managers (regional officers only)
            cursor.execute("""
                SELECT id, CONCAT(first_name, ' ', last_name) as name
                FROM users
                WHERE role = 'regional_officer'
                ORDER BY first_name
            """)
            managers = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'states': states,
                'countries': countries,
                'managers': managers
            })
        except Exception as e:
            print(f"Get filter options error: {e}")
            return jsonify({'states': [], 'countries': [], 'managers': []})
