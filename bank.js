const fs = require('fs');
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

let account = loadUserData();;

function saveUserData() {
    const dataToSave = JSON.stringify(account);
    fs.writeFileSync('userData.json', dataToSave);
  }

function loadUserData() {
  try {
    const data = fs.readFileSync('userData.json', 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    return [];
  }
}



function getUserAcct() {
  return new Promise(resolve => {
    rl.question("Input your account number? ", answer => {
      resolve(answer);
    });
  });
}

function getUserPin() {
    return new Promise(resolve => {
      rl.question("Enter Your PIN? ", answer => {
        resolve(answer);
      });
    });
  }

function selectOption(option) {
  switch (option) {
    case 1:
      createAccount();
      break;
    case 2:
      depositFunds();
      break;
    case 3:
      withdrawFunds();
      break;
    case 4:
      fundTransfer();
      break;
    case 5:
      checkStatement();
      break;
    case 6:
      fundHistory();
      break;
    default:
      console.log('Enter correct option');
  }
}

function optionsStatement() {
  console.log('1 Create Account');
  console.log('2 Deposit Money');
  console.log('3 Withdraw Money');
  console.log('4 Transfer Money');
  console.log('5 Check Statement');
  console.log('6 Transaction History');
}

optionsStatement();

rl.question('Enter your option: ', (optionInput) => {
  optionInput = parseInt(optionInput);

  if (!isNaN(optionInput) && optionInput >= 1 && optionInput <= 6) {
    loadUserData(); 
    selectOption(optionInput);
    saveUserData();
  } else {
    console.log('Enter correct option');
    rl.close();
  }

  
});

function accountNumbers() {
  return Math.floor(Math.random() * 1000000000);
}

function getPin() {
  return Math.floor(Math.random() * 10000);
}

function createAccount() {
    loadUserData(); 
    rl.question('Enter account name: ', (accountId) => {
      if (accountId.trim() === "") {
        console.log('Provide a unique name');
        rl.close();
      } else {
        console.log('Account created successfully');
        const newAccount = {
          accountName: accountId,
          accountNumber: accountNumbers(),
          pin: getPin(),
          funds: 0,
          transactions: []
        };
        saveUserData();
        account.push(newAccount);
        console.log('Your account name is ' + newAccount.accountName + '\nYour account number is ' + newAccount.accountNumber + '\nYour pin is ' + newAccount.pin);
        saveUserData();
        
  
        rl.close();
      }
    });
  }
  

function checkStatement() {
    loadUserData(); 
  getUserAcct().then(user => {
    const profile = account.find((userProfile) => userProfile.accountNumber == user);

    if (profile) {
      console.log('Hello ' + profile.accountName);
      console.log('Your account balance is: ' + profile.funds);
    } else {
      console.log('User not found');
    }

    rl.close();
  });
}

function depositFunds() {
    loadUserData(); 
  getUserAcct().then(user => {
    const profile = account.find((userProfile) => userProfile.accountNumber == user);

    if (profile) {
      rl.question('Enter the amount to deposit: ', (amount) => {
        amount = parseFloat(amount);

        if (!isNaN(amount) && amount > 0) {
          profile.funds += amount;
          const transactionText = `Deposit of ${amount} at ${new Date().toLocaleString()}`;
          profile.transactions.push(transactionText);
          saveUserData();
          console.log('Deposit successful. Your new balance is: ' + profile.funds);
        } else {
          console.log('Invalid amount');
        }

        rl.close();
      });
    } else {
      console.log('User not found');
      rl.close();
    }
  });
}

function withdrawFunds() {
loadUserData(); 
  getUserPin().then(user => {
    const profile = account.find((userProfile) => userProfile.pin == user);

    if (profile) {
      rl.question('Enter the amount to withdraw: ', (amount) => {
        amount = parseFloat(amount);

        if (!isNaN(amount) && amount > 0 && amount <= profile.funds) {
          profile.funds -= amount;
          const transactionText = `Withdrawal of ${amount} at ${new Date().toLocaleString()}`;
          profile.transactions.push(transactionText);
          saveUserData();
          console.log('Withdrawal successful. Your new balance is: ' + profile.funds);
        } else {
          console.log('Invalid amount or insufficient funds');
        }

        rl.close();
      });
    } else {
      console.log('User not found');
      rl.close();
    }
  });
}

function fundTransfer() {
    loadUserData(); 

    rl.question('Enter Recepient Account Number: ', (acct) => {
        const recepientAcct = account.find((userProfile) => userProfile.accountNumber == acct);

        if(recepientAcct){
            currentAcct = recepientAcct.funds
            console.log(recepientAcct.accountName)



            getUserAcct().then(user => {
                const profile = account.find((userProfile) => userProfile.accountNumber == user);
            
                if (profile) {
                  rl.question('Enter the amount to Transfer: ', (amount) => {
                    amount = parseFloat(amount);
            
                    if (!isNaN(amount) && amount > 0) {
                      recepientAcct.funds += amount;
                      const transactionText = `Credit of ${amount} from ${profile.accountName} at ${new Date().toLocaleString()}`;
                      recepientAcct.transactions.push(transactionText);
                      profile.funds -= amount
                      const transactionTextt = `Transfer of ${amount} to ${recepientAcct.accountName} at ${new Date().toLocaleString()}`;
                      profile.transactions.push(transactionTextt);
                      saveUserData();
                      console.log('Transfer successful. Your new balance is: ' + profile.funds);
                    } else {
                      console.log('Invalid amount');
                    }
            
                    rl.close();
                  });
                } else {
                  console.log('User not found');
                  rl.close();
                }
              });


        }else{
            console.log('User not found')
            rl.close();
        }
      });

    }
      
    

function fundHistory() {
   loadUserData(); 
  getUserAcct().then(user => {
    const profile = account.find((userProfile) => userProfile.accountNumber == user);

    if (profile) {
      console.log('Hello ' + profile.accountName);
      console.log('Your history is: ' + profile.transactions);
    } else {
      console.log('User not found');
    }

    rl.close();
  });
}
