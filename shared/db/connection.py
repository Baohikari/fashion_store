import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", 'localhost'),
        user=os.getenv("MYSQL_USER", 'root'),
        password=os.getenv("MYSQL_PASSWORD",''),
        database=os.getenv("MYSQL_DATABASE", "fashion_store")
    )