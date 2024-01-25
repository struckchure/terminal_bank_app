import sqlite3

conn = sqlite3.connect('bank_system.db')
cursor = conn.cursor()

# create users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        account_number INTEGER NOT NULL UNIQUE,
        pin_salt TEXT NOT NULL,
        pin_hash TEXT NOT NULL
    )
''')

# create banks table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Banks (
        bank_id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        type TEXT DEFAULT 'Verve' CHECK(type IN ('VISA', 'Verve', 'MasterCard'))
    )
''')

# create wallets table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Wallets (
        wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bank_id INTEGER,
        balance REAL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES Users(user_id),
        FOREIGN KEY (bank_id) REFERENCES Banks(bank_id)
    )
''')

# create transactions table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        wallet_id INTEGER,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (wallet_id) REFERENCES Wallets(wallet_id)
    )
''')

# commit changes and close the connection
conn.commit()
conn.close()
