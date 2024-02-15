import hashlib, sqlite3, secrets, requests, time, logging
from typing import Tuple, Optional, Dict, List, Any
from config import *


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Initialization manager
class Initialization:
    @staticmethod
    
    def create_database_tables():
        logging.info(f'Loading database: {DB_NAME}.')
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
        try: 
            logging.info(f'Loading bank data to Banks table from {API_URL}.')
            headers = {'Authorization': f'Bearer {API_SECRET_KEY}', 'Content-Type': 'application/json'}
            response = requests.get(API_URL, headers=headers)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute('''SELECT COUNT(*) FROM Banks''')
                    bank = cursor.fetchone()[0]
                    if bank == 0:
                        cursor.executemany('''
                            INSERT OR IGNORE INTO Banks (code, name) VALUES (?, ?)
                        ''', [(bank['code'], bank['name']) for bank in data])
                        conn.commit()
                        conn.close()
                        logging.info('Bank data successfully inserted')
                else:
                    logging.debug(f'No bank data found in the API response.')
            else:
                logging.error(f'Failed to fetch data from the API. Status code: {response.status_code}')
            time.sleep(5)
            logging.info("Starting main application...")
            time.sleep(2)
        except Exception as e:
            logging.error(f'An Error Occurred: {e}')


# Database manager
class DatabaseManager:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.conn = self._create_connection()

    def _create_connection(self):
        try:
            conn = sqlite3.connect(self.db_name)
            return conn
        except sqlite3.Error as e:
            print("Database Error:", str(e))
            return None

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Dict[str, Any]]]:
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if query.strip().lower().startswith(('select', 'pragma')):
                return self._fetch_rows(cursor)
            elif query.strip().lower().startswith(('insert', 'update', 'delete')):
                self.conn.commit()
                return None  # No rows to return for INSERT, UPDATE, DELETE
        except sqlite3.Error as e:
            print("Database Error:", str(e))
            return None

    def _fetch_rows(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
        
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

        # Create wallet for user 
        user_id = self.db_manager.execute_query('SELECT last_insert_rowid()')
        bank_id = self.db_manager.execute_query('SELECT bank_id FROM Banks WHERE bank_id = ?', (selected_bank_id,))
        
        self.db_manager.execute_query('''
            INSERT INTO Wallets (user_id, bank_id)
            VALUES (?, ?)
        ''', (next(iter(user_id[0].values())), next(iter(bank_id[0].values())),))
        
        print("\nUser registration successful.\n\n")
# Authentication manager 
            
class AuthManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def retrieve_password_hash(self, username: str) -> Tuple[Optional[str], Optional[str]]:
        query = 'SELECT pin_salt, pin_hash FROM Users WHERE username = ?'
        result = self.db_manager.execute_query(query, (username,))
        if result:
            first_row = result[0]  # Get the first dictionary in the list
            pin_salt, pin_hash = first_row.get('pin_salt'), first_row.get('pin_hash')
            return pin_salt, pin_hash
        else:
            print("\nUser not found in the database.")
            return None, None

    def authenticate_user(self, username: str, pin: str) -> bool:
        pin_salt, stored_pin_hash = self.retrieve_password_hash(username)
        if pin_salt is not None:
            provided_pin_with_salt = pin_salt + pin
            provided_pin_hash = hashlib.sha256(provided_pin_with_salt.encode()).hexdigest()
            print("Authentication successfull")
            return provided_pin_hash == stored_pin_hash
        else:
            print("Authentication failed")

# Account manager 
class AccountManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_user_info(self, identifier: str) -> Optional[Dict[str, str]]:
        query = '''
            SELECT Users.user_id, Users.username, Users.account_number, Wallets.wallet_id, Wallets.bank_id,
                Wallets.balance, Banks.code AS bank_code, Banks.name AS bank_name
            FROM Users
            JOIN Wallets ON Users.user_id = Wallets.user_id
            JOIN Banks ON Wallets.bank_id = Banks.bank_id
            WHERE Users.username = ? OR Users.account_number = ? OR Users.user_id = ?
        '''
        try:
            user_info = self.db_manager.execute_query(query, (identifier, identifier, identifier))

            if user_info:
                user = user_info[0]  # Get the first row from the result
                return {
                    'user_id': user.get('user_id'),
                    'username': user.get('username'),
                    'account_number': user.get('account_number'),
                    'wallet_id': user.get('wallet_id'),
                    'bank_id': user.get('bank_id'),
                    'balance': user.get('balance'),
                    'bank_code': user.get('bank_code'),
                    'bank_name': user.get('bank_name')
                }
            else:
                print("User not found.")
                return None
        except Exception as e:
            print("Error retrieving user information:", e)
            return None

    def get_banks(self):
        query = 'SELECT bank_id, name FROM Banks'
        try:
            banks = self.db_manager.execute_query(query)
            if banks:
                print("Available Banks:")
                for bank in banks:
                    print(f"{bank.get('bank_id')}: {bank.get('name')}")
            else:
                print("No banks found in the database.")
        except sqlite3.Error as e:
            print("Error fetching available banks:", str(e))

# Transaction manager 
class TransactionManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def deposit(self, account_number: str, amount: float, bank_id: int):
        query = '''
            UPDATE Wallets
            SET balance = balance + ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE account_number = ?
            ) AND bank_id = ?
        '''
        try:
            self.db_manager.execute_query(query, (amount, account_number, bank_id))
            print("Deposit successful.\n")
        except Exception as e:
            print("Error depositing funds:", e)

    def transfer(self, account_manager: AccountManager, username: str, recipient_account_number: str, bank_id: int, amount: float, description: str):
        
        sender = account_manager.get_user_info(username)
        receiver = account_manager.get_user_info(recipient_account_number)

        sender_user_id, sender_account_number = sender['user_id'], sender['account_number']
        sender_bank_id, sender_balance = sender['bank_id'], sender['balance']

        receiver_bank_id, receiver_user_id = receiver['bank_id'], receiver['user_id']

        update_receiver_balance_query = '''
            UPDATE Wallets
            SET balance = balance + ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE account_number = ?
            ) AND bank_id = ?
        '''
        update_sender_balance_query = '''
            UPDATE Wallets
            SET balance = balance - ?
            WHERE user_id = (
                SELECT user_id
                FROM Users
                WHERE username = ?
            )
        '''
        if sender_balance < amount:
            print("Insufficient balance.")
            return  # Exit the method if the balance is insufficient
            
        try:
            # Update receiver's balance
            self.db_manager.execute_query(update_receiver_balance_query, (amount, recipient_account_number, bank_id))
            # Deduct from sender's balance
            self.db_manager.execute_query(update_sender_balance_query, (amount, username))

            # Record the transaction
            self.record_transaction(sender_user_id, sender_account_number, receiver_user_id, recipient_account_number, amount, description, sender_bank_id, receiver_bank_id)
            print("\nTransfer Successful\n")
        except Exception as e:
            print("Error during transfer:", e)

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

    def transaction_history(self, account_manager, user_id):
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
        ''', (user_id,))

        if transaction_history:
            print("\nTransaction History:")
            for transaction in transaction_history:
                timestamp = transaction.get('timestamp')
                amount = transaction.get('amount')
                transaction_type = transaction.get('transaction_type')
                description = transaction.get('description')
                sender_account_number = transaction.get('sender_account_number')
                receiver_account_number = transaction.get('receiver_account_number')
                sender_bank_name = transaction.get('sender_bank_name')
                receiver_bank_name = transaction.get('receiver_bank_name')
                sender_username = transaction.get('sender_username')
                receiver_username = transaction.get('receiver_username')

                print(f"Timestamp: {timestamp}, Amount: {amount}, Type: {transaction_type}, Description: {description}")
                print(f"Sender Account Number: {sender_account_number}, Sender Bank: {sender_bank_name}, Sender Username: {sender_username}")
                print(f"Receiver Account Number: {receiver_account_number}, Receiver Bank: {receiver_bank_name}, Receiver Username: {receiver_username}\n")


        else:
            print("\nNo transaction history found.")

