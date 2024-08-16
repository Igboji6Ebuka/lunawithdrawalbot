import time
from terra_sdk.client.lcd import LCDClient
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.bank import MsgSend
from terra_sdk.core import Coins
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.exceptions import LCDResponseError
import requests

# Set up chain and LCD URL for Phoenix mainnet
lcd_url = "https://phoenix-lcd.terra.dev"
chain_id = "phoenix-1"

# Request current gas rates on Phoenix mainnet for fee estimation
gas_price_dict = requests.get("https://phoenix-fcd.terra.dev/v1/txs/gas_prices").json()

# Initialize LCDClient
terra = LCDClient(chain_id=chain_id, url=lcd_url)

# Your mnemonic and wallet initialization
mnemonic = "jelly depart logic animal tent client pink voice cement embrace omit guilt design flee news parade sphere machine occur tackle still possible across team"
mk = MnemonicKey(mnemonic)
wallet = terra.wallet(mk)

# Define the recipient address
recipient_address = "terra1llury9rt0dvc9u9ggg2eg24yp7faa38cv96cve"

while True:
    try:
        # Fetch balances
        balance_info = terra.bank.balance(wallet.key.acc_address)
        print(f"Balance info: {balance_info}")

        # Ensure we have valid balance data
        if not balance_info or len(balance_info) == 0:
            print("Error: balance_info is empty or None.")
            time.sleep(2)
            continue

        # Extract the balance of uluna
        if isinstance(balance_info, tuple):
            balance_info = balance_info[0]
            print(f"Extracted Coins object from tuple: {balance_info}")

        uluna_balance = next((coin for coin in balance_info if coin.denom == 'uluna'), None)

        if uluna_balance:
            available_balance = int(uluna_balance.amount)
            print(f"Available uluna balance: {available_balance}")

            # Set the amount to send as the entire available balance
            amount_to_send = available_balance

            if amount_to_send > 0:
                print(f"Amount to send: {amount_to_send}")

                # Ensure gas_prices is formatted correctly as a Coins object
                gas_prices = Coins(gas_price_dict)

                # Create transaction options
                tx_options = CreateTxOptions(
                    msgs=[
                        MsgSend(
                            from_address=wallet.key.acc_address,
                            to_address=recipient_address,
                            amount=Coins({'uluna': str(amount_to_send)})
                        )
                    ],
                    gas="auto",
                    gas_prices=gas_prices,
                    fee_denoms=["uluna"],
                    gas_adjustment=1.5
                )

                retry = True
                while retry:
                    try:
                        # Create and sign the transaction
                        tx = wallet.create_and_sign_tx(options=tx_options)
                        print("Transaction created and signed successfully.")

                        # Broadcast the transaction
                        result = terra.tx.broadcast_sync(tx)
                        print(f"Transaction hash: {result.txhash}")
                        print(f"Transaction details: {result}")

                        retry = False  # Exit retry loop after success

                    except LCDResponseError as e:
                        if "account sequence mismatch" in str(e):
                            print("Account sequence mismatch detected, retrying...")
                            # Update the sequence and retry
                            account_info = terra.auth.account_info(wallet.key.acc_address)
                            wallet.sequence = account_info.sequence
                        else:
                            print(f"Error broadcasting transaction: {e}")
                            retry = False  # Exit retry loop on other errors
                            break
            else:
                print("No uluna balance available to send.")
        else:
            print("No uluna balance found.")

    except LCDResponseError as e:
        print(f"LCD Error: {e}")
        if "503" in str(e):
            print("Service Unavailable. Retrying in 2 seconds...")
            time.sleep(2)  # Wait 2 seconds before retrying
        else:
            print(f"Error processing transaction: {e}")
            time.sleep(2)  # Wait before retrying on other errors

    time.sleep(2)  # Sleep before the next loop iteration
