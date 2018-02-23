
CRITICAL = 0
ERROR = 1
WARNING = 2
INFO = 3
DEBUG = 4


class Logger(object):
    def __init__(self, stdout_verbosity=INFO, storage_verbosity=DEBUG):
        self.stdout_verbosity = stdout_verbosity
        self.storage_verbosity = storage_verbosity

        self.cache = ""

        self.orders = []

    def log_order(self, order):
        self.orders.append(order)
        the_string = f"Placed {order.orderSide.upper()}"

    def log(self, to_log, level):
        if level <= self.stdout_verbosity:
            print(str(to_log))

        if level <= self.storage_verbosity:
            self.cache = f"{self.cache}\n{to_log}"

    def generate_history(self):
        pass