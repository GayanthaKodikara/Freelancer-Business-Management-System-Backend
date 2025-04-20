import pymysql
from dotenv import load_dotenv
import os  # os is the Python module for interacting with the operating system.
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

logging.info("Attempting to connect to MySQL...")

# Function to create a MySQL connection
def get_db_connection():
    mydb = None
    try:
        mydb = pymysql.connect(
            host=os.getenv('mysql_host'),
            user=os.getenv('mysql_user'),
            password=os.getenv('mysql_password'),
            database=os.getenv('mysql_database'),
        )
        logging.info("Successfully Connected to MySQL")
        return mydb
    except pymysql.Error as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return None

# Example of how to use the connection (optional)
if __name__ == '__main__':
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            db_version = cursor.fetchone()
            logging.info(f"Database Version: {db_version[0]}")
            cursor.close()
        finally:
            connection.close()
            logging.info("Database connection closed")
    else:
        logging.error("Failed to establish database connection.")