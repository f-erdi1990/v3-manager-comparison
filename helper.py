import requests
import os
import json

from web3 import Web3

# manage API_KEY with heroku setup vs. local testing
ON_HEROKU = os.environ.get("ON_HEROKU")
if ON_HEROKU:
    API_KEY = os.environ.get('API_KEY')
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')
    try:
        with open(CONFIG_PATH, 'r') as f:
            tg_config = json.load(f)
            API_KEY = tg_config['API_KEY']
    except FileNotFoundError:
        print("log: config file not found")


class EvmAPI:
    """ This class will take a chain as an argument and construct simple API queries, predominantly the methods for
    getting the contract ABI and the native token balance"""

    API_DICT = {
        "ethereum": ["https://api.etherscan.io/api", API_KEY]
    }

    def __init__(self, blockchain):
        self.blockchain = blockchain.lower()
        self.url_stem = self.API_DICT[self.blockchain][0]
        self.api_key = self.API_DICT[self.blockchain][1]

    def get_normal_tx(self, wallet_address):
        module_string = "?module=account" \
                        "&action=txlist" \
                        "&address=" + wallet_address + \
                        "&startblock=1&endblock=99999999&sort=asc"
        return self.execute(module_string)

    def get_internal_tx(self, wallet_address):
        module_string = "?module=account" \
                        "&action=txlistinternal" \
                        "&address=" + wallet_address + \
                        "&startblock=1&endblock=99999999&sort=asc"
        return self.execute(module_string)

    def get_token_tx(self, wallet_address):
        module_string = "?module=account" \
                        "&action=tokentx" \
                        "&address=" + wallet_address + \
                        "&startblock=1&endblock=99999999&sort=asc"
        return self.execute(module_string)

    def get_nft_tx(self, wallet_address):
        module_string = "?module=account" \
                        "&action=tokennfttx" \
                        "&address=" + wallet_address + \
                        "&startblock=1&endblock=99999999&sort=asc"
        return self.execute(module_string)

    def get_fee_balance(self, wallet_address):
        module_string = "?module=account" \
                        "&action=balance" \
                        "&address=" + wallet_address + \
                        "&tag=latest"
        return self.execute(module_string)

    def get_abi(self, contract_address):
        module_string = "?module=contract" \
                        "&action=getabi" \
                        "&address=" + contract_address
        return self.execute(module_string)

    def gas_oracle(self):
        module_string = "?module=gastracker" \
                        "&action=gasoracle"
        return self.execute(module_string)

    def execute(self, module_string):
        if self.api_key is None:
            module_string_adapted = module_string
        else:
            module_string_adapted = module_string + "&apikey=" + self.api_key
        result = requests.get(self.url_stem + module_string_adapted).json()['result']
        return result


class Blockchain:
    """Primarily used to make code less lengthy and ease interacting with contracts on chain"""

    RPC_DICT = {
        "ethereum": "https://mainnet.infura.io/v3/d13464cb686d48a4b6d58d40277503f5",
        "arbitrum": "https://arb1.arbitrum.io/rpc",
        "celo": "https://forno.celo.org",
        "avalanche": "https://api.avax.network/ext/bc/C/rpc",
        "fantom": "https://rpc.ftm.tools/",
    }

    def __init__(self, blockchain):
        self.blockchain = blockchain.lower()
        self.abis = gsinputs.ABIs()

    def get_w3(self):
        # get correct RPC address
        rpc_url = self.RPC_DICT[self.blockchain]
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        return w3

    def create_contract(self, contract_address, abi_address=None, abi_name=None):
        # check if ABI was passed as argument
        if abi_address is None:
            abi_address = contract_address

        # make checksum addresses
        abi_address = Web3.toChecksumAddress(abi_address)
        contract_address = Web3.toChecksumAddress(contract_address)

        # get correct RPC address
        rpc_url = self.RPC_DICT[self.blockchain]
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        # get ABI
        if abi_name is None:
            abi = EvmAPI(self.blockchain).get_abi(abi_address)
        else:
            abi = self.abis.abi(abi_name)

        # create contract instance
        contract_instance = w3.eth.contract(address=contract_address, abi=abi)

        return contract_instance

    def create_account(self, private_key):
        # get correct RPC address
        rpc_url = self.RPC_DICT[self.blockchain]
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        # create account
        account = w3.eth.account.from_key(private_key)
        return account
