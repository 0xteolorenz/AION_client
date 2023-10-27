# Author:  Matteo Lorenzato
# Date: 2023-08-26


import requests
import socketio
import trading_clients as tc
import dex_trading_client as dextc
import time
from typing import Any, Dict
import json

# Define terminal colors for visual cues
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
END_COLOR = '\033[0m'

sio = socketio.Client()
BASE_URL = 'http://localhost:5000'

def login(username: str, password: str) -> None:
    """
    Authenticate and establish a connection to the server.

    :param username: User's identification string.
    :param password: User's password string.
    """
    response = requests.post(f'{BASE_URL}/login_for_websocket', json={'username': username, 'password': password})
    if response.status_code == 200:
        user_id = response.json()['user_id']
        print(YELLOW + 'Login successful. user_id:' + END_COLOR, user_id)
        connect_to_socket(user_id)  # Connect to the socket with the received user ID
    else:
        print(RED + 'Login failed. Invalid username or password.' + END_COLOR)


def connect_to_socket(user_id: str) -> None:
    """
    Establish a connection to the server's socket and handle events.

    :param user_id: User's unique identification string.
    """
    @sio.event
    def on_connect() -> None:
        """Handle server connection event."""
        print(GREEN + 'Connected to the server.' + END_COLOR)
        sio.emit('join', {'room': user_id})  # Join the room with the received user ID

    @sio.on('new_updates')
    def handle_updates(data: Dict[str, Any]) -> None:
        """Handle incoming updates from the server.

        :param data: A dictionary containing new updates.
        """
        print('______New updates received______')
        for alert in data['data']:
            print(YELLOW + "ALERT TO EXECUTE:" + END_COLOR)
            print(alert)
            ticker_pair = alert['symbol']
            exchange = alert['exchange'].lower()

            if client_type == 'cex':
                if exchange in clients:
                    for subaccount, client in clients[exchange].items():
                        if client.supports_pair(ticker_pair):
                            order_info = client.process_order(alert)
                            print(GREEN + "ORDER INFO PROCESSED" + END_COLOR)
                            #print(order_info)
                            time.sleep(2)
                else:
                    print(RED + f"Received data for unsupported exchange: {exchange}" + END_COLOR)

            # Handling for DEX clients
            elif client_type == 'dex':
                dex_handled = False
                for account_name, dex_client in clients.items():
                    if dex_client.supports_pair(ticker_pair):
                        order_info = dex_client.process_order(alert)
                        print(GREEN + f"ORDER INFO PROCESSED FOR DEX ACCOUNT {account_name}:" + END_COLOR)
                        print(order_info)
                        time.sleep(2)
                        dex_handled = True

                if not dex_handled:
                    print(RED + f"Received data for unsupported ticker pair: {ticker_pair}" + END_COLOR)

    @sio.on('disconnect')
    def on_disconnect() -> None:
        """Handle server disconnection event."""
        print(RED + 'Disconnected from the server.' + END_COLOR)

    # Pass the user_id as a query parameter in the socket connection URL
    sio.connect(f'{BASE_URL}?user_id={user_id}')
    sio.wait()

def choose_client_type():
    while True:
        client_choice = input("Do you want to use CEX or DEX client? (cex/dex): ").strip().lower()
        if client_choice in ['cex', 'dex']:
            return client_choice
        else:
            print(RED + "Invalid choice. Please choose 'cex' or 'dex'." + END_COLOR)

def initialize_dex_clients(credentials):
    print(YELLOW + "Available DEX clients:" + END_COLOR)
    for idx, client in enumerate(credentials, 1):
        print(f"{idx}. {client['client_name']}")

    chosen_clients = {}
    
    while True:
        choice = input("Choose the DEX client by its number (or type 'done' to finish): ")

        if choice.lower() == 'done':
            break

        try:
            client_data = credentials[int(choice) - 1]

            # Further choice for which DEX to use
            print(YELLOW + "Supported DEX for " + client_data['client_name'] + END_COLOR)
            for idx, dex_name in enumerate(client_data["dex"], 1):
                print(f"{idx}. {dex_name}")

            dex_choice = int(input("Choose the DEX to use by its number: ")) - 1
            dex_name = client_data["dex"][dex_choice]

            # Initialize DEX client with chosen client_data
            client = dextc.DexTradingClient(client_data)

            # Use a dictionary to store your client, keyed by its client name.
            chosen_clients[client_data['client_name']] = client

            print(GREEN + f"{client_data['client_name']} added!" + END_COLOR)

        except (ValueError, IndexError):
            print(RED + "Invalid choice. Please try again." + END_COLOR)

    return chosen_clients


def start() -> None:
    """Start the application, prompting the user for credentials and initiating the login."""
    print(YELLOW + "CREDENTIALS FOR WEBHOOKS:" + END_COLOR)
    username = input('Enter username: ')
    password = input('Enter password: ')
    login(username, password)


client_type = choose_client_type()

if client_type == 'cex':
    test_mode = tc.choose_network_mode()
    chosen_exchanges = tc.choose_exchanges(test_mode)
    clients = {exchange: {subaccount: tc.TradingClient(exchange, subaccount, test_mode=test_mode) for subaccount in subaccounts} for exchange, subaccounts in chosen_exchanges.items()}

elif client_type == 'dex':
    with open('dex_credentials.json', 'r') as file:
        dex_configurations = json.load(file)

    clients = initialize_dex_clients(dex_configurations)


if __name__ == '__main__':
    start()
