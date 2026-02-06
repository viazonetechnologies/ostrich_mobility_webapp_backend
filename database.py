import pymysql
from dbutils.pooled_db import PooledDB
import os
import re

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return ''
    return re.sub(r'[<>"\';]', '', str(text).strip())

# Connection pool
_db_pool = None

def _init_pool():
    """Initialize database connection pool"""
    global _db_pool
    if _db_pool is None:
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        _db_pool = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=2,
            maxcached=10,
            blocking=True,
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT')),
            charset='utf8mb4',
            autocommit=True
        )
    return _db_pool

def get_db():
    """Get database connection from pool"""
    try:
        pool = _init_pool()
        return pool.connection()
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
