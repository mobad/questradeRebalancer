import json
import requests

OAUTH_URL = "https://login.questrade.com/oauth2/token"
# OAUTH_URL = "https://practicelogin.questrade.com/oauth2/token"

SETTINGS_FILE = "auth.json"

api_paths = {
    "time": "v1/time",
    "accounts": "v1/accounts",
    "symbols": "v1/symbols",
    "markets": "v1/markets"
}


class WrappedRequests:
    def __init__(self, api_server, auth_header):
        self.session = requests.Session()
        self.api_server = api_server
        self.auth_header = auth_header

    def get(self, path, **kwargs):
        get_url = "{}{}".format(self.api_server, path)
        kwargs['headers'] = self.auth_header
        return self.session.get(get_url, **kwargs).json()

    def post(self, path, **kwargs):
        post_url = "{}{}".format(self.api_server, path)
        kwargs['headers'] = self.auth_header
        return self.session.post(post_url, **kwargs).json()


class QuestradeApi:
    def __init__(self):
        self.requests = None
        self.api_server = None
        self.auth_header = None
        self.setup()

    def read_auth_file(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def write_auth_file(self, auth_dict, path):
        with open(path, "w") as f:
            json.dump(auth_dict, f, indent=4, sort_keys=True)
            f.write('\n')

    def _parse_auth(self, auth):
        auth_entry = "{} {}".format(auth["token_type"], auth["access_token"])
        self.auth_header = {"Authorization": auth_entry}
        self.api_server = auth['api_server']

    def fetch_auth(self, auth_token):
        params = {"grant_type": "refresh_token",
                  "refresh_token": auth_token}
        r = requests.get(OAUTH_URL, params=params)
        return r.json()

    def _list_to_string(self, list_of_strings):
        out_string = ""
        list_length = len(list_of_strings)
        list_of_strings = list(map(lambda x: str(x), list_of_strings))
        for i in range(list_length):
            entry = list_of_strings[i]
            out_string += entry
            if i < list_length - 1:
                out_string += ","
        return out_string

    # Try to read auth file
    def setup(self):
        try:
            auth = self.read_auth_file(SETTINGS_FILE)
            self._parse_auth(auth)
            self.write_auth_file(auth, SETTINGS_FILE)
            self.requests = WrappedRequests(self.api_server, self.auth_header)
        except FileNotFoundError:
            print("Couldn't find auth file. Please try running .auth().")

    def auth(self):
        auth_token = input("Enter your auth token: ")
        auth = self.fetch_auth(auth_token.split())
        self._parse_auth(auth)
        self.write_auth_file(auth, SETTINGS_FILE)
        self.setup()

    ## Account Calls

    def get_time(self):
        return self.requests.get(api_paths["time"])["time"]

    def get_accounts(self):
        return self.requests.get(api_paths["accounts"])

    def get_positions(self, account_id):
        positions_path = \
            "{}/{}/positions".format(api_paths["accounts"], account_id)
        return self.requests.get(positions_path)

    def get_balances(self, account_id):
        balanced_path = \
            "{}/{}/balances".format(api_paths["accounts"], account_id)
        return self.requests.get(balanced_path)

    def get_executions(self, account_id, **kwargs):
        executions_path = \
            "{}/{}/executions".format(api_paths["accounts"], account_id)
        return self.requests.get(executions_path, params=kwargs)

    def get_orders(self, account_id, **kwargs):
        orders_path = \
            "{}/{}/orders".format(api_paths["accounts"], account_id)
        if "order_id" in kwargs:
            orders_path += "/{}".format(kwargs["order_id"])
        return self.requests.get(orders_path, params=kwargs)

    def get_activities(self, account_id, **kwargs):
        activities_path = \
            "{}/{}/activities".format(api_paths["accounts"], account_id)
        return self.requests.get(activities_path, params=kwargs)

    ## Market Calls

    def _get_symbol_info(self, **kwargs):
        return self.requests.get(api_paths["symbols"], params=kwargs)

    def get_symbol_info_from_id(self, symbol_ids):
        if type(symbol_ids) == int:
            symbol_ids = [symbol_ids]
        params = {"ids": self._list_to_string(symbol_ids)}
        return self._get_symbol_info(**params)

    def get_id_from_symbol_name(self, symbol_name):
        query = self.get_symbol_info_from_name(symbol_name)
        first_entry = query["symbols"][0]
        return int(first_entry["symbolId"])

    def get_symbol_info_from_name(self, symbol_names):
        if type(symbol_names) == str:
            symbol_names = [symbol_names]
        params = {"names": self._list_to_string(symbol_names)}
        return self._get_symbol_info(**params)

    def search_symbol(self, prefix,  **kwargs):
        search_path = "{}/search".format(api_paths["symbols"])
        kwargs["prefix"] = prefix
        return self.requests.get(search_path, params=kwargs)

    def get_symbol_options(self, symbol_id):
        options_path = "{}/{}/options".format(api_paths["symbols"], symbol_id)
        return self.requests.get(options_path)

    def get_markets(self):
        return self.requests.get(api_paths["markets"])

    def get_market_quotes(self, symbol_ids):
        quotes_path = "{}/quotes".format(api_paths["markets"])
        if type(symbol_ids) == int:
            symbol_ids = [symbol_ids]
        params = {"ids": self._list_to_string(symbol_ids)}
        return self.requests.get(quotes_path, params=params)

    def get_quotes_options(self):
        options_path = "{}/quotes/options".format(api_paths["markets"])
        return self.requests.get(options_path)

    def get_quotes_strategies(self):
        strategies_path = "{}/quotes/strategies".format(api_paths["markets"])
        return self.requests.get(strategies_path)

    def get_candles(self, symbol_id, **kwargs):
        candles_path = "{}/candles/{}".format(api_paths["markets"], symbol_id)
        return self.requests.get(candles_path, params=kwargs)

    # Order Calls
    def place_order(self, account_id, symbol_id, quantity, price, buy=True):
        payload = {
            "accountNumber": account_id,
            "symbolId": symbol_id,
            "quantity": quantity,
            "limitPrice": price,
            "isAllOrNone": False,
            "isAnonymous": False,
            "orderType": "Limit",
            "timeInForce": "Day",
            "action": 'Buy' if buy else 'Sell',
            "primaryRoute": "AUTO",
            "secondaryRoute": "AUTO"
        }
        return self._send_order(**payload)

    def place_buy_order(self, account_id, symbol_id, quantity, price):
        return self.place_order(account_id, symbol_id, quantity, price, buy=True)

    def place_sell_order(self, account_id, symbol_id, quantity, price):
        return self.place_order(account_id, symbol_id, quantity, price, buy=False)

    def _send_order(self, **kwargs):
        orders_path = "{}/{}/orders"
        orders_path = orders_path.format(
            api_paths["accounts"], kwargs["accountNumber"])
        return self.requests.post(orders_path, json=kwargs)

    def get_order_impact(self, account_id, **kwargs):
        pass

    def delete_order(self, account_id, order_id):
        delete_path = "{}/{}/orders/{}".format(api_paths["accounts"],
                                               account_id, order_id)
        return self.requests.delete(delete_path)

    # TODO: continue order calls later maybe
