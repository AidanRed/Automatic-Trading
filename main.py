"""
Set up interface as own class
Set up analysis as own class
Set up communication as own class
"""
import shelve
import ws
import sys
import threading
from subprocess import PIPE, Popen
import canon

from btcmarket_api import Market, parse_json_string


#datafile = shelve.open("data")


DIVIDE_BY = 100000000

print("Starting market object.")
m = Market()

purchases = [m.get_history()]

ON_POSIX = 'posix' in sys.builtin_module_names


def make_purchase(volume, price):
    purchases.append((volume, price))


def calculate_profit(initial_price, current_quantity, current_price, instrument="ETH"):
    fee = m.get_trading_fee(instrument)
    print(f"Fee: {fee}")

    will_receive = current_price * current_quantity
    will_receive -= will_receive*fee
    initially_spent = initial_price * current_quantity

    print(f"Initially spent: {initially_spent}\nWill receive: {will_receive}\n")

    return will_receive - initially_spent


def update_calculations(ticker_amount):
    print(ticker_amount)
    values = parse_json_string(ticker_amount)

    price = float(values["lastPrice"])/DIVIDE_BY
    print(f"Current price: {price}")
    for volume, initial_price in purchases:
        profit = calculate_profit(initial_price, volume, price)
        print(f"Purchase of {volume} Ether at {initial_price} can be sold for ${profit} profit.\n")
        if profit >= 15: # FIXME
            canon.play()

    print("______________________________")


class Account(object):
    def __init__(self):
        self.balance = m.get_balance()


def main():
    print("Creating ticker storage...")
    bitcoin_ticker_storage = ws.TickerStorage("bitcoin_data.txt", update_calculations)
    ether_ticker_storage = ws.TickerStorage("ether_data.txt", update_calculations)
    print("Opening ticker...")
    p = Popen(["C:\Program Files\\nodejs\\node.exe", "ticker_watch\\ether_ticker.js"], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
    print("Starting thread...")
    t1 = threading.Thread(target=ws.enqueue_output, args=(p.stdout, ether_ticker_storage))
    t1.daemon = False
    t1.start()
    print("Thread started.")
    while True:
        if input().lower() in ("q", "quit"):
            return


if __name__ == "__main__":
    while True:
        try:
            main()

        except (KeyboardInterrupt, SystemExit):
            raise

        except:
            print(sys.exc_info()[0])
            print("\nRestarting...")

