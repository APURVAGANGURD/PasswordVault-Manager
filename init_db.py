import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    """Create the database and tables"""
    try:
        # Connect to MySQL without specifying database
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            db_name = os.getenv('DB_NAME', 'password_vault')
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            logger.info(f"✅ Database '{db_name}' created or already exists")
            
            # Use the database
            cursor.execute(f"USE {db_name}")
            
            # Create users table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('Admin', 'Manager', 'User') NOT NULL DEFAULT 'User',
                mfa_enabled BOOLEAN DEFAULT FALSE,
                status ENUM('Active', 'Inactive', 'Suspended') NOT NULL DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            logger.info("✅ Table 'users' created successfully")
            
            # Show table structure
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            logger.info("📊 Table structure:")
            for column in columns:
                logger.info(f"   {column[0]} - {column[1]}")
            
            # Check if any users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            logger.info(f"👥 Total users in database: {count}")
            
            cursor.close()
            connection.close()
            logger.info("🎉 Database initialization completed successfully!")
            return True
            
    except Error as e:
        logger.error(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database initialization...")
    create_database()