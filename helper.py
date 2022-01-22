import requests
import os
import json
import gspread
import pandas as pd

from web3 import Web3

# manage API_KEY with heroku setup vs. local testing
ON_HEROKU = os.environ.get("ON_HEROKU")
if ON_HEROKU:
    print("log: system is aware its on heroku")
    API_KEY = os.environ.get('API_KEY')
    string_gs_service = os.environ.get('GS_SERVICE')
    GS_SERVICE = json.loads(string_gs_service)
else:
    print("log: system is aware it is not on heroku")
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            API_KEY = config['API_KEY']
    except FileNotFoundError:
        print("log: config file not found")

    GS_TOKEN_PATH = os.path.join(ROOT_DIR, 'gs-token.json')
    try:
        with open(GS_TOKEN_PATH, 'r') as f:
            GS_SERVICE = json.load(f)
    except FileNotFoundError:
        print("log: google sheets token file not found")


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
        "ethereum": "https://eth-mainnet.gateway.pokt.network/v1/5f3453978e354ab992c4da79",
    }

    def __init__(self, blockchain):
        self.blockchain = blockchain.lower()

    def get_w3(self):
        # get correct RPC address
        rpc_url = self.RPC_DICT[self.blockchain]
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        return w3

    def create_contract(self, contract_address, abi_address=None):
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
        abi = EvmAPI(self.blockchain).get_abi(abi_address)

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


class Sheets():
    """This class will enable saving and retrieving of data from google spreadsheets
    It always retrieves and writes data from and to the given spreadsheet"""

    def __init__(self, sheet_name):
        self.sheet_name = sheet_name
        gc = gspread.service_account_from_dict(info=GS_SERVICE)
        self.sheet = gc.open(self.sheet_name).sheet1
        self.df = pd.DataFrame(self.sheet.get_all_records())

    def get_df(self):
        return self.df

    def write_df(self, df):
        self.sheet.update([df.columns.values.tolist()] + df.values.tolist())
        print("log: files successfully written to google sheet")
        return
