import hashlib
import random
import sqlite3

def authenticate_user(username, provided_pin):
    # Retrieve salt and hash from the database for the user
    pin_salt, stored_pin_hash = retrieve_from_database(username)

    # Combine provided PIN with retrieved salt and hash it
    provided_pin_with_salt = pin_salt + provided_pin
    provided_pin_hash = hashlib.sha256(provided_pin_with_salt.encode()).hexdigest()

    # Compare the provided hash with the stored hash for authentication
    if provided_pin_hash == stored_pin_hash:
        print("Authentication successful")
    else:
        print("Authentication failed")

def retrieve_from_database(username):
    # Fetch pin_salt and pin_hash from the database based on the username
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT pin_salt, pin_hash FROM Users WHERE username = ?', (username,))
        result = cursor.fetchone()

        if result:
            return result
        else:
            print("User not found in the database.")
            return None
    except sqlite3.Error as e:
        print("Error retrieving data from the database:", str(e))
        return None
    finally:
        conn.close()
