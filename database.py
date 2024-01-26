import sqlite3

def create_database_tables(DB_NAME):
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
