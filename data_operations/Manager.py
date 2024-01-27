import hashlib, sqlite3, secrets, requests
from typing import Tuple, Optional, Dict, List
from config import *

# Initialization manager
class Initialization:
    @staticmethod
    def create_database_tables():
        # List of SQL queries to create tables
        create_table_queries = [
            '''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                account_number INTEGER NOT NULL UNIQUE,
                pin_salt TEXT NOT NULL,
                pin_hash TEXT NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Banks (
                bank_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS Wallets (
                wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                bank_id INTEGER,
                balance REAL DEFAULT 0,
                type TEXT DEFAULT 'Verve' CHECK(type IN ('VISA', 'Verve', 'MasterCard')),
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (bank_id) REFERENCES Banks(bank_id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS TransactionsHistory (
                transaction_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                amount REAL,
                transaction_type TEXT,
                description TEXT,
                sender_account_number TEXT,
                receiver_account_number TEXT,
                sender_bank_id INTEGER,
                receiver_bank_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                FOREIGN KEY (sender_bank_id) REFERENCES Banks(bank_id),
                FOREIGN KEY (sender_account_number) REFERENCES Users(account_number),
                FOREIGN KEY (receiver_account_number) REFERENCES Users(account_number),
                FOREIGN KEY (receiver_bank_id) REFERENCES Banks(bank_id)
            )
            '''
        ]

        # Connect to the database and create tables
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # Execute each query in the list
            for query in create_table_queries:
                cursor.execute(query)
            # Commit changes
            conn.commit()

    @staticmethod
    def load_bank_api():
        api_url = API_URL
        headers = {'Authorization': f'Bearer {API_SECRET_KEY}', 'Content-Type': 'application/json'}
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT OR IGNORE INTO Banks (code, name) VALUES (?, ?)
                ''', [(bank['code'], bank['name']) for bank in data])
                conn.commit()
                conn.close()
                print("Bank data successfully inserted.")
            else:
                print("No bank data found in the API response.")
        else:
            print(f"Failed to fetch data from the API. Status code: {response.status_code}")

# Database manager
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
            return None
        
# User manager 
        
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

        # user_id = self.db_manager.execute_query('SELECT last_insert_rowid()')[0]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        user_id = cursor.lastrowid

        cursor.execute('SELECT bank_id FROM Banks WHERE bank_id = ?', (selected_bank_id,))
        bank_row = cursor.fetchone()
        # Check if selected_bank_id exists
        # bank_row = self.db_manager.execute_query('SELECT bank_id FROM Banks WHERE bank_id = ?', (selected_bank_id,))
        if bank_row:
            bank_id = bank_row[0]
            self.db_manager.execute_query('''
                INSERT INTO Wallets (user_id, bank_id, balance, type)
                VALUES (?, ?, 0, 'Verve')
            ''', (user_id, bank_id))
            print("\nUser registration successful.\n\n")
        else:
            print("Invalid bank ID. User registration failed.\n\n")
# Authentication manager 
            
class AuthManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def retrieve_password_hash(self, username: str) -> Tuple[Optional[str], Optional[str]]:
        result = self.db_manager.execute_query('SELECT pin_salt, pin_hash FROM Users WHERE username = ?', (username,))
        if result:
            return result
        else:
            print("\nUser not found in the database.")
            return None, None

    def authenticate_user(self, username: str, pin: str) -> bool:
        pin_salt, stored_pin_hash = self.retrieve_password_hash(username)
        if pin_salt is not None:
            provided_pin_with_salt = pin_salt + pin
            provided_pin_hash = hashlib.sha256(provided_pin_with_salt.encode()).hexdigest()
            return provided_pin_hash == stored_pin_hash
        else:
            return False

# Account manager 
class AccountManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_account_info_by_username(self, username: str) -> Optional[Dict[str, str]]:
        result = self.db_manager.execute_query('''
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

    def get_user_info(self, identifier: str) -> Optional[Dict[str, str]]:
        result = self.db_manager.execute_query('''
            SELECT Users.user_id, Users.username, Users.account_number, Wallets.wallet_id, Wallets.bank_id,
                Wallets.balance, Banks.code AS bank_code, Banks.name AS bank_name
            FROM Users
            JOIN Wallets ON Users.user_id = Wallets.user_id
            JOIN Banks ON Wallets.bank_id = Banks.bank_id
            WHERE Users.username = ? OR Users.account_number = ? OR Users.user_id = ?
        ''', (identifier, identifier, identifier))

        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'account_number': result[2],
                'wallet_id': result[3],
                'bank_id': result[4],
                'balance': result[5],
                'bank_code': result[6],
                'bank_name': result[7]
            }
        else:
            print("User not found.")
            return None

    def get_account_balance(self, username: str) -> Optional[Dict[str, str]]:
        result = self.db_manager.execute_query('''
            SELECT Wallets.balance
            FROM Users
            JOIN Wallets ON Users.user_id = Wallets.user_id
            WHERE Users.username = ?
        ''', (username,))

        if result:
            return result[0]
        else:
            return 0

    def get_banks(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT bank_id, name FROM Banks')
            return cursor.fetchall()
        except sqlite3.Error as e:
            print("Error fetching available banks:", str(e))
        finally:
            conn.close()

# Transaction manager 
class TransactionManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def deposit(self, account_number: str, amount: float, bank_id: int):
        self.db_manager.execute_query('''
            UPDATE Wallets
            SET balance = balance + ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE account_number = ?
            ) AND bank_id = ?
        ''', (amount, account_number, bank_id))

    def transfer(self, account_manager, username, recipient_account_number: str, bank_id: int, amount: float, description: str):
        # add to balance 
        self.db_manager.execute_query('''
            UPDATE Wallets
            SET balance = balance + ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE account_number = ?
            ) AND bank_id = ?
        ''', (amount, recipient_account_number, bank_id))

        # deduct from account 
        self.db_manager.execute_query('''
            UPDATE Wallets
            SET balance = balance - ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE username = ?
            )
        ''', (amount, username))
        sender = account_manager.get_user_info(username)
        receiver = account_manager.get_user_info(recipient_account_number)

        sender_user_id = sender['user_id']
        sender_account_number = sender['account_number']
        sender_bank_id = sender['bank_id']
        receiver_bank_id = receiver['bank_id']
        receiver_user_id = receiver['user_id']

        self.record_transaction(sender_user_id, sender_account_number, receiver_user_id, recipient_account_number, amount, description, sender_bank_id, receiver_bank_id)
        
    def record_transaction(self, sender_user_id, sender_account_number, receiver_user_id, receiver_account_number, amount, description, sender_bank_id, receiver_bank_id):
        # Record the transaction in the database
        self.db_manager.execute_query('''
            INSERT INTO TransactionsHistory (user_id, timestamp, amount, transaction_type, description, sender_account_number, receiver_account_number, sender_bank_id, receiver_bank_id)
            VALUES (?, CURRENT_TIMESTAMP, ?, 'DEBIT', ?, ?, ?, ?, ?)
        ''', (sender_user_id, amount, description, sender_account_number, receiver_account_number, sender_bank_id, receiver_bank_id))

        # Record the receiver's transaction (CREDIT)
        self.db_manager.execute_query('''
            INSERT INTO TransactionsHistory (user_id, timestamp, amount, transaction_type, description, sender_account_number, receiver_account_number, sender_bank_id, receiver_bank_id)
            VALUES (?, CURRENT_TIMESTAMP, ?, 'CREDIT', ?, ?, ?, ?, ?)
        ''', (receiver_user_id, amount, description, sender_account_number, receiver_account_number, sender_bank_id, receiver_bank_id))

    def transaction_history(self, account_manager, username, pin):
        # Authenticate the user
        auth_manager = AuthManager(self.db_manager)
        if not auth_manager.authenticate_user(username, pin):
            print("Authentication failed.")
            return

        # Retrieve user_id based on username
        user_id = self.db_manager.execute_query('SELECT user_id FROM Users WHERE username = ?', (username,))
        if not user_id:
            print("User not found.")
            return

        # Retrieve transaction history for the user
        transaction_history = self.db_manager.execute_query('''
            SELECT th.timestamp, th.amount, th.transaction_type, th.description,
                th.sender_account_number, th.receiver_account_number,
                sb.name AS sender_bank_name, rb.name AS receiver_bank_name,
                su.username AS sender_username, ru.username AS receiver_username
            FROM TransactionsHistory th
            LEFT JOIN Banks sb ON th.sender_bank_id = sb.bank_id
            LEFT JOIN Banks rb ON th.receiver_bank_id = rb.bank_id
            LEFT JOIN Users su ON th.user_id = su.user_id
            LEFT JOIN Users ru ON th.user_id = ru.user_id
            WHERE th.user_id = ?
            ORDER BY th.timestamp DESC
        ''', (user_id[0],))

        if transaction_history:
            print("\nTransaction History:")
            for transaction in transaction_history:
                timestamp = transaction[0]
                amount = transaction[1]
                transaction_type = transaction[2]
                description = transaction[3]
                sender_account_number = transaction[4]
                receiver_account_number = transaction[5]
                sender_bank_name = transaction[6]
                receiver_bank_name = transaction[7]
                sender_username = transaction[8]
                # receiver_username = transaction[9]
                receiver_username = account_manager.get_user_info(sender_account_number)['username']

                print(f"Timestamp: {timestamp}, Amount: {amount}, Type: {transaction_type}, Description: {description}")
                print(f"Sender Account Number: {sender_account_number}, Sender Bank: {sender_bank_name}, Sender Username: {sender_username}")
                print(f"Receiver Account Number: {receiver_account_number}, Receiver Bank: {receiver_bank_name}, Receiver Username: {receiver_username}\n")


        else:
            print("\nNo transaction history found.")
