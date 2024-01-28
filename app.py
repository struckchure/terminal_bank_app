import os, platform, random, time
from typing import Tuple, Optional, Dict, List
from data_operations.Manager import *
from config import *

# print(f"Initializing Database: {DB_NAME}")
# initialization = Initialization()
# # Create database
# initialization.create_database_tables()
# # Load api data to bank table 
# try:
#     initialization.load_bank_api()
#     print("Initialization successfully.")
# except Exception:
#     print("Initialization failed.")
# time.sleep(2)
# print("Starting main application..."), time.sleep(2)
# os.system('cls' if platform.system() == 'Windows' else 'clear')

options = ["Create an Account", "View Account Information", "Deposit", "Transfer", "Transaction History", "Exit\n"]
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
        for index, option in enumerate(options, start=1):
            print(f"{index}. {option}")

        choice = input("Enter the number of your choice: ")

        if choice == "1":
            username, pin = input("Enter a username: "), input("Create 4-digit PIN: ") # username, pin
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(5)]) # autogenerated account number
            account_manager.get_banks() # get list of banks
            selected_bank_id = input("Enter the ID of the bank you want to register with: ") # bank id selected
            user_manager.register_user(username, account_number, pin, int(selected_bank_id)) # create user -> bank -> wallet

        elif choice == "2":
            username, pin = input("Enter your username: "), input("Enter 4-digit PIN: ")
            auth_manager.authenticate_user(username, pin)
            account_info = account_manager.get_user_info(username)
            print("\nAccount Information:"), _account_info(account_info)

        elif choice == "3":
            account_number, bank_id = input("Enter your account number: "), input("Enter your bank ID: ")
            amount = float(input("Enter the deposit amount: "))
            transaction_manager.deposit(account_number, amount, int(bank_id))

        elif choice == "4":
            username, pin = input("Enter your username: "), input("Enter 4-digit PIN: ")
            auth_manager.authenticate_user(username, pin)
            bank_id = input("Enter Recipient Bank ID: ")
            recipient_account_number = input("Enter Recipient Account Number: ")
            recipient_account_info = account_manager.get_user_info(recipient_account_number)
            print("\nConfirm Account Information:"), _account_info(recipient_account_info)

            amount, description = float(input("Enter Transfer Amount: ")), input("Add Description (Optional): ")
            transaction_manager.transfer(account_manager, username, recipient_account_number, bank_id, amount, description)

        elif choice == "5":
            username, pin = input("Enter your username: "), input("Enter 4-digit PIN: ")
            auth_manager.authenticate_user(username, pin)
            user_id = account_manager.get_user_info(username)['user_id']
            transaction_manager.transaction_history(account_manager, user_id)
                
        elif choice == "6":
            _exit()
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

        another_action = input("Would you like to perform another action? (Y/n): ")
        if another_action.lower() != 'y':
            _exit()
            break

def _account_info(param):
    print(f"Username: {param['username']}")
    print(f"Account Number: {param['account_number']}")
    print(f"Balance: {param['balance']}")
    print(f"Bank Name: {param['bank_name']} ({param['bank_code']})")
    print(f"Bank ID: {param['bank_id']}\n")

def _exit():
    print("Thank you for using the Terminal Bank App. Goodbye...!")
    time.sleep(2)
    os.system('cls' if platform.system() == 'Windows' else 'clear')


if __name__ == "__main__":
    main()