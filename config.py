import pymysql
from dotenv import load_dotenv
import os #os is the Python module for interacting with the operating system.

load_dotenv()

print("Attempting to connect to MySQL...")
# Function to create a MySQL connection
def get_db_connection():
    mydb = pymysql.connect(
        host=os.getenv('mysql_host'),
        user=os.getenv('mysql_user'),
        password=os.getenv('mysql_password'),
        database=os.getenv('mysql_database'),
    )
    print("Successfully Connected")
    return mydb