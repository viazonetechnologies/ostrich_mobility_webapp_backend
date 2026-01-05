import pymysql
from pymysql.cursors import DictCursor
import threading
import time
import os
from contextlib import contextmanager

class WebappDatabasePool:
    def __init__(self, max_connections=15, max_idle_time=300):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.pool = []
        self.pool_lock = threading.Lock()
        
        # Use both local and Aiven configs for fallback
        self.primary_config = {
            'host': 'mysql-ostrich-tviazone-5922.i.aivencloud.com',
            'user': 'avnadmin',
            'password': 'AVNS_c985UhSyW3FZhUdTmI8',
            'database': 'defaultdb',
            'port': 16599,
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
            'autocommit': True,
            'cursorclass': DictCursor
        }
        
        self.fallback_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'Aru247899!',
            'database': 'ostrich_db',
            'port': 3306,
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
            'autocommit': True,
            'cursorclass': DictCursor
        }
        
    def _create_connection(self):
        """Create a new database connection with fallback"""
        # Try primary (Aiven) first
        for config_name, config in [("primary", self.primary_config), ("fallback", self.fallback_config)]:
            try:
                conn = pymysql.connect(**config)
                return {
                    'connection': conn,
                    'config_used': config_name,
                    'created_at': time.time(),
                    'last_used': time.time()
                }
            except Exception as e:
                print(f"Failed to connect using {config_name} config: {e}")
                continue
        
        print("All database connection attempts failed")
        return None
    
    def _is_connection_valid(self, conn_info):
        """Check if connection is still valid"""
        try:
            conn = conn_info['connection']
            if not conn.open:
                return False
            conn.ping(reconnect=False)
            return True
        except:
            return False
    
    def get_connection(self):
        """Get a connection from the pool"""
        with self.pool_lock:
            # Try to find a valid connection from pool
            for i, conn_info in enumerate(self.pool):
                if self._is_connection_valid(conn_info):
                    conn_info['last_used'] = time.time()
                    return self.pool.pop(i)['connection']
                else:
                    # Remove invalid connection
                    try:
                        conn_info['connection'].close()
                    except:
                        pass
                    self.pool.pop(i)
            
            # Create new connection if pool is empty
            conn_info = self._create_connection()
            return conn_info['connection'] if conn_info else None
    
    def return_connection(self, connection):
        """Return connection to pool"""
        if not connection or not connection.open:
            return
            
        with self.pool_lock:
            if len(self.pool) < self.max_connections:
                self.pool.append({
                    'connection': connection,
                    'created_at': time.time(),
                    'last_used': time.time()
                })
            else:
                try:
                    connection.close()
                except:
                    pass
    
    def cleanup_idle_connections(self):
        """Remove idle connections from pool"""
        current_time = time.time()
        with self.pool_lock:
            active_connections = []
            for conn_info in self.pool:
                if current_time - conn_info['last_used'] < self.max_idle_time:
                    active_connections.append(conn_info)
                else:
                    try:
                        conn_info['connection'].close()
                    except:
                        pass
            self.pool = active_connections

# Global pool instance
webapp_db_pool = WebappDatabasePool()

@contextmanager
def get_optimized_db_connection():
    """Optimized context manager for database connections"""
    connection = None
    try:
        connection = webapp_db_pool.get_connection()
        if connection:
            yield connection
        else:
            yield None
    except Exception as e:
        print(f"Database connection error: {e}")
        yield None
    finally:
        if connection:
            webapp_db_pool.return_connection(connection)