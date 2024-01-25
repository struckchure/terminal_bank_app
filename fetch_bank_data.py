import sqlite3
import requests

def fetch_banks_data(secret_key):
    api_url = "https://api.flutterwave.com/v3/banks/NG"
    headers = {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json',
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        # print(response.json())
        return response.json()
    else:
        print(f"Failed to fetch data from the API. Status code: {response.status_code}")
        return None
    

def insert_banks_data(data):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    for bank in data:
        cursor.execute('''
            INSERT OR IGNORE INTO Banks (code, name)
            VALUES (?, ?)
        ''', (bank['code'], bank['name']))

    conn.commit()
    conn.close()

bank_data = fetch_banks_data('FLWSECK_TEST-cfb8a9a23ed548e354984f2334ab0cc2-X')['data']

if bank_data:
    insert_banks_data(bank_data)
    print("Bank data successfully inserted.")
else:
    print("Failed to fetch bank data from the API.")