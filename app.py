import hashlib
import random
import sqlite3
import secrets
from typing import Tuple, Optional, Dict, List


class DatabaseManager:
    def __init__(self, db_name: str = 'bank_system.db'):
        self.db_name = db_name
        self.conn = self._create_connection()

    def _create_connection(self):
        try:
            conn = sqlite3.connect(self.db_name)
            return conn
        except sqlite3.Error as e:
            print("Database Error:", str(e))
            return None

    def execute_query(self, query: str, params: Optional[Tuple] = None):
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
        except sqlite3.Error as e:
            print("Database Error:", str(e))

    def fetch_query(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except sqlite3.Error as e:
            print("Database Error:", str(e))
            return None

    def fetch_all_query(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Tuple]]:
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print("Database Error:", str(e))
            return None



class UserManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def register_user(self, username: str, account_number: str, pin: str, selected_bank_id: int):
        # Validate input
        if not (username and account_number.isdigit() and len(account_number) == 5 and pin.isdigit() and len(pin) == 4):
            print("Invalid input. Please provide valid username, account number, and 4-digit PIN.")
            return

        pin_salt = secrets.token_hex(8)
        pin_with_salt = pin_salt + pin
        pin_hash = hashlib.sha256(pin_with_salt.encode()).hexdigest()

        # Insert user into database
        self.db_manager.execute_query('''
            INSERT INTO Users (username, account_number, pin_salt, pin_hash)
            VALUES (?, ?, ?, ?)
        ''', (username, account_number, pin_salt, pin_hash))

        user_id = self.db_manager.fetch_query('SELECT last_insert_rowid()')[0]

        # Check if selected_bank_id exists
        bank_row = self.db_manager.fetch_query('SELECT bank_id FROM Banks WHERE bank_id = ?', (selected_bank_id,))
        if bank_row:
            bank_id = bank_row[0]
            self.db_manager.execute_query('''
                INSERT INTO Wallets (user_id, bank_id, balance, type)
                VALUES (?, ?, 0, 'Verve')
            ''', (user_id, bank_id))
            print("\nUser registration successful.\n\n")
        else:
            print("Invalid bank ID. User registration failed.\n\n")


class AuthManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def retrieve_password_hash(self, username: str) -> Tuple[Optional[str], Optional[str]]:
        result = self.db_manager.fetch_query('SELECT pin_salt, pin_hash FROM Users WHERE username = ?', (username,))
        if result:
            return result
        else:
            print("User not found in the database.")
            return None, None

    def authenticate_user(self, username: str, pin: str) -> bool:
        pin_salt, stored_pin_hash = self.retrieve_password_hash(username)
        if pin_salt is not None:
            provided_pin_with_salt = pin_salt + pin
            provided_pin_hash = hashlib.sha256(provided_pin_with_salt.encode()).hexdigest()
            return provided_pin_hash == stored_pin_hash
        else:
            return False


class AccountManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_account_info(self, username: str) -> Optional[Dict[str, str]]:
        result = self.db_manager.fetch_query('''
            SELECT Users.username, Users.account_number, Wallets.balance, Banks.name AS bank_name, 
            Banks.code AS bank_code, Banks.bank_id AS bank_id
            FROM Users
            JOIN Wallets ON Users.user_id = Wallets.user_id
            JOIN Banks ON Wallets.bank_id = Banks.bank_id
            WHERE Users.username = ?
        ''', (username,))
        if result:
            return {
                'username': result[0],
                'account_number': result[1],
                'balance': result[2],
                'bank_name': result[3],
                'bank_code': result[4],
                'bank_id': result[5]
            }
        else:
            print("User not found in the database.")
            return None


class TransactionManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_to_balance(self, account_number: str, amount: float, bank_id: int):
        self.db_manager.execute_query('''
            UPDATE Wallets
            SET balance = balance + ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE account_number = ?
            ) AND bank_id = ?
        ''', (amount, account_number, bank_id))

    # Implement other transaction related methods...


def main():
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    auth_manager = AuthManager(db_manager)
    account_manager = AccountManager(db_manager)
    transaction_manager = TransactionManager(db_manager)

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
            username = input("Enter a username (e.g JohnDoe): ")
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(5)])
            pin = input("Create 4-digit PIN: ")
            selected_bank_id = input("Enter the ID of the bank you want to register with: ")

            user_manager.register_user(username, account_number, pin, int(selected_bank_id))

        elif choice == "2":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            if auth_manager.authenticate_user(username, pin):
                account_info = account_manager.get_account_info(username)
                if account_info:
                    print("\nAccount Information:")
                    print(f"Username: {account_info['username']}")
                    print(f"Account Number: {account_info['account_number']}")
                    print(f"Balance: {account_info['balance']}")
                    print(f"Bank: {account_info['bank_name']} ({account_info['bank_code']})")
                    print(f"Bank ID: {account_info['bank_id']}\n")
            else:
                print("Authentication failed")

        elif choice == "3":
            account_number = input("Enter your account number: ")
            bank_id = input("Enter your bank ID: ")
            amount = float(input("Enter the deposit amount: "))
            transaction_manager.add_to_balance(account_number, amount, int(bank_id))
            print("Deposit successful.\n")

        elif choice == "4":
            # Implement transfer logic using transaction_manager
            pass

        elif choice == "5":
            # Implement transaction history retrieval logic using transaction_manager
            pass

        elif choice == "6":
            print("Thank you for using the Terminal Bank App. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 6.")


if __name__ == "__main__":
    main()