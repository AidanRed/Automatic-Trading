

def analyse_chain(formatted_trades, bid_overwrite_order):
    # Does cancelling a partially matched trade convert it to partially cancelled, or is there now a trade entry for
    # both the cancelled and matched amounts?

    current_balance = m.get_balance()

    effective_trades = {}
    for key, item in current_balance.items():
        effective_trades[key] = (item.balance(), [])

    for trade_obj in formatted_trades:
        if trade_obj.orderSide == "Bid":
            effective_trades[trade_obj.instrument][0] += trade_obj.volume

            effective_trades[trade_obj.currency][0] -= (trade_obj.volume *
                                                        trade_obj.price) + trade_obj.fee
            effective_trades[trade_obj.currency][1].append(trade_obj)

        elif trade_obj.orderSide == "Ask":
            effective_trades[trade_obj.instrument][0] -= (trade_obj.volume + (trade_obj.fee / trade_obj.price)) # FIXME: Ensure fee is being handled correctly

            currency_amount = trade_obj.volume * trade_obj.price
            effective_trades[trade_obj.currency][0] += currency_amount

            while currency_amount > 0:
                pass

        else:
            raise AssertionError("Order is neither bid nor ask!")


class Chain(object):
    def __init__(self, instrument, volume, precursor=None):
        self.instrument = instrument
        self.volume = volume

        self.precursor = precursor

    def merge(self, other_chain):
        """
        TODO: Fix this. Currently destroys other chain's history
        Returns False if unsuccessful
        """
        if other_chain.instrument == self.instrument:
            self.volume += other_chain.volume

        elif self.precursor is not None:
            return self.precursor.merge(other_chain)

        else:
            return False

        del other_chain

        return True

    def split(self, new_instrument, volume):
        assert volume < self.volume

        return Chain(new_instrument, volume, self)

#ChainTrade = namedtuple("ChainTrade", ["id", "currency", "instrument", "orderSide", "price", "volume", "fee", "completionTime"])
def follow_chain(trades):
    current_tails = [trades[0]]
    for trade in trades[1:]:
        new_link = Chain(trade.instrument, trade.volume)

        prev_paid = (trade.price / trade.volume) + trade.fee # TODO: Double-check this is how the fee works



        for index, precursor in enumerate(current_tails):
            if new_link.instrument == precursor.instrument:
                precursor.merge(new_link)
                continue

            if precursor.instrument == new_link.instrument:
                if precursor.volume > new_link.volume:
                    current_tails.append(precursor.split(new_link.instrument, new_link.volume))
                    continue

                elif precursor.volume == new_link.volume:
                    new_link.precursor = precursor
                    current_tails[index] = new_link
                    continue

        # Money has been transferred in - needs to be handled elsewhere

        precursor = new_link

    return current_tails

# NO NEED TO STORE BUY / SELL PRICE - chain automatically keeps track of profits using volume
# Loop through open chains when calculating profits and potential trades. Each link in the chain holds one instrument


"""
app.startSubWindow("buysellchainer")
app.startLabelFrame("Drag and drop bids in overwrite order")

being_dragged = None

to_order = format_trades(m.get_history(99))
to_label = [item for item in to_order if item.orderSide == "Bid"]


def drag(widget):
    global being_dragged

    being_dragged = widget


def drop(widget):
    global being_dragged

    text1 = app.getLabel(being_dragged)
    text2 = app.getLabel(widget)

    first_index = int(being_dragged[-1])
    second_index = int(widget[-1])

    to_label[first_index], to_label[second_index] = to_label[second_index], to_label[first_index]

    app.setLabel(being_dragged, text2)
    app.setLabel(widget, text1)

    being_dragged = None


for index, item in enumerate(to_label):
    if index != 0:
        app.addHorizontalSeparator()

    title = f"to_swap{index}"
    app.addLabel(title,
                 f"{index+1}. Volume: {item.volume}, Price: {item.price} at {readable_time(item.completionTime)}")

    app.setLabelDragFunction(title, [drag, drop])
app.stopLabelFrame()


def chainer_submit(button):
    app.hideSubWindow("buysellchainer")
    analyse_chain(to_order, to_label)


app.addButton("Submit", chainer_submit)
app.stopSubWindow()
app.showSubWindow("buysellchainer")
"""