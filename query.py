import time
import os
import json
import pandas as pd

from pycoingecko import CoinGeckoAPI
from web3 import Web3

import helper


class Query:
    """This class houses multiple functions to query
    a) prices,
    b) web3 balances,
    c) contract states
    in order to create a comparative view of various providers of UniV3 strategies"""

    FILEPATH = "collected_data.csv"
    # get contract data
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONTRACTS_PATH = os.path.join(ROOT_DIR, 'contracts.json')
    try:
        with open(CONTRACTS_PATH, 'r') as f:
            CONTRACTS = json.load(f)
    except FileNotFoundError:
        print("log: contracts file not found")

    def __init__(self, config):
        """config file must have the following dict logic:
        {str_pool_fee: {
            str_v3manager: str_contract_address,
            str_v3manager: str_contract_address,
            },
        str_pool_fee: {...
        """

        self.config = config
        self.bc = helper.Blockchain("Ethereum")
        return

    def compile(self):
        """summary function to iterate through config, which eventually compiles the dataframe"""
        config = self.config['query']
        uni_pools = self.config['uni_pools']
        list_df = []
        for str_pool, dict_managers in config.items():
            uni_pool_address = Web3.toChecksumAddress(uni_pools[str_pool])
            token_0_contract, token_1_contract = self.get_uni_pool_tokens(uni_pool_address)
            token_0_price = self.get_price(token_0_contract)
            token_1_price = self.get_price(token_1_contract)
            print("log: querying uni vault {}".format(str_pool))
            for str_manager, str_contract in dict_managers.items():
                function = self.mapping(str_manager)
                list_df.append(function(
                    pool_id=str_pool,
                    contract=str_contract,
                    token_0_contract=token_0_contract,
                    token_0_price=token_0_price,
                    token_1_contract=token_1_contract,
                    token_1_price=token_1_price,
                ))

        df = pd.DataFrame(list_df)
        return df

    def mapping(self, str_manager):
        dict_map = {
            "g-uni": self.g_uni_vaults,
            "gamma": self.gamma_vaults,
            "lixir": self.lixir_vaults,
            "charm": self.charm_vaults,
            "popsicle": self.popsicle_vaults,
        }
        return_function = dict_map[str_manager]

        return return_function

    def get_uni_pool_tokens(self, contract):
        # inits
        contract = Web3.toChecksumAddress(contract)
        abi = "0x8f8ef111b67c04eb1641f5ff19ee54cda062f163"
        contract_instance = self.bc.create_contract(contract_address=contract, abi_address=abi)

        # get token0 and token1
        token_0 = contract_instance.functions.token0().call()
        token_1 = contract_instance.functions.token1().call()
        print("log: tokens of uni_pool retrieved")

        return token_0, token_1

    def get_price(self, contract):
        # initialize Coingecko API instance
        cg = CoinGeckoAPI()
        # get coingecko price for asset
        cg_id = self.CONTRACTS[contract.lower()][0]
        price = cg.get_price(ids=cg_id, vs_currencies='usd')[cg_id]['usd']
        return price

    def g_uni_vaults(self, pool_id, contract, token_0_contract, token_0_price, token_1_contract, token_1_price):
        """ gets core information from g-uni contracts"""
        # inits
        abi_contract = Web3.toChecksumAddress("0xb542d5Cb34ef265fB87c170181127332f7797369")
        contract = Web3.toChecksumAddress(contract)
        contract_instance = self.bc.create_contract(contract_address=contract, abi_address=abi_contract)

        # get data from contract
        decimals = contract_instance.functions.decimals().call()
        total_supply_wei = contract_instance.functions.totalSupply().call()
        total_supply = total_supply_wei / (10 ** decimals)
        # get necessary details for tokens
        token_0_balance_wei, token_1_balance_wei = contract_instance.functions.getUnderlyingBalances().call()
        token_0_balance = token_0_balance_wei / (10 ** self.CONTRACTS[token_0_contract.lower()][1])
        token_1_balance = token_1_balance_wei / (10 ** self.CONTRACTS[token_1_contract.lower()][1])
        token_0_value = token_0_balance * token_0_price
        token_1_value = token_1_balance * token_1_price
        vault_value = token_0_value + token_1_value
        vault_token_price = vault_value / total_supply
        upper_bound = contract_instance.functions.upperTick().call()
        lower_bound = contract_instance.functions.lowerTick().call()
        now = int(time.time())

        return_dict = {
            "timestamp": now,
            "poolId": pool_id,
            "manager": "g-uni",
            "totalSupply": total_supply,
            "token0Balance": token_0_balance,
            "token0Contract": token_0_contract,
            "token0Price": token_0_price,
            "token0Value": token_0_value,
            "token1Contract": token_1_contract,
            "token1Balance": token_1_balance,
            "token1Price": token_1_price,
            "token1Value": token_1_value,
            "vaultValue": vault_value,
            "vaultTokenPrice": vault_token_price,
            "upperBound": upper_bound,
            "lowerBound": lower_bound,
        }
        print("log: queried g-uni vault for uni vault {}".format(pool_id))
        return return_dict

    def gamma_vaults(self, pool_id, contract, token_0_contract, token_0_price, token_1_contract, token_1_price):
        """ gets core information from gamma contracts"""
        # inits
        contract = Web3.toChecksumAddress(contract)
        contract_instance = self.bc.create_contract(contract_address=contract)

        # get data from contract
        decimals = contract_instance.functions.decimals().call()
        total_supply_wei = contract_instance.functions.totalSupply().call()
        total_supply = total_supply_wei / (10 ** decimals)
        # get necessary details for tokens
        token_0_balance_wei, token_1_balance_wei = contract_instance.functions.getTotalAmounts().call()
        token_0_balance = token_0_balance_wei / (10 ** self.CONTRACTS[token_0_contract.lower()][1])
        token_1_balance = token_1_balance_wei / (10 ** self.CONTRACTS[token_1_contract.lower()][1])
        token_0_value = token_0_balance * token_0_price
        token_1_value = token_1_balance * token_1_price
        vault_value = token_0_value + token_1_value
        vault_token_price = vault_value / total_supply
        upper_bound = contract_instance.functions.baseUpper().call()
        lower_bound = contract_instance.functions.baseLower().call()
        now = int(time.time())

        return_dict = {
            "timestamp": now,
            "poolId": pool_id,
            "manager": "gamma",
            "totalSupply": total_supply,
            "token0Balance": token_0_balance,
            "token0Contract": token_0_contract,
            "token0Price": token_0_price,
            "token0Value": token_0_value,
            "token1Contract": token_1_contract,
            "token1Balance": token_1_balance,
            "token1Price": token_1_price,
            "token1Value": token_1_value,
            "vaultValue": vault_value,
            "vaultTokenPrice": vault_token_price,
            "upperBound": upper_bound,
            "lowerBound": lower_bound,
        }
        print("log: queried gamma vault for uni vault {}".format(pool_id))
        return return_dict

    def lixir_vaults(self, pool_id, contract, token_0_contract, token_0_price, token_1_contract, token_1_price):
        """ gets core information from lixir contracts"""
        # inits
        contract = Web3.toChecksumAddress(contract)
        contract_instance = self.bc.create_contract(contract_address=contract)

        # get data from contract
        decimals = contract_instance.functions.decimals().call()
        total_supply_wei = contract_instance.functions.totalSupply().call()
        total_supply = total_supply_wei / (10 ** decimals)
        # get necessary details for tokens
        token_0_balance_wei, token_1_balance_wei, q1, q2 = contract_instance.functions.calculateTotals().call()
        token_0_balance = token_0_balance_wei / (10 ** self.CONTRACTS[token_0_contract.lower()][1])
        token_1_balance = token_1_balance_wei / (10 ** self.CONTRACTS[token_1_contract.lower()][1])
        token_0_value = token_0_balance * token_0_price
        token_1_value = token_1_balance * token_1_price
        vault_value = token_0_value + token_1_value
        vault_token_price = vault_value / total_supply
        lower_bound, upper_bound = contract_instance.functions.mainPosition().call()
        now = int(time.time())

        return_dict = {
            "timestamp": now,
            "poolId": pool_id,
            "manager": "lixir",
            "totalSupply": total_supply,
            "token0Balance": token_0_balance,
            "token0Contract": token_0_contract,
            "token0Price": token_0_price,
            "token0Value": token_0_value,
            "token1Contract": token_1_contract,
            "token1Balance": token_1_balance,
            "token1Price": token_1_price,
            "token1Value": token_1_value,
            "vaultValue": vault_value,
            "vaultTokenPrice": vault_token_price,
            "upperBound": upper_bound,
            "lowerBound": lower_bound,
        }
        print("log: queried lixir vault for uni vault {}".format(pool_id))
        return return_dict

    def charm_vaults(self, pool_id, contract, token_0_contract, token_0_price, token_1_contract, token_1_price):
        """ gets core information from charm contracts"""
        # inits
        contract = Web3.toChecksumAddress(contract)
        contract_instance = self.bc.create_contract(contract_address=contract)

        # get data from contract
        decimals = contract_instance.functions.decimals().call()
        total_supply_wei = contract_instance.functions.totalSupply().call()
        total_supply = total_supply_wei / (10 ** decimals)
        # get necessary details for tokens
        token_0_balance_wei, token_1_balance_wei= contract_instance.functions.getTotalAmounts().call()
        token_0_balance = token_0_balance_wei / (10 ** self.CONTRACTS[token_0_contract.lower()][1])
        token_1_balance = token_1_balance_wei / (10 ** self.CONTRACTS[token_1_contract.lower()][1])
        token_0_value = token_0_balance * token_0_price
        token_1_value = token_1_balance * token_1_price
        vault_value = token_0_value + token_1_value
        vault_token_price = vault_value / total_supply
        lower_bound = contract_instance.functions.baseLower().call()
        upper_bound = contract_instance.functions.baseUpper().call()
        now = int(time.time())

        return_dict = {
            "timestamp": now,
            "poolId": pool_id,
            "manager": "charm",
            "totalSupply": total_supply,
            "token0Balance": token_0_balance,
            "token0Contract": token_0_contract,
            "token0Price": token_0_price,
            "token0Value": token_0_value,
            "token1Contract": token_1_contract,
            "token1Balance": token_1_balance,
            "token1Price": token_1_price,
            "token1Value": token_1_value,
            "vaultValue": vault_value,
            "vaultTokenPrice": vault_token_price,
            "upperBound": upper_bound,
            "lowerBound": lower_bound,
        }
        print("log: queried charm vault for uni vault {}".format(pool_id))
        return return_dict

    def popsicle_vaults(self, pool_id, contract, token_0_contract, token_0_price, token_1_contract, token_1_price):
        """ gets core information from charm contracts"""
        # inits
        contract = Web3.toChecksumAddress(contract)
        contract_instance = self.bc.create_contract(contract_address=contract)

        # get data from contract
        decimals = contract_instance.functions.decimals().call()
        total_supply_wei = contract_instance.functions.totalSupply().call()
        total_supply = total_supply_wei / (10 ** decimals)
        # get necessary details for tokens
        token_0_balance_wei, token_1_balance_wei = contract_instance.functions.usersAmounts().call()
        token_0_balance = token_0_balance_wei / (10 ** self.CONTRACTS[token_0_contract.lower()][1])
        token_1_balance = token_1_balance_wei / (10 ** self.CONTRACTS[token_1_contract.lower()][1])
        token_0_value = token_0_balance * token_0_price
        token_1_value = token_1_balance * token_1_price
        vault_value = token_0_value + token_1_value
        vault_token_price = vault_value / total_supply
        lower_bound = contract_instance.functions.tickLower().call()
        upper_bound = contract_instance.functions.tickUpper().call()
        now = int(time.time())

        return_dict = {
            "timestamp": now,
            "poolId": pool_id,
            "manager": "popsicle",
            "totalSupply": total_supply,
            "token0Balance": token_0_balance,
            "token0Contract": token_0_contract,
            "token0Price": token_0_price,
            "token0Value": token_0_value,
            "token1Contract": token_1_contract,
            "token1Balance": token_1_balance,
            "token1Price": token_1_price,
            "token1Value": token_1_value,
            "vaultValue": vault_value,
            "vaultTokenPrice": vault_token_price,
            "upperBound": upper_bound,
            "lowerBound": lower_bound,
        }
        print("log: queried popsicle vault for uni vault {}".format(pool_id))
        return return_dict

