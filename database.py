import pymysql
import os
import re

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return ''
    return re.sub(r'[<>"\';]', '', str(text).strip())

def get_db():
    """Get database connection"""
    try:
        # Ensure all required environment variables are set
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # SSL configuration - only use if DB_SSL is set to 'true'
        ssl_config = None
        if os.getenv('DB_SSL', 'false').lower() == 'true':
            ssl_config = {'ssl': True}
        
        return pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT')),
            charset='utf8mb4',
            autocommit=True,
            ssl=ssl_config
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None