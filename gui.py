"""
FIXME: Profit calculations need to account for fees for both buying and selling (fees apply both ways)
"""
from appJar import gui
from collections import namedtuple
from btcmarket_api import Market, parse_json_string
import sys
import time
import atexit
from subprocess import PIPE, Popen
import ws
from config import MY_ACCOUNT

ON_POSIX = 'posix' in sys.builtin_module_names

DIVISOR_TIME = 1000
DIVISOR_INSTRUMENT = 100000000

m = Market()

app = gui("ProfitCO", "300x300")
app.setSticky("new")
app.setExpand("both")


ChainTrade = namedtuple("ChainTrade", ["id", "currency", "instrument", "orderSide", "price", "volume", "fee", "completionTime"])


def readable_time(the_time):
    return time.strftime("%H:%M:%S %d/%m/%y", time.localtime(the_time))


def trade_completion_time(the_trade):
    return max([transfer["creationTime"] for transfer in the_trade["trades"]]) / 1000


def format_trades(trades):
    the_trades = []
    for trade in trades:
        if trade["status"] not in ("Partially Matched", "Fully Matched"):
            continue

        total_fee = sum([fee["fee"] for fee in trade["trades"]]) / DIVISOR_INSTRUMENT
        the_trades.append(ChainTrade(trade["id"], trade["currency"], trade["instrument"], trade["orderSide"],
                                     trade["price"] / DIVISOR_INSTRUMENT, trade["volume"] / DIVISOR_INSTRUMENT, total_fee,
                                     trade_completion_time(trade)))

    return the_trades


def last_order(formatted_trades, instrument="ETH"):
    for trade_obj in formatted_trades[::-1]:
        if trade_obj.instrument == instrument and trade_obj.orderSide == "Bid":
            return trade_obj

    return None


def get_prev_trades():
    return sorted(format_trades(m.get_history(limit=100)), key=lambda x: x.completionTime)


#purchase = [order["trades"] for order in m.get_history(limit=10, status="Fully Matched") if order["orderSide"] == "Bid"]
last_purchase = {"ETH": last_order(get_prev_trades(), instrument="ETH"), "BTC": last_order(get_prev_trades(), instrument="BTC")}


# Last order when the currency is the same or when the instrument is the same? Store currency price at time of purchase of instrument?
def percentage_profit(instrument, currency, current_price):
    prev = last_order(get_prev_trades(), instrument)
    if prev is None:
        return 0

    return (((current_price / prev.price) - 1) * 100) - m.get_trading_fee(instrument, currency)

#print(percentage_profit("ETH", "AUD", 1190))


class Trader(object):
    def __init__(self):
        self.alarms = {"ETH": [], "BTC": []}

    def add_alarm(self, amount, instrument="ETH"):
        self.alarms[instrument].append(amount)

    def check_alarms(self, ticker_update):
        pass


def calculate_profit(initial_price, current_quantity, current_price, instrument="ETH"):
    fee = m.get_trading_fee(instrument)
    print(f"Fee: {fee}")
    will_receive = current_price * current_quantity
    will_receive -= will_receive*fee
    initially_spent = initial_price * current_quantity

    print(f"Initially spent: {initially_spent}\nWill receive: {will_receive}\n")

    return will_receive - initially_spent


def update_calculations(ticker_amount, instrument):
    values = parse_json_string(ticker_amount)

    price = float(values["lastPrice"]) / DIVISOR_INSTRUMENT

    app.queueFunction(app.setLabel, f"{instrument}_CURRENT_PRICE", f"Current price: {price}")

    if last_purchase[instrument] is not None: # FIXME for bitcoin - follow chain
        purchase = last_purchase[instrument]

        initial_price = purchase.price
        volume = purchase.volume

        profit = round(calculate_profit(initial_price, volume, price, instrument), 2)
        app.queueFunction(app.setLabel, f"{instrument}_CURRENT_PROFIT", f"Current profit: {profit}")
        #print(f"Purchase of {volume} Ether at {initial_price} can be sold for ${profit} profit.\n")



app.startLabelFrame("Ether", row=1, column=1, colspan=2)
app.addLabel("ETH_CURRENT_PRICE", "Current price:", row=2, column=1, colspan=2)
app.addLabel("ETH_CURRENT_PROFIT", "Current profit:", row=3, column=1, colspan=2)
app.stopLabelFrame()

ether_ticker_storage = ws.TickerStorage("ETH", update_calculations)
p = Popen([MY_ACCOUNT["nodejs_executable"], "ticker_watch\\ether_ticker.js"], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
app.thread(ws.enqueue_output, p.stdout, ether_ticker_storage)

app.startLabelFrame("Bitcoin", row=1, column=3, colspan=2, rowspan=0)
app.addLabel("BTC_CURRENT_PRICE", "Current price:", row=2, column=3, colspan=2)
app.addLabel("BTC_CURRENT_PROFIT", "Current profit:", row=3, column=3, colspan=2)
app.stopLabelFrame()

bitcoin_ticker_storage = ws.TickerStorage("BTC", update_calculations)
p2 = Popen([MY_ACCOUNT["nodejs_executable"], "ticker_watch\\bitcoin_ticker.js"], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
app.thread(ws.enqueue_output, p2.stdout, bitcoin_ticker_storage)


def close_storage(*args):
    try:
        app.stop()

    except:
        pass

    for container in args:
        container.write_out()


atexit.register(close_storage, ether_ticker_storage, bitcoin_ticker_storage)
app.go()