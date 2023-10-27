import json
import os
from web3 import Web3
from termcolor import colored

class DexTradingClient:
    """
    A client for interacting with decentralized exchanges (DEX) and managing token trades.

    Attributes:
    - client_name (str): Name of the client.
    - public_key (str): Public Ethereum address of the client.
    - private_key (str): Private key for the Ethereum address (used for signing transactions).
    - infura_url (str): URL endpoint for the Infura Ethereum node service.
    - web3 (Web3 instance): Web3 instance to interact with the Ethereum blockchain.
    - dex (str): The name or identifier of the DEX.
    - tokens (dict): Information about supported tokens.
    - token_symbols (list): List of token symbols extracted from the tokens dictionary.
    - supported_pairs (list): Trading pairs that are supported by this client.
    - token_abis (dict): ABIs for the supported tokens.
    """

    def __init__(self, client_data):
        """
        Initialize the DEX trading client with provided data.

        Args:
        - client_data (dict): Data needed to initialize the client, including client name, keys, Infura URL, DEX, and tokens.
        """
        self.client_name = client_data["client_name"]
        self.public_key = client_data["public_key"]
        self.private_key = client_data["private_key"]
        self.infura_url = client_data["infura_url"]
        self.web3 = Web3(Web3.HTTPProvider(self.infura_url))
        self.dex = client_data["dex"]
        self.tokens = client_data["tokens"]
        self.token_symbols = list(self.tokens.keys())
        self.supported_pairs = self.generate_supported_pairs(self.tokens)
        self.token_abis = self.load_token_abis(self.token_symbols)

        for token_symbol, data in self.tokens.items():
            self.validate_token_address_with_abi(token_symbol, data['contract_address'])

        self.display_balances()

    def validate_token_address_with_abi(self, token_symbol: str, token_address: str):
        """
        Validate that a given token address returns the expected symbol using its ABI.

        Args:
        - token_symbol (str): Expected symbol of the token.
        - token_address (str): Ethereum address of the token contract.

        Raises:
        - ValueError: If the fetched symbol doesn't match the expected one or if the symbol couldn't be fetched.
        """
        expected_symbol = token_symbol.upper()
        fetched_symbol = get_token_symbol(self.web3, token_address, self.token_abis[token_symbol])
        
        if not fetched_symbol:
            raise ValueError(f"Failed to fetch symbol for address {token_address}. ABI might be incorrect.")
        
        if fetched_symbol != expected_symbol:
            raise ValueError(f"Symbol mismatch! Expected {expected_symbol} but got {fetched_symbol} for address {token_address}.")

    def generate_supported_pairs(self, tokens: dict) -> list:
        """
        Generate a list of supported trading pairs based on provided tokens.

        Args:
        - tokens (dict): Dictionary of supported tokens.

        Returns:
        - list: All possible unique trading pairs created from the token list.
        """
        token_names = list(tokens.keys())
        pairs = [f"{token1}/{token2}" for idx, token1 in enumerate(token_names) for token2 in token_names[idx+1:]]
        return pairs

    def supports_pair(self, pair: str) -> bool:
        """
        Check if a given trading pair is supported by the client.

        Args:
        - pair (str): Trading pair to check (e.g., "ETH/BTC").

        Returns:
        - bool: True if the pair is supported, otherwise False.
        """
        return pair in self.supported_pairs


    def load_token_abis(self, tokens: list) -> dict:
        """
        Load ABIs (Application Binary Interfaces) for the given tokens.
        
        Args:
        - tokens (list): List of token symbols to fetch ABIs for.
        
        Returns:
        - dict: Dictionary mapping token symbols to their respective ABIs.
        """
        abis = {}
        for token in tokens:
            # Convert the token to uppercase when opening the file
            with open(f'ABI/tokens/{token.upper()}.json', 'r') as file:
                abis[token] = json.load(file)
        return abis

    def display_balances(self):
        """
        Display the balances of all supported tokens, including Ethereum, for the current user.

        Prints:
        - Ethereum balance.
        - Balance for each supported token.
        """
        print(colored("Balances for client: " + self.client_name, 'yellow'))
        
        # Fetch and display Ethereum (ETH) balance
        eth_balance = self.web3.from_wei(self.web3.eth.get_balance(self.public_key), 'ether')
        print(colored(f"ETH: {eth_balance} Ether", 'green'))

        # Fetch and display balances for all supported tokens
        for token_symbol, token_data in self.tokens.items():
            balance = self.fetch_token_balance(token_symbol)
            readable_balance = self.web3.from_wei(balance, 'ether')  # Assumes tokens have 18 decimals like Ether
            print(colored(f"{token_symbol}: {readable_balance}", 'green'))

    def fetch_token_balance(self, token_symbol: str) -> float:
        """
        Fetch the balance of a specific token for the current user.

        Args:
        - token_symbol (str): Symbol of the token to fetch the balance for.

        Returns:
        - float: Balance of the token for the current user in the smallest denomination (e.g., wei for ETH-based tokens).

        Raises:
        - ValueError: If the provided token_symbol is not supported.
        """
        if token_symbol not in self.tokens:
            raise ValueError(f"Token '{token_symbol}' not supported.")
        
        token_address = self.tokens[token_symbol]['contract_address']
        token_abi = self.token_abis[token_symbol]
            
        token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
        return token_contract.functions.balanceOf(self.public_key).call()

    def simulate_swap(self, token_in_address: str, token_out_address: str, amount_in: float) -> float:
        """
        Simulate a token swap on Uniswap to get the expected output amount.

        Args:
        - token_in_address (str): Ethereum address of the input token.
        - token_out_address (str): Ethereum address of the output token.
        - amount_in (int): Amount of the input token to swap.

        Returns:
        - float: Expected output amount after performing the swap.
        """
        amounts_out = self.uniswap_contract.functions.getAmountsOut(
            amount_in, [token_in_address, token_out_address]
        ).call()
        return amounts_out[-1]

    def is_received_amount_correct(self, token_in_address: str, token_out_address: str, amount_in: float, expected_amount_out: float) -> bool:
        """
        Check if the simulated swap output matches the expected amount within an acceptable range.

        Args:
        - token_in_address (str): Ethereum address of the input token.
        - token_out_address (str): Ethereum address of the output token.
        - amount_in (int): Amount of the input token to swap.
        - expected_amount_out (int): Expected amount of the output token after the swap.

        Returns:
        - bool: True if the simulated amount is within the acceptable range, else False.
        """
        simulated_amount_out = self.simulate_swap(token_in_address, token_out_address, amount_in)

        acceptable_slippage = 0.01  # 1% slippage
        min_acceptable = expected_amount_out * (1 - acceptable_slippage)
        max_acceptable = expected_amount_out * (1 + acceptable_slippage)

        return min_acceptable <= simulated_amount_out <= max_acceptable

    def process_order(self, alert: dict) -> dict:
        """
        Process an order based on an alert received.

        Args:
        - alert (dict): A dictionary containing order details. Expected to have the following keys:
            - 'symbol': The trading pair (e.g., 'ETH/BTC').
            - 'price': The price at which the order is to be executed.
            - 'order_type': Type of the order (e.g., 'market').
            - 'qty_perc': Percentage of the token to be used in the swap.
            - 'side': Either 'buy' or 'sell'.

        Returns:
        - dict: A dictionary indicating the status and result of the order processing. 
                If successful, it will contain a transaction receipt.

        Raises:
        - May raise ValueError or other exceptions from called methods.
        """

        # Extract necessary details from the alert
        symbol = alert['symbol']
        price = alert['price']
        order_type = alert['order_type']
        qty_perc = alert['qty_perc']
        side = alert['side'].lower()  # Ensure the side is in lowercase for subsequent comparison

        # Check if the provided trading pair is supported by the DEX
        if not self.supports_pair(symbol):
            return {"status": "error", "message": f"Pair {symbol} not supported."}

        # Split the symbol to get individual tokens and their respective contract addresses
        token1, token2 = symbol.split('/')
        token1_address = self.tokens[token1]['contract_address']
        token2_address = self.tokens[token2]['contract_address']

        # Decide the input and output tokens based on the side of the trade
        if side == 'buy':
            token_out_address = token1_address
            token_in_address = token2_address
            amount_in = self.fetch_balance(token2) * qty_perc / 100  # Determine amount of token2 to use for the swap
        elif side == 'sell':
            token_in_address = token1_address
            token_out_address = token2_address
            amount_in = self.fetch_balance(token1) * qty_perc / 100  # Determine amount of token1 to use for the swap
        else:
            return {"status": "error", "message": "Invalid side. Only 'buy' or 'sell' are supported."}

        # Ensure the order type is 'market' since that's the only supported type for this DEX client
        if order_type != 'market':
            return {"status": "error", "message": "Only market orders are supported for DEX."}

        # Estimate the expected output amount for the swap based on side and price
        if side == 'buy':
            expected_amount_out = amount_in / price  # Calculate expected amount of token1 received for given amount of token2
        else:  # sell
            expected_amount_out = amount_in * price  # Calculate expected amount of token2 received for given amount of token1

        # Check if the simulated output amount from DEX matches our expectations within an acceptable range
        if not self.is_received_amount_correct(token_in_address, token_out_address, amount_in, expected_amount_out):
            return {"status": "error", "message": "Simulated output amount doesn't match expectations within acceptable slippage."}

        # If everything checks out, process the swap on the DEX
        transaction_receipt = self.swap(token_in_address, token_out_address, amount_in)

        return {"status": "success", "transaction_receipt": transaction_receipt}

    def connect(self):
        """
        Connect to the Ethereum network using Web3, initialize account from a private key, 
        and set up a connection to the Uniswap smart contract.

        Attributes set:
        - self.web3: Instance of the Web3 connection.
        - self.account: Ethereum account derived from the private key.
        - self.uniswap_contract: Web3 contract instance of the Uniswap smart contract.

        Raises:
        - FileNotFoundError: If the ABI file for Uniswap is missing.
        - JSONDecodeError: If there's an issue parsing the ABI.
        """
        
        # Set up a Web3 connection using the provided Infura URL
        self.web3 = Web3(Web3.HTTPProvider(self.infura_url))

        # Initialize an Ethereum account using the private key
        self.account = self.web3.eth.account.privateKeyToAccount(self.private_key)

        # Load the ABI for the Uniswap smart contract from a JSON file
        try:
            with open('ABI/dex/uniswap.json', 'r') as file:
                uniswap_abi = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("The ABI file for Uniswap is missing!")
        except json.JSONDecodeError:
            raise json.JSONDecodeError("There's an issue parsing the ABI for Uniswap!")

        # Set up a Web3 contract instance for the Uniswap smart contract using the ABI
        # Make sure to replace 'UNISWAP_CONTRACT_ADDRESS' with the actual address for the specific Uniswap version/network you're using
        self.uniswap_contract = self.web3.eth.contract(address='UNISWAP_CONTRACT_ADDRESS', abi=uniswap_abi)


def swap(self, token_in_address: str, token_out_address: str, amount_in: float, slippage: float = 0.01) -> dict:
    """
    Swap tokens on Uniswap, taking slippage into account.

    Args:
    - token_in_address (str): Contract address of the token to swap from.
    - token_out_address (str): Contract address of the token to swap to.
    - amount_in (float): Amount of `token_in` to swap.
    - slippage (float, optional): Acceptable slippage percentage. Default is 1%.

    Returns:
    - dict: Transaction receipt after the swap is executed.
    """

    # Check if the wallet has enough ETH to cover the gas fees
    available_balance = self.web3.eth.getBalance(self.public_key)
    gas_required = self.uniswap_contract.functions.swapExactTokensForTokens(
        amount_in,
        Web3.toWei(min_output, 'ether'),  # Convert to Wei format
        [token_in_address, token_out_address],
        self.account.address,
        deadline
    ).estimateGas({'from': self.public_key})

    if available_balance < gas_required:
        raise ValueError(f'Insufficient ETH balance. Available: {available_balance}, Required: {gas_required}')

    # Simulate swap to get expected output
    expected_output = self.simulate_swap(token_in_address, token_out_address, amount_in)

    # Calculate minimum amount out based on slippage
    min_output = expected_output * (1 - slippage)

    # Deadline for the transaction
    deadline = int(self.web3.eth.getBlock('latest')['timestamp']) + 600

    # Construct the swap function call
    swap_function = self.uniswap_contract.functions.swapExactTokensForTokens(
        amount_in,
        Web3.toWei(min_output, 'ether'),  # Convert to Wei format
        [token_in_address, token_out_address],
        self.account.address,
        deadline
    )

    # Sign the transaction
    signed_txn = self.web3.eth.account.signTransaction(
        {
            'chainId': 1,
            'gas': gas_required,
            'gasPrice': self.web3.eth.gasPrice,  # Fetching current gas price
            'nonce': self.web3.eth.getTransactionCount(self.public_key),
            'to': self.uniswap_contract.address,
            'value': 0,
            'data': swap_function.buildTransaction({'chainId': 1, 'nonce': self.web3.eth.getTransactionCount(self.public_key)})['data']  # Adding function call data
        }
    )

    # Send the transaction
    txn_hash = self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)

    # Wait for the transaction to be mined
    txn_receipt = self.web3.eth.waitForTransactionReceipt(txn_hash)

    return txn_receipt

def get_token_symbol(web3: Web3, token_address: str, token_abi: dict) -> str:
    """
    Fetch the symbol of a token using its contract address and ABI.

    Args:
    - web3 (Web3): Instance of Web3 to interact with Ethereum.
    - token_address (str): Contract address of the token.
    - token_abi (dict): ABI of the token.

    Returns:
    - str: Symbol of the token or None if fetch fails.
    """
    token_contract = web3.eth.contract(address=token_address, abi=token_abi)
    try:
        return token_contract.functions.symbol().call()
    except:
        return None
        

def fetch_credentials() -> dict:
    """
    Load credentials for DEX trading from a JSON file.

    Returns:
    - dict: Credentials dictionary.
    """
    with open("dex_credentials.json", "r") as file:
        return json.load(file)