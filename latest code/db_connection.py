# db_connection.py

import mysql.connector
from mysql.connector import Error

# Database configuration
db_config = {
    'user': 'root',
    'password': 'Sarvesh@4419',
    'host': 'localhost',
    'database': 'cloudjunebot'
}

def create_connection():
    """ Create a database connection to the MySQL database """
    connection = None
    try:
        connection = mysql.connector.connect(
            user=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            database=db_config['database']
        )
        if connection.is_connected():
            print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# Establish the database connection
db_connection = create_connection()
