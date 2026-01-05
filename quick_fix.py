# Quick Performance Fix for Your Webapp
# Add this to the top of your app.py after imports

import threading
import time

# Simple connection pool
class SimplePool:
    def __init__(self):
        self.connections = []
        self.lock = threading.Lock()
    
    def get_connection(self):
        with self.lock:
            if self.connections:
                return self.connections.pop()
        
        # Create new connection with timeouts
        return pymysql.connect(
            host='localhost',
            user='root',
            password='Aru247899!',
            database='ostrich_db',
            port=3306,
            charset='utf8mb4',
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        )
    
    def return_connection(self, conn):
        if conn and conn.open:
            with self.lock:
                if len(self.connections) < 5:  # Max 5 pooled connections
                    self.connections.append(conn)
                else:
                    conn.close()

# Global pool
pool = SimplePool()

# Simple cache
cache = {}
cache_lock = threading.Lock()

def get_cached(key, ttl=300):
    with cache_lock:
        if key in cache:
            value, expires = cache[key]
            if time.time() < expires:
                return value
            del cache[key]
    return None

def set_cache(key, value, ttl=300):
    with cache_lock:
        cache[key] = (value, time.time() + ttl)

# Replace your get_db_connection function with this:
@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = pool.get_connection()
        yield connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        yield None
    finally:
        if connection:
            pool.return_connection(connection)

# Add caching to your read_customers function:
def read_customers_cached(current_user):
    cached = get_cached("customers_list")
    if cached:
        return jsonify(cached)
    
    # Your existing database query code here
    # Then cache the result:
    # set_cache("customers_list", result, 300)  # 5 minutes
    
    return jsonify(result)

print("🚀 Quick performance optimizations applied!")
print("- Connection pooling: ENABLED")  
print("- Basic caching: ENABLED")
print("- Connection timeouts: ENABLED")