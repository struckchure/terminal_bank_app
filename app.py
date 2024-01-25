import hashlib
import random
import sqlite3
import secrets

def get_available_banks():
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT bank_id, code, name FROM Banks')
        return cursor.fetchall()
    except sqlite3.Error as e:
        print("Error fetching available banks:", str(e))
    finally:
        conn.close()

def create_account():
    available_banks = get_available_banks()

    if available_banks:
        print("Available Banks:")
        for bank_id, bank_code, bank_name in available_banks:
            print(f"{bank_id}: {bank_name}")

        username = input("Enter a username (e.g JohnDoe): ")
        account_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        pin = input("Create 4-digit PIN: ")
        selected_bank_id = input("Enter the ID of the bank you want to register with: ")

        register_user(username, account_number, pin, selected_bank_id)

def register_user(username, account_number, pin, selected_bank_id):
    if not (username and account_number.isdigit() and len(account_number) == 10 and pin.isdigit() and len(pin) == 4):
        print("Invalid input. Please provide valid username, account number, and 4-digit PIN.")
        return

    pin_salt = secrets.token_hex(8)
    pin_with_salt = pin_salt + pin
    pin_hash = hashlib.sha256(pin_with_salt.encode()).hexdigest()

    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO Users (username, account_number, pin_salt, pin_hash)
            VALUES (?, ?, ?, ?)
        ''', (username, account_number, pin_salt, pin_hash))

        user_id = cursor.lastrowid

        cursor.execute('SELECT bank_id FROM Banks WHERE bank_id = ?', (selected_bank_id,))
        bank_row = cursor.fetchone()

        if bank_row:
            bank_id = bank_row[0]
            cursor.execute('''
                INSERT INTO Wallets (user_id, bank_id, balance, type)
                VALUES (?, ?, 0, 'Verve')
            ''', (user_id, bank_id))

            conn.commit()
            print("User registration successful.\n\n")
        else:
            print("Invalid bank ID. User registration failed.\n\n")
    except sqlite3.Error as e:
        print("Error registering user:", str(e))
    finally:
        conn.close()

def view_account_info(username, pin):
    # Retrieve salt and hash from the database for the user
    pin_salt, stored_pin_hash = retrieve_from_database(username)

    if pin_salt is not None:
        # Combine provided PIN with retrieved salt and hash it
        provided_pin_with_salt = pin_salt + pin
        provided_pin_hash = hashlib.sha256(provided_pin_with_salt.encode()).hexdigest()

        # Compare the provided hash with the stored hash for authentication
        if provided_pin_hash == stored_pin_hash:
            print("Authentication successful")
        else:
            print("Authentication failed")
            
        # Fetch and display user account information
        account_info = get_account_info_from_database(username)
        if account_info:
            print("\nAccount Information:")
            print(f"Username: {account_info['username']}")
            print(f"Account Number: {account_info['account_number']}")
            print(f"Balance: {account_info['balance']}")
            print(f"Bank: {account_info['bank_name']} ({account_info['bank_code']})\n")
        else:
            print("User does not exist.\n")
    else:
        print("Incorrect PIN.\n")
        
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
            return None, None  # Return default values when no data is found
    except sqlite3.Error as e:
        print("Error retrieving data from the database:", str(e))
        return None, None  # Return default values on error
    finally:
        conn.close()

def get_account_info_from_database(username):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT Users.username, Users.account_number, Wallets.balance, Banks.name AS bank_name, Banks.code AS bank_code
            FROM Users
            JOIN Wallets ON Users.user_id = Wallets.user_id
            JOIN Banks ON Wallets.bank_id = Banks.bank_id
            WHERE Users.username = ?
        ''', (username,))

        result = cursor.fetchone()

        if result:
            account_info = {
                'username': result[0],
                'account_number': result[1],
                'balance': result[2],
                'bank_name': result[3],
                'bank_code': result[4]
            }
            return account_info
        else:
            print("User not found in the database.")
            return None
    except sqlite3.Error as e:
        print("Error retrieving data from the database:", str(e))
        return None
    finally:
        conn.close()

def main():
    print("Welcome to the Terminal Bank App!\n")

    while True:
        print("Choose an option:")
        print("1. Create an Account")
        print("2. View Account Information")
        print("3. Transfer")
        print("4. Deposit")
        print("5. Transaction History")
        print("6. Exit")

        choice = input("Enter the number of your choice: ")

        if choice == "1":
            create_account()
        elif choice == "2":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            view_account_info(username, pin)
        elif choice == "6":
            print("Thank you for using the Terminal Bank App. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()
