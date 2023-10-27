# AION_client
"AION_client" is a Python program that's an essential component of the AION cryptocurrency trading automation system. This client program connects to the AION_live trading server, manages data updates, and executes trading signals. It offers users the flexibility to choose between CEX (Centralized Exchange) and DEX (Decentralized Exchange) clients, making it a versatile tool for cryptocurrency trading automation.
## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Disclaimer](#warning-disclaimer)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Features
- Connects only to the AION_live api server for real-time data processing.
- Handles data updates and executes trading signals.
- Supports both CEX (Centralized Exchange) and DEX (Decentralized Exchange **NOT COMPLETE**) clients.
  (check [SupportedExchanges](#supportedexchanges))
- Secure authentication for user accounts.
- Seamless interaction with cryptocurrency exchanges.
- Part of the broader AION cryptocurrency trading automation system.
## Installation
To use "AION_client," follow these steps:
1. Clone the repository to your local machine:
    ```bash
    git clone https://github.com/your-username/AION_client.git
    ```
2. Install the required dependencies:
    ```bash
    pip install requirement.txt
    ```
3. Configure the program as needed (see [Configuration](#configuration)).
## Usage
- Start the program by running the following command from the AION_client directory (not AION_client_test directory that it is used for debugging new features):
```bash
python client_websocket.py
```
- Use exchanges testnet to first try the clients.
- 
## Configuration
Configure the program as follows:
- **Set the AION_live IP address**: navigate to the *client_websocket.py** and change the ip address in base of where you are running the AION_live flask app:
  ```python
  BASE_URL = 'http://localhost:5000'
  ```
- **Credentials**: Provide your credentials (username and password) when prompted during program initialization. You can register your credentials and select which algo signals to receive by connecting to the AION_live API IP address.
- **Client Type**: Choose between CEX and DEX client types. This choice determines the nature of your trading activities. (Only CEX works, check [SupportedExchanges](#supportedexchanges))
- **CEX Configuration (if applicable)**: Configure your CEX client with details such as network mode and chosen exchanges but before complete with your exhanges api keys and the pairs you want to trade the credential.json. Example:
```json
[
    "bybit": {
        "sub_acc": {
          "sub_acc_name1": {
            "apiKey": "YOUR_BYBIT_API_KEY_1",
            "secret": "YOUR_BYBIT_SECRET_KEY_1",
            "market_type": "spot",
            "pair_supported": ["BTC/USDT","ETH/USDT"],
            "urls": {
            "api": {
                "live_net": "https://api.bybit.com"
            }
            }
        },
          "sub_acc_name2": {
            "apiKey": "YOUR_BYBIT_API_KEY_2",
            "secret": "YOUR_BYBIT_SECRET_KEY_2",
            "market_type": "future",
            "pair_supported": ["BTC/USDT:USDT"],
            "urls": {
                "api": {
                    "live_net": "https://api.bybit.com"                
            }
            }
            }
        }
    },
    "bybit_testnet": {
      "sub_acc": {
        "sub_acc_name1": {
          "apiKey": "YOUR_BYBIT_TESTNET_API_KEY_1",
          "secret": "YOUR_BYBIT_TESTNET_SECRET_KEY_1",
          "market_type": "future",
          "pair_supported": ["ETH/USDT:USDT"],
          "urls": {
            "api": {
              "test_net": "https://api-testnet.bybit.com"
            }
          }
        },
        "sub_acc_name2": {
            "apiKey": "YOUR_BYBIT_TESTNET_API_KEY_2",
            "secret": "YOUR_BYBIT_TESTNET_SECRET_KEY_2",
            "market_type": "spot",
            "pair_supported": ["BTC/USDT"],
            "urls": {
                "api": {
                  "test_net": "https://api-testnet.bybit.com"                
             }
            }
          }
      }
    }
]
```
- **DEX Configuration (if applicable)**: If you choose a DEX client, you can provide configuration details for the supported DEX platforms but before complete with your dex parameters the dex_credential.json. 
Example:
```json
[
    {
        "client_name": "Aion_uniswap",
        "public_key": "PUBLIC_KEY_1",
        "private_key": "PRIVATE_KEY_1",
        "infura_url": "INFURA_URL_1",
        "dex": ["uniswap"],
        "supported_pairs": ["WETH/USDT", "WETH/DAI", "WBTC/USDT", "WBTC/DAI", "WETH/WBTC"],
        "tokens": {
            "WETH": {
                "contract_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
            },
            "WBTC": {
                "contract_address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
            },
            "USDT": {
                "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7"
            },
            "DAI": {
                "contract_address": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
            }
        }
    },
    {
        "client_name": "Client2",
        "public_key": "PUBLIC_KEY_2",
        "private_key": "PRIVATE_KEY_2",
        "infura_url": "INFURA_URL_2",
        "dex": ["uniswap"],
        "supported_pairs": ["WETH/USDT"],
        "tokens": {
            "WETH": {
                "contract_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
            }
        }
    }
]
```
- **Data Handling**: The program handles real-time data updates and executes trading signals as per your chosen client type and configurations.
## SupportedExchanges
- **CEX**: Bybit
- **DEX**: Uniswap
## :warning: Disclaimer
This project is in an early stage of development. It currently supports operation only on Centralized Exchanges (CEX) and specifically on Bybit. While we are working to extend its capabilities, please use it with caution.
### Security Precautions
- Do **NOT** upload your personal API keys or any other sensitive data to GitHub branches or any public repositories.
- Exercise caution while trading, and be aware of the risks involved in cryptocurrency trading.
### Development Background
This script is not written in an academic manner as I do not hold an academic degree in development. However, it was crafted out of necessity to facilitate algorithmic trading without relying on TradingView or third-party services managing TradingView webhook signals. There may be syntax errors or unconventional coding practices, and contributions to improve the code are highly welcomed.
We appreciate your understanding and patience as we continue to improve and extend the functionality of this project.
## Contributing
Contributions to this project are welcome. If you'd like to contribute, please follow these guidelines:
1. Fork the repository.
2. Create a new branch for your feature or bug fix: 
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. Commit your changes: 
    ```bash
    git commit -m 'Add some feature'
    ```
4. Push to your branch: 
    ```bash
    git push origin feature/your-feature-name
    ```
5. Submit a pull request to the main repository.
## Acknowledgments
This project utilizes the [CCXT library](https://github.com/ccxt/ccxt), an invaluable resource for cryptocurrency trading. We extend our gratitude to the developers and contributors of CCXT for providing a robust foundation for interacting with various cryptocurrency exchanges.
## License
This project is licensed under the [License Name] - see the LICENSE.md file for details.
