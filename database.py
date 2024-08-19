import mysql.connector as mysql
import os
from datetime import datetime, timedelta
def init_db():
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'Sarvesh@4419'),
        'database': os.getenv('DB_NAME', 'cloudjunebot'),
    }

    try:
        db_connection = mysql.connect(**db_config)
    except mysql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        db_connection = None

    return db_connection

def get_or_create_user(db_connection, session_id):
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM users WHERE session_id = %s", (session_id,))
    user = cursor.fetchone()
    if user is None:
        cursor.execute("INSERT INTO users (session_id) VALUES (%s)", (session_id,))
        db_connection.commit()
        cursor.execute("SELECT id FROM users WHERE session_id = %s", (session_id,))
        user = cursor.fetchone()
    cursor.close()
    return user[0]

def get_available_slots(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("SELECT appointment_time FROM appointments")
    booked_slots = [row[0] for row in cursor.fetchall()]
    cursor.close()

    available_slots = []
    now = datetime.now()
    for i in range(7):  # Next 7 days
        date = now.date() + timedelta(days=i)
        for hour in range(9, 18):  # 9 AM to 5 PM
            slot = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour)
            if slot not in booked_slots:
                available_slots.append(slot.strftime("%Y-%m-%d %H:00"))

    return available_slots[:5]  # Return the first 5 available slots

def book_appointment(db_connection, user_id, appointment_time):
    try:
        cursor = db_connection.cursor()
        cursor.execute("INSERT INTO appointments (user_id, appointment_time) VALUES (%s, %s)", (user_id, appointment_time))
        db_connection.commit()
        cursor.close()
        print(f"Appointment booked: user_id={user_id}, appointment_time={appointment_time}")
    except mysql.Error as err:
        print(f"Error: {err}")

def store_conversation(db_connection, user_id, query, response):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO conversations (user_id, user_query, bot_response) VALUES (%s, %s, %s)", (user_id, query, response))
    db_connection.commit()
    cursor.close()
