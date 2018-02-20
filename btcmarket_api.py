"""
TODO:
 - Handle leap years?
 - Log dummy market operations
"""

import requests
import time
from collections import OrderedDict, namedtuple
import hmac
import base64
import hashlib
import json
import uuid

from config import MY_ACCOUNT

# Seconds since unix epoch that trades opened on BTCMarkets
OPENING = 1344760668851

# Amount to divide timestamps received from BTCMarkets by
DIVISOR_TIME = 1000
# Amount to divide instrument quantities received from BTCMarkets by
DIVISOR_INST = 100000000

# Number of seconds in time constants
HOUR_S = 60*60
HOUR_MS = HOUR_S*1000
DAY_MS = HOUR_MS * 24
WEEK_MS = DAY_MS * 7
YEAR_MS = DAY_MS * 365


Tick = namedtuple("Tick", ["timestamp", "open", "high", "low", "close", "volume"])


call_limits = ("/order/open", "/order/cancel", "/order/detail", "/account/balance", "/market/")


def parse_json_string(the_string):
    """
    Convert json string to dictionary.

    Args:
        the_string: the string containing the JSON.

    Returns: dict
    """
    def parse_dict(the_dict):
        pairs = the_dict.split(",")

        to_return = {}
        for pair in pairs:
            pair = pair.replace(" ", "").replace("{", "").replace("}", "")
            key, value = pair.split(":")

            # There are no floating point values
            if not value.startswith("'"):
                value = int(value)

            to_return[key] = value

        return to_return

    if the_string.startswith("["):
        # Strip the brackets off the ends
        the_string = the_string[1:-1]
        the_string.split("},")

        to_return = []
        for dictionary in the_string:
            to_return.append(parse_dict(dictionary))

        return to_return

    return parse_dict(the_string)


def download_history(instrument, interval="day", currency="AUD"):
    assert interval in ("day", "minute") # What other options are available?

    r = requests.get(f"https://btcmarkets.net/data/market/BTCMarkets/{instrument}/{currency}/tickByTime?timeWindow={interval}&since={OPENING}")
    ticks = r.json()["ticks"]

    to_return = []
    for tick in ticks:
        to_return.append(Tick(*tick))

    return to_return


class DummyMarket(object):
    def __init__(self, logging=True):
        self.public_key = "f963b24e-66fa-4a68-b5dd-21b22ad23e8c"
        self.secret_key = ""

        self.BASE_URL = ""

        self.cached_fee = {}

        self._prev_call = {}

        self.logging = logging

    @staticmethod
    def timestamp():
        return int(time.time()) * 1000

    @staticmethod
    def parameterise(*args):
        num_args = len(args)
        assert num_args % 2 == 0

        the_dict = OrderedDict()

        i = 0
        while i < num_args:
            the_dict[args[i]] = args[i + 1]

            i += 2

        return json.dumps(the_dict).replace(" ", "")

    def limit_call(self, amount_per_10):
        the_time = time.time()

        try:
            prev_call = self._prev_call[amount_per_10]

        except KeyError:
            self._prev_call[amount_per_10] = [the_time]

        else:
            # Remove calls that have expired
            self._prev_call[amount_per_10] = [i for i in self._prev_call[amount_per_10] if the_time - i < 10]
            the_list = self._prev_call[amount_per_10]

            if len(the_list) < amount_per_10:
                the_list.append(the_time)
                self._prev_call[amount_per_10] = the_list

            else:
                to_wait = 10 - (the_time - self._prev_call[amount_per_10][0])

                print(f"Throttle limit exceeded. Waiting for {to_wait} seconds.")
                time.sleep(to_wait)

    def _create_headers(self, path, data=""):
        if path.startswith("/market/") or path in call_limits:
            self.limit_call(25)

        else:
            self.limit_call(10)

        the_timestamp = self.timestamp()
        body = f"{path}\n{the_timestamp}\n{data}".encode("utf-8")
        rsig = hmac.new(MY_ACCOUNT["private_key"], body, hashlib.sha512)
        bsig = base64.standard_b64encode(rsig.digest())

        return OrderedDict([("Accept", "application/json"),
                            ("Accept-Charset", "UTF-8"),
                            ("Content-Type", "application/json"),
                            ("apikey", MY_ACCOUNT["public_key"]),
                            ("timestamp", str(the_timestamp)),
                            ("signature", bsig)])

    def post_request(self, path, data):
        retry = True
        the_request = None
        while retry:
            try:
                the_request = requests.post(f"{self.BASE_URL}{path}",
                                            data=data,
                                            headers=self._create_headers(path, data),
                                            verify=True)

                retry = False

            except requests.exceptions.ConnectionError:
                print("Lost internet connection. Retrying...")
                time.sleep(1)

        while the_request.status_code != 200:
            print(f"POST request with path {path} failed with status code: {the_request.status_code}")
            print("Retrying...")
            time.sleep(1)
            the_request = requests.post(f"{self.BASE_URL}{path}",
                                        data=data,
                                        headers=self._create_headers(path, data),
                                        verify=True)

        return the_request

    def get_request(self, path):
        retry = True
        the_request = None
        while retry:
            try:
                the_request = requests.get(f"{self.BASE_URL}{path}",
                                           headers=self._create_headers(path),
                                           verify=True)
                retry = False

            except requests.exceptions.ConnectionError:
                print("Lost internet connection. Retrying...")
                time.sleep(1)

        while the_request.status_code != 200:
            print(f"GET request with path {path} failed with status code: {the_request.status_code}")
            print("Retrying...")
            time.sleep(1)
            the_request = requests.get(f"{self.BASE_URL}{path}",
                                       headers=self._create_headers(path),
                                       verify=True)

        return the_request

    def create_order(self, amount, price, bid_ask, type="Limit", currency="AUD", instrument="ETH"):
        pass

    def cancel_order(self, order_id):
        pass

    def open_orders(self, limit=10):
        pass

    def cancel_last_order(self):
        pass

    def get_balance(self):
        pass

    def get_history(self, limit=10, status="*", include_cancelled=False):
        pass

    def get_ticker(self, instrument="ETH"):
        return self.get_request(f"/market/{instrument}/AUD/tick")

    def get_trading_fee(self, instrument="ETH", currency="AUD"):
        # Cache the trading fee and update it only every hour
        try:
            cached = self.cached_fee[f"{instrument}/{currency}"]
            if time.time() - cached[0] < HOUR_S:
                return cached[1]

        except KeyError:
            pass

        response = self.get_request(f"/account/{instrument}/{currency}/tradingfee")
        the_rate = round(int(response.json()["tradingFeeRate"]) / DIVISOR_INST, 4)
        self.cached_fee[f"{instrument}/{currency}"] = (time.time(), the_rate)

        return the_rate


class Market(DummyMarket):
    def __init__(self):
        super().__init__(logging=False)
        self.public_key = "f963b24e-66fa-4a68-b5dd-21b22ad23e8c"
        self.secret_key = "II3xe/ILNBsHh4NaKiyv92PgM4RtjhflxDbC8DblXXLhArS+SPaCjWovCXjI0XWoQgpAhLZnilYFiye3oY+zDg=="
        self.BASE_URL = "https://api.btcmarkets.net"

    def create_order(self, amount, price, bid_ask, type="Limit", currency="AUD", instrument="ETH"):
        super().create_order(amount, price, bid_ask, type, currency, instrument)
        
        bid_ask = bid_ask.title()
        assert bid_ask in ("Bid", "Ask")

        return self.post_request("/order/create", self.parameterise("currency", currency, "instrument", instrument,
                                                                    "price", price * DIVISOR_INST,
                                                                    "volume", amount * DIVISOR_INST,
                                                                    "orderSide", bid_ask,
                                                                    "ordertype", type,
                                                                    "clientRequestId", str(uuid.uuid4())))

    def cancel_order(self, order_id):
        super().cancel_order(order_id)
        return self.post_request("order/cancel", self.parameterise("orderIds", order_id))

    def open_orders(self, limit=10):
        super().open_orders(limit)
        return self.post_request("/order/open", self.parameterise("currency", "AUD",
                                                                  "instrument", "ETH",
                                                                  "limit", limit,
                                                                  "since", 1)).json()["orders"]

    def cancel_last_order(self):
        super().cancel_last_order()
        try:
            the_id = (self.open_orders())[-1]["id"]

        except IndexError:
            print("No open orders found.")

        else:
            return self.cancel_order(the_id)

    def get_balance(self):
        super().get_balance()
        Balance = namedtuple("Balance", ["balance", "pendingFunds"])

        the_json = self.get_request("/account/balance").json()

        to_return = {}
        for dictionary in the_json:
            to_return[dictionary["currency"]] = Balance(dictionary["balance"] / DIVISOR_INST,
                                                        dictionary["pendingFunds"] / DIVISOR_INST)

        return to_return

    def get_history(self, limit=10, status="*", include_cancelled=False):
        super().get_history(limit, status, include_cancelled)

        status = status.title()
        assert status in ("*", "New", "Error", "Partially Cancelled", "Placed", "Cancelled", "Fully Matched",
                          "Partially Matched", "Failed")

        the_orders = self.post_request("/order/history", self.parameterise("currency", "AUD",
                                                                           "instrument", "ETH",
                                                                           "limit", limit,
                                                                           "since", 1)).json()["orders"]

        return [order for order in the_orders if ((True if include_cancelled else order["status"] != "Cancelled")
                       and (status == "*" or order["status"] == status))]


if __name__ == "__main__":
    the_market = Market()

    print(the_market.get_history())
