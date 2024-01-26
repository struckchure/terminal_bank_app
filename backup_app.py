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
        account_number = ''.join([str(random.randint(0, 9)) for _ in range(5)])
        pin = input("Create 4-digit PIN: ")
        selected_bank_id = input("Enter the ID of the bank you want to register with: ")

        register_user(username, account_number, pin, selected_bank_id)

def register_user(username, account_number, pin, selected_bank_id):
    if not (username and account_number.isdigit() and len(account_number) == 5 and pin.isdigit() and len(pin) == 4):
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
            print("\nUser registration successful.\n\n")
        else:
            print("Invalid bank ID. User registration failed.\n\n")
    except sqlite3.Error as e:
        print("Error registering user:", str(e))
    finally:
        conn.close()

def view_account_info(username, pin):
    pin_salt, stored_pin_hash = retrieve_from_database(username)

    if pin_salt is not None:
        provided_pin_with_salt = pin_salt + pin
        provided_pin_hash = hashlib.sha256(provided_pin_with_salt.encode()).hexdigest()

        if provided_pin_hash == stored_pin_hash:
            print("Authentication successful")
        else:
            print("Authentication failed")
            return

        account_info = get_account_info_from_database(username)
        if account_info:
            print("\nAccount Information:")
            print(f"Username: {account_info['username']}")
            print(f"Account Number: {account_info['account_number']}")
            print(f"Balance: {account_info['balance']}")
            print(f"Bank: {account_info['bank_name']} ({account_info['bank_code']})")
            print(f"Bank ID: {account_info['bank_id']}\n")
        else:
            print("User does not exist.\n")
    else:
        print("Incorrect PIN.\n")

def retrieve_from_database(username):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT pin_salt, pin_hash FROM Users WHERE username = ?', (username,))
        result = cursor.fetchone()

        if result:
            return result
        else:
            print("User not found in the database.")
            return None, None
    except sqlite3.Error as e:
        print("Error retrieving data from the database:", str(e))
        return None, None
    finally:
        conn.close()

def get_account_info_from_database(username):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT Users.username, Users.account_number, Wallets.balance, Banks.name AS bank_name, Banks.code AS bank_code, Banks.bank_id AS bank_id
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
                'bank_code': result[4],
                'bank_id': result[5]
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

def deposit_money(account_number, bank_id, amount):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE Wallets
            SET balance = balance + ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE account_number = ?
            ) AND bank_id = ?
        ''', (amount, account_number, bank_id))
        conn.commit()
        print("Deposit successful.\n")
    except sqlite3.Error as e:
        print("Error depositing money:", str(e))
    finally:
        conn.close()


def initiate_transfer(username, recipient_account_number, bank_id, amount):
    recipient_exists = check_recipient_exists(recipient_account_number, bank_id)
    
    if not recipient_exists:
        print("\nInvalid Recipient Information.\n")
        return

    sender_balance = get_user_balance(username)

    if sender_balance < amount:
        print("Insufficient balance.")
        return

    deduct_from_balance(username, amount)
    add_to_balance(recipient_account_number, amount, bank_id)
    update_transaction_history(username, amount, "DEBIT")

    print("Transfer successful.")

def update_transaction_history(username, amount, type):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO Transactions (wallet_id, amount, type)
            VALUES (
                (SELECT wallet_id FROM Wallets WHERE user_id = ( SELECT user_id FROM Users WHERE username = ? )),
                ?, ? 
            )
        ''', (username, amount, type))
        conn.commit()
    except sqlite3.Error as e:
        print("Error updating transaction history:", str(e))
    finally:
        conn.close()

def add_to_balance(account_number, amount, bank_id):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE Wallets
            SET balance = balance + ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE account_number = ?
            ) AND bank_id = ?
        ''', (amount, account_number, bank_id))
        conn.commit()
    except sqlite3.Error as e:
        print("Error adding to balance:", str(e))
    finally:
        conn.close()

def deduct_from_balance(username, amount):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE Wallets
            SET balance = balance - ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE username = ?
            )
        ''', (amount, username))
        conn.commit()
    except sqlite3.Error as e:
        print("Error deducting from balance:", str(e))
    finally:
        conn.close()

def get_user_balance(username):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT Wallets.balance
            FROM Users
            JOIN Wallets ON Users.user_id = Wallets.user_id
            WHERE Users.username = ?
        ''', (username,))
        balance = cursor.fetchone()

        if balance:
            return balance[0]
        else:
            return 0
    except sqlite3.Error as e:
        print("Error getting user balance:", str(e))
        return 0
    finally:
        conn.close()

def check_recipient_exists(recipient_account_number, bank_id):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT user_id FROM Wallets WHERE user_id = ( SELECT user_id FROM Users WHERE account_number = ? )
            AND bank_id = ?
        ''', (recipient_account_number, bank_id))

        recipient_id = cursor.fetchone()

        if recipient_id:
            return True
        else:
            return False
    except sqlite3.Error as e:
        print("Error checking recipient:", str(e))
        return False
    finally:
        conn.close()

def get_transaction_history(username, pin):
    pin_salt, stored_pin_hash = retrieve_from_database(username)

    if pin_salt is not None:
        provided_pin_with_salt = pin_salt + pin
        provided_pin_hash = hashlib.sha256(provided_pin_with_salt.encode()).hexdigest()

        if provided_pin_hash == stored_pin_hash:
            print("Authentication successful")
        else:
            print("Authentication failed")
            return

        conn = sqlite3.connect('bank_system.db')
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT t.amount, t.type, t.timestamp
                FROM Transactions t
                JOIN Wallets w ON t.wallet_id = w.wallet_id
                JOIN Users u ON w.user_id = u.user_id
                WHERE u.username = ?
                ORDER BY t.timestamp DESC
            ''', (username,))

            transaction_history = cursor.fetchall()

            if transaction_history:
                print("\nTransaction History:")
                for transaction in transaction_history:
                    print(f"Amount: {transaction[0]}, Type: {transaction[1]}, Timestamp: {transaction[2]}")
                print("\n")
            else:
                print("No transaction history found.")
        except sqlite3.Error as e:
            print("Error retrieving transaction history:", str(e))
        finally:
            conn.close()
    else:
        print("Incorrect PIN.\n")

def main():
    print("Welcome to the Terminal Bank App!\n")

    while True:
        print("Choose an option:")
        print("1. Create an Account")
        print("2. View Account Information")
        print("3. Deposit")
        print("4. Transfer")
        print("5. Transaction History")
        print("6. Exit")

        choice = input("Enter the number of your choice: ")

        if choice == "1":
            create_account()
        elif choice == "2":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            view_account_info(username, pin)
        elif choice == "3":
            account_number = input("Enter your account number: ")
            bank_id = input("Enter your bank ID: ")
            amount = float(input("Enter the deposit amount: "))
            deposit_money(account_number, bank_id, amount)
        elif choice == "4":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            view_account_info(username, pin)
            print('\nEnter Recipient Information below')

            recipient_account_number = input("Recipient Account Number: ")
            bank_id = input("Recipient Bank ID: ")
            amount = float(input("Enter the transfer amount: "))
            initiate_transfer(username, recipient_account_number, bank_id, amount)
        elif choice == "5":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            get_transaction_history(username, pin)
        elif choice == "6":
            print("Thank you for using the Terminal Bank App. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()
