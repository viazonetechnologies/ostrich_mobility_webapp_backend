import pymysql
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/test-sale', methods=['POST'])
def test_sale():
    try:
        # Direct database connection test
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Aru247899!',
            database='ostrich_db',
            port=3306,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Simple insert test
        cursor.execute("""
            INSERT INTO sales (sale_number, customer_id, total_amount, final_amount, payment_status, delivery_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("TEST001", 1, 100.0, 100.0, "pending", "pending"))
        
        sale_id = cursor.lastrowid
        connection.commit()
        connection.close()
        
        return jsonify({"success": True, "sale_id": sale_id})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8001, debug=True)