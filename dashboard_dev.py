import psycopg2
from dotenv import load_dotenv
import os

# load environment variables from .env file
load_dotenv()

# fetch variable
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DBNAME = os.getenv("DBNAME")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")

# Connect to the database
try:
    connection = psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        user=USER,
        password=PASSWORD,
        sslmode='require'
    )
    print("Wired On.")

    # Create a cursor to excecute SQL queries
    cursor = connection.cursor()

    # Example query
    cursor = connection.cursor()
    cursor.execute("SELECT NOW();")
    print("Server time:", cursor.fetchone()[0])

except Exception as e:
    print("something happened:", e)