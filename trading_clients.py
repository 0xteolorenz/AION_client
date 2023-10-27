# Author:  Matteo Lorenzato
# Date: 2023-08-26


import ccxt
import json
import time
from typing import Dict, Tuple, Any, List, Optional, Union

# Define terminal colors for visual cues
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
END_COLOR = '\033[0m'


available_exchanges = ['bybit']


class TradingClient:
    def __init__(self, exchange_id: str, subaccount: str, test_mode: bool = False):
        """
        Initialize a trading client for the given exchange.

        :param exchange_id: Identifier for the desired exchange.
        :param subaccount: Name of the subaccount within the exchange.
        :param test_mode: Boolean indicating whether the client should operate in test mode.
        """
        credentials = self.load_credentials(exchange_id, subaccount, test_mode)
        self.pairs_supported = credentials["pair_supported"]
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': credentials['apiKey'],
            'secret': credentials['secret'],
            'enableRateLimit': True,
            'options': {
                'defaultType': credentials['market_type'],
                'adjustForTimeDifference': False,
                'tpslMode': 'Partial'
            },
        })

        if exchange_id == 'bybit':
            self.exchange.options['enableUnifiedAccount'] = True
            self.exchange.options['enableUnifiedMargin'] = True

        self.exchange.verbose = False
        self.exchange.timeout = 30000
        self.exchange.urls['api'] = self.get_url(test_mode)
        print(self.exchange.check_required_credentials())

        self.balance = self.get_balance()
        self.last_position_opened = {}
        self.init_position_contracts = {}

        print(YELLOW + "BALANCE USDT:" + END_COLOR)
        print(self.balance["USDT"])
        print(YELLOW + "POSITIONS OPEN:" + END_COLOR)
        for pair in self.pairs_supported:
            last_pos_opened = self.get_last_position_opened(pair)['info']['size']
            self.last_position_opened[pair] = float(last_pos_opened)
            self.init_position_contracts[pair] = self.last_position_opened[pair]
            print({pair: last_pos_opened})

        self.precision = {}
        self.are_pairs_supported_and_set_precision()

    def are_pairs_supported_and_set_precision(self):
        """
        Verifies if pairs are supported by the exchange and sets their precision.
        """
        markets = self.exchange.fetch_markets()
        supported_pairs = [market['symbol'] for market in markets]
        precision_dict = {market['symbol']: market['precision'] for market in markets}

        for pair in self.pairs_supported:
            if pair in supported_pairs:
                self.precision[pair] = len(str(precision_dict[pair]['amount']).split('.')[1])
                print(GREEN + f"{pair} is supported by the exchange! Amount Precision: {self.precision[pair]}" + END_COLOR)
            else:
                print(RED + f"{pair} is NOT supported by the exchange." + END_COLOR)

    def supports_pair(self, pair: str) -> bool:
        """
        Determine if a given trading pair is supported.

        :param pair: The trading pair string.
        :return: True if supported, False otherwise.
        """
        return pair in self.pairs_supported

    def get_balance(self) -> Dict[str, Any]:
        """
        Fetch the balance for the initialized exchange.

        :return: A dictionary containing balance details.
        """
        return self.exchange.fetch_balance({"type": "fund", "accountType": "UNIFIED"})

    def get_last_position_opened(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch the last position opened for the given symbol.

        :param symbol: Trading symbol.
        :return: A dictionary with details about the position.
        """
        return self.exchange.fetch_position(symbol)

    def get_url(self, test_mode: bool) -> str:
        """
        Get the appropriate URL based on the test mode status.

        :param test_mode: Boolean indicating if in test mode.
        :return: The URL string.
        """
        if test_mode:
            return self.exchange.urls['test']
        else:
            return self.exchange.urls['api']

    def load_credentials(self, exchange_id: str, subaccount: str, test_mode: bool) -> Dict[str, Any]:
        """
        Load the credentials for a given exchange and subaccount.

        :param exchange_id: Identifier for the desired exchange.
        :param subaccount: Name of the subaccount within the exchange.
        :param test_mode: Boolean indicating whether to load testnet credentials.
        :return: A dictionary containing the credentials.
        """
        with open('credentials.json', 'r') as file:
            credentials = json.load(file)
            if test_mode and f"{exchange_id}_testnet" in credentials:
                return credentials[f"{exchange_id}_testnet"]['sub_acc'][subaccount]
            else:
                return credentials[exchange_id]['sub_acc'][subaccount]

    def open_position_contracts(self, pair):
        """
        Fetch the number of contracts in an open position for the given trading pair.
        """
        # Retrieve all open positions
        open_position = self.last_position_opened[pair]>0

        if open_position:
            return self.last_position_opened[pair]  # or 'quantity' or other relevant key depending on the exchange
        else:
            return 0
        
    def max_contracts_to_buy(self, pair):
        """
        Calculate the maximum number of contracts that can be bought or sold.
        """
        quote_currency = get_quote_currency(pair)
        balance = self.balance[quote_currency]['free']
        contract_price = self.exchange.fetch_ticker(pair)['last']
        
        # Assuming balance is in the quote currency (e.g., USDT for BTC/USDT)
        #
        #quote_balance = balance['total'][quote_currency]
        max_contracts = balance / contract_price
        return max_contracts

    def contracts_for_percentage_to_open_pos(self, pair: str, percentage: float):
        """
        Calculate the number of contracts corresponding to a given percentage of max contracts.
        """
        return self.max_contracts_to_buy(pair) * (percentage / 100.5)
    
    def contracts_for_percentage_to_close_pos(self, pair, percentage, type_pos):
        """
        Calculate the number of contracts corresponding to a given percentage of max contracts.
        """
        if percentage < 100 and type_pos == 'limit':
            return self.open_position_contracts(pair) * (percentage / 100.0)
        elif percentage < 100 and type_pos == 'market':
            return float(self.get_last_position_opened(pair)['info']['size']) * (percentage / 100.0)
        elif percentage == 100:
            return float(self.get_last_position_opened(pair)['info']['size'])

            
    def process_order(self, strategy_dict: Dict[str, Any]) -> Any:
        """
        Process the order based on provided strategy.

        :param strategy_dict: A dictionary containing order details.
        :return: Executed order or a message indicating insufficient funds.
        """
        
        # Extract order details
        symbol, side, order_type, quantity_percent, price, reduce_only, stop_price, comment = self.extract_order_details(strategy_dict)
        
        # Validate extracted order details
        self.validate_order_details(symbol, side, order_type, quantity_percent, price, reduce_only)

        # Determine the number of contracts
        order_n_contracts = self.get_order_contracts(symbol, quantity_percent, reduce_only, order_type)
        
        # Execute order if valid contract number
        if order_n_contracts > 0:
            order = self.execute_order(symbol, side, order_type, order_n_contracts, price, reduce_only, stop_price)
            self.post_order_processing(symbol, order_n_contracts, reduce_only, comment)
            return order
        else:
            return RED + "Not sufficient funds to execute order" + END_COLOR
        
    def extract_order_details(self, strategy_dict: Dict[str, Any]) -> Tuple[str, str, str, float, float, bool, float, str]:
        """
        Extract order details from the strategy dictionary.

        :param strategy_dict: A dictionary containing order details.
        :return: Extracted order details.
        """
        
        keys = ['symbol', 'side', 'order_type', 'qty_perc', 'price', 'reduceOnly', 'stopPrice', 'comment']
        return (strategy_dict.get(key, None) for key in keys)

    def validate_order_details(self, *args: Any) -> None:
        """
        Validate the extracted order details.

        :param args: Extracted order details.
        :raise ValueError: If any of the required order parameters is missing.
        """
        
        if None in args:
            raise ValueError("One or more required order parameters are missing")

    def get_order_contracts(self, symbol: str, quantity_percent: float, reduce_only: bool, type_order: str) -> int:
        """
        Get the number of contracts based on the order strategy.

        :param symbol: Trading symbol.
        :param quantity_percent: Percentage of quantity.
        :param reduce_only: Whether to reduce only or not.
        :return: Number of contracts.
        """
        
        if reduce_only:
            return self.contracts_for_percentage_to_close_pos(symbol, quantity_percent, type_order)
        return self.contracts_for_percentage_to_open_pos(symbol, quantity_percent)

    def execute_order(self, symbol: str, side: str, order_type: str, order_n_contracts: int, price: float, reduce_only: bool, stop_price: float) -> Dict[str, Any]:
        """
        Execute the order based on provided details.

        :param symbol: Trading symbol.
        :param side: Order side ('buy' or 'sell').
        :param order_type: Type of order ('market', 'limit', or 'stopLimit').
        :param order_n_contracts: Number of contracts to order.
        :param price: Order price.
        :param reduce_only: Whether to reduce only or not.
        :param stop_price: Stop price for stop-limit orders.
        :return: Executed order.
        """
        
        if not reduce_only:
            print(YELLOW+'SENDING MARKET ORDER...'+END_COLOR)
            self.exchange.cancel_all_unified_account_orders(symbol)
            return self.exchange.create_order(symbol, order_type, side, order_n_contracts, None)
        elif stop_price:
            print(YELLOW+'SENDING STOPLOSS ORDER...'+END_COLOR)
            params = {'stopLossPrice': stop_price}
            return self.exchange.create_order(symbol, order_type, side, order_n_contracts, price, params)
        else:
            print(YELLOW+'SENDING TAKEPROFIT ORDER...'+END_COLOR)
            if order_type == 'limit':
                params = {'takeProfitPrice': price}
            else:
                params = {'reduceOnly': reduce_only}
            return self.exchange.create_order(symbol, order_type, side, order_n_contracts, price, params)

    def post_order_processing(self, symbol: str, order_n_contracts: int, reduce_only: bool, comment: str) -> None:
        """
        Process steps after the order is executed.

        :param symbol: Trading symbol.
        :param order_n_contracts: Number of contracts ordered.
        """
        
        time.sleep(1)

        if comment == 'openlong' or comment == 'openshort':
            self.last_position_opened[symbol] = float(self.get_last_position_opened(symbol)['info']['size'])
            self.init_position_contracts[symbol] = self.last_position_opened[symbol]
        elif comment == 'set take profit' or comment == 'closelong' or comment == 'closeshort':
            self.last_position_opened[symbol] += -order_n_contracts
        elif comment == 'closelong' or comment == 'closeshort':
            self.last_position_opened[symbol] = float(self.get_last_position_opened(symbol)['info']['size'])

        self.balance = self.get_balance()
        print(YELLOW+'New Balance:'+END_COLOR)
        quote_currency = get_quote_currency(symbol)
        balance = self.balance[quote_currency]["free"]
        print(balance)
        print(YELLOW+'Free position contracts:'+END_COLOR)
        print(self.last_position_opened[symbol])

    def fetch_active_orders(self) -> List[Dict[str, Union[str, float, int]]]:
        """
        Fetch the active orders from the exchange.

        :return: A list of active orders or an empty list if an error occurs.
        """
        try:
            return self.exchange.fetch_open_orders()
        except Exception as e:
            print(RED + f"An error occurred while fetching active orders: {e}" + END_COLOR)
            return []

    def fetch_wallet_balance(self) -> Optional[Dict[str, Union[str, float, int]]]:
        """
        Fetch the wallet balance from the exchange.

        :return: A dictionary containing wallet balance details or None if an error occurs.
        """
        try:
            return self.exchange.fetch_balance({"type": "fund", "accountType": "UNIFIED"})
        except Exception as e:
            print(RED + f"An error occurred while fetching the wallet balance: {e}" + END_COLOR)
            return None

    def fetch_last_n_profits_losses(self, n: int) -> List[float]:
        """
        Fetch the last 'n' profit and loss details from the exchange.

        :param n: The number of profit and loss details to retrieve.
        :return: A list of profits and losses or an empty list if an error occurs.
        """
        try:
            trades = self.exchange.fetch_my_trades(limit=n)
            profits_losses = [trade['profit'] for trade in trades if 'profit' in trade]
            return profits_losses
        except Exception as e:
            print(RED + f"An error occurred while fetching the last {n} profits and losses: {e}" + END_COLOR)
            return []
        
# FUNCTIONS

def choose_network_mode() -> bool:
    """
    Prompt the user to decide if they want to use the test network.

    :return: True if the user wants to use the test network, otherwise False.
    """
    choice = input("Do you want to use the test network? (yes/no): ").strip().lower()
    return choice == 'yes'

def choose_exchanges(test_mode: bool) -> Dict[str, List[str]]:
    """
    Prompt the user to choose the exchanges they want to activate.

    :param test_mode: A boolean indicating if the user is in test mode.
    :return: A dictionary where keys are exchanges and values are lists of subaccounts.
    """
    print("Please choose exchanges to activate:")
    for idx, exchange in enumerate(available_exchanges):
        print(f"{idx + 1}. {exchange}")

    chosen_exchanges = {}
    while True:
        chosen_exchange = ""
        chosen_subaccounts = []
        choice = input("Enter the number of the exchange ('done' to finish): ")
        if choice == 'done':
            break
        try:
            exchange_idx = int(choice) - 1
            chosen_exchange = available_exchanges[exchange_idx]
            if test_mode:
                # Adding '_testnet' to the exchange name when retrieving subaccounts in test mode
                chosen_subaccounts = choose_subaccounts(chosen_exchange + "_testnet")
            else:
                chosen_subaccounts = choose_subaccounts(chosen_exchange)
            chosen_exchanges[chosen_exchange] = chosen_subaccounts
            print(YELLOW + "Exchange apis chosen:" + END_COLOR)
            print(chosen_exchanges)
        except (ValueError, IndexError):
            print("Invalid choice. Please try again.")

    return chosen_exchanges

def choose_subaccounts(exchange: str) -> List[str]:
    """
    Prompt the user to choose the subaccounts for a given exchange.

    :param exchange: The name of the exchange.
    :return: A list of chosen subaccounts for the given exchange.
    """
    print(f"Please choose subaccounts for {exchange}:")
    with open('credentials.json', 'r') as file:
        credentials = json.load(file)
        subaccounts = list(credentials[exchange]['sub_acc'].keys())
        for subaccount in subaccounts:
            print(f"- {subaccount}")

    chosen_subaccounts = []
    while True:
        choice = input("Enter the name of the subaccount ('done' to finish): ")
        if choice.lower() == 'done':
            break
        if choice in subaccounts:
            chosen_subaccounts.append(choice)
        else:
            print("Invalid choice. Please try again.")

    return chosen_subaccounts

def get_quote_currency(pair: str) -> str:
    """
    Extract the quote currency from a given trading pair.

    :param pair: The trading pair string.
    :return: The quote currency from the trading pair.
    """
    # Check if there's a ':' separator and extract the part after it
    if ':' in pair:
        return pair.split(":")[1]
    
    # If not, split on '/' to get quote currency
    return pair.split("/")[1]