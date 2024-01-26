from database import create_database_tables
import sqlite3, requests, config, time, os, platform

def bank_api(secret_key):
    api_url = config.API_URL
    headers = {'Authorization': f'Bearer {secret_key}', 'Content-Type': 'application/json'}
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        if data:
            conn = sqlite3.connect(config.DB_NAME)
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


def boot():
    # Perform initialization tasks here
    print("Initializing application...")
    # Create database
    create_database_tables(config.DB_NAME)
    # Load api data to bank table 
    bank_api(config.API_SECRET_KEY)
    print("Initialization successfully.")
    time.sleep(3)

# main.py

from boot import boot

def main():
    boot()  # Call the boot function
    # Start your main application logic here
    print("Starting main application...")
    time.sleep(5)
    os.system('cls' if platform.system() == 'Windows' else 'clear')

if __name__ == "__main__":
    main()