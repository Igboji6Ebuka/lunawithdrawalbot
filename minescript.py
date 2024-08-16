import time
from terra_classic_sdk.client.lcd import LCDClient
from terra_classic_sdk.client.lcd.api.tx import CreateTxOptions
from terra_classic_sdk.core.bank import MsgSend
from terra_classic_sdk.core import Coins
from terra_classic_sdk.key.mnemonic import MnemonicKey
from terra_classic_sdk.exceptions import LCDResponseError
from terra_classic_sdk.core.fee import Fee

# Set up chain and LCD URL for Terra Classic
lcd_url = "https://terra-classic-lcd.publicnode.com"
chain_id = "columbus-5"

# Initialize LCDClient
terra = LCDClient(chain_id=chain_id, url=lcd_url)

# Your mnemonic and wallet initialization
mnemonic ="jelly depart logic animal tent client pink voice cement embrace omit guilt design flee news parade sphere machine occur tackle still possible across team"
mk = MnemonicKey(mnemonic)
wallet = terra.wallet(mk)

# Define the recipient address
recipient_address ="terra1pgelevgcsch9a8dkn75269pf6m0var6qvpz6gs"

# Manually set gas price for uluna
manual_gas_prices = {'uluna': '0.015'}  # Adjust this based on current network conditions

# Define an even higher fee amount
fee_amount_str = '150000000uluna'  # Increased fee amount

while True:
    try:
        
        balance_info = terra.bank.balance(wallet.key.acc_address)
        print(f"Balance info: {balance_info}")

        
        if not balance_info or len(balance_info) == 0:
            print("Error: balance_info is empty or None.")
            time.sleep(2)
            continue

        
        if isinstance(balance_info, tuple):
            balance_info = balance_info[0]
            print(f"Extracted Coins object from tuple: {balance_info}")

        uluna_balance = next((coin for coin in balance_info if coin.denom == 'uluna'), None)

        if uluna_balance:
            available_balance = int(uluna_balance.amount)
            print(f"Available uluna balance: {available_balance}")

            
            fee_amount = int(fee_amount_str.replace('uluna', '')) 

            
            amount_to_send = available_balance - fee_amount

            if amount_to_send > 0:
                print(f"Amount to send: {amount_to_send}")
                print(f"Fee amount: {fee_amount}")

                
                tx_options = CreateTxOptions(
                    msgs=[
                        MsgSend(
                            from_address=wallet.key.acc_address,
                            to_address=recipient_address,
                            amount=Coins({'uluna': str(amount_to_send)})
                        )
                    ],
                    fee=Fee(
                        amount=Coins({'uluna': str(fee_amount)}), 
                        gas_limit=250000  
                    ),
                    gas="auto",
                    gas_prices=Coins(manual_gas_prices),
                    gas_adjustment=1.5
                )

                retry = True
                while retry:
                    try:
                        
                        tx = wallet.create_and_sign_tx(options=tx_options)
                        print("Transaction created and signed successfully.")

                        
                        result = terra.tx.broadcast_sync(tx)
                        print(f"Transaction hash: {result.txhash}")
                        print(f"Transaction details: {result}")

                        retry = False  

                    except LCDResponseError as e:
                        if "account sequence mismatch" in str(e):
                            print("Account sequence mismatch detected, retrying...")
                            
                            account_info = terra.auth.account_info(wallet.key.acc_address)
                            wallet.sequence = account_info.sequence
                        else:
                            print(f"Error broadcasting transaction: {e}")
                            retry = False  
                            break
            else:
                print("No uluna balance available to send after accounting for fees.")
        else:
            print("No uluna balance found.")

    except LCDResponseError as e:
        print(f"LCD Error: {e}")
        if "503" in str(e):
            print("Service Unavailable. Retrying in 2 seconds...")
            time.sleep(2) 
        else:
            print(f"Error processing transaction: {e}")
            time.sleep(2)  

    time.sleep(2)  
