import os, platform, random, time
from typing import Tuple, Optional, Dict, List
from data_operations.Manager import *
from config import *

print("Initializing application...")
initialization = Initialization()
# Create database
initialization.create_database_tables()
# Load api data to bank table 
try:
    initialization.load_bank_api()
    print("Initialization successfully.")
except Exception:
    print("Initialization failed.")
time.sleep(3)
print("Starting main application..."), time.sleep(5)
os.system('cls' if platform.system() == 'Windows' else 'clear')
# Main function 
def main():
    db_manager = DatabaseManager()
    user_manager = UserManager(db_manager)
    auth_manager = AuthManager(db_manager)
    account_manager = AccountManager(db_manager)
    transaction_manager = TransactionManager(db_manager)
    
    print("Welcome to the Terminal Bank App!")

    while True:
        print("\nChoose an option:")
        print("1. Create an Account")
        print("2. View Account Information")
        print("3. Deposit")
        print("4. Transfer")
        print("5. Transaction History")
        print("6. Exit\n")

        choice = input("Enter the number of your choice: ")

        if choice == "1":
            username = input("Enter a username (e.g JohnDoe): ")
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(5)])
            pin = input("Create 4-digit PIN: ")
            try:
                banks = account_manager.get_banks()
                if banks:
                    print("Available Banks:")
                    for bank in banks:
                        print(f"{bank[0]}: {bank[1]}")
                    selected_bank_id = input("Enter the ID of the bank you want to register with: ")
                else:
                    print("No banks found in the database.")
            except Exception as e:
                print(f"Error fetching banks from the database: {e}")

            user_manager.register_user(username, account_number, pin, int(selected_bank_id))

        elif choice == "2":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            if auth_manager.authenticate_user(username, pin):
                account_info = account_manager.get_user_info(username)
                if account_info:
                    print("\nAccount Information:")
                    print(f"Username: {account_info['username']}")
                    print(f"Account Number: {account_info['account_number']}")
                    print(f"Balance: {account_info['balance']}")
                    print(f"Bank Name: {account_info['bank_name']} ({account_info['bank_code']})")
                    print(f"Bank ID: {account_info['bank_id']}\n")
            else:
                print("Authentication failed")

        elif choice == "3":
            account_number = input("Enter your account number: ")
            bank_id = input("Enter your bank ID: ")
            amount = float(input("Enter the deposit amount: "))
            transaction_manager.deposit(account_number, amount, int(bank_id))
            print("Deposit successful.\n")

        elif choice == "4":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            if auth_manager.authenticate_user(username, pin):
                print("\nAuthentication Successful\n")
                bank_id = input("Enter Recipient Bank ID: ")
                recipient_account_number = input("Enter Recipient Account Number: ")
                recipient_account_info = account_manager.get_user_info(recipient_account_number)
                sender_account_balance = account_manager.get_account_balance(username)
                if recipient_account_info:
                    print("\nConfirm Account Information:")
                    print(f"Username: {recipient_account_info['username']}")
                    print(f"Account Number: {recipient_account_info['account_number']}")
                    print(f"Balance: {recipient_account_info['balance']}")
                    print(f"Bank Name: {recipient_account_info['bank_name']} ({recipient_account_info['bank_code']})")
                    print(f"Bank ID: {recipient_account_info['bank_id']}\n")

                    amount = float(input("Enter Transfer Amount: "))
                    description = input("Add Description (Optional): ")
                    if sender_account_balance < amount:
                        print("Insufficient balance.")
                    transaction_manager.transfer(account_manager, username, recipient_account_number, bank_id, amount, description)
                    print("\nTransfer Successful\n")
            else:
                print("Authentication failed")

        elif choice == "5":
            username = input("Enter your username: ")
            pin = input("Enter 4-digit PIN: ")
            transaction_manager.transaction_history(account_manager, username, pin)
                
        elif choice == "6":
            print("Thank you for using the Terminal Bank App. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

        another_action = input("Would you like to perform another action? (Y/n): ")
        if another_action.lower() != 'y':
            print("Exiting...")
            break

if __name__ == "__main__":
    main()