import time
import os


class TickerStorage(object):
    def __init__(self, instrument, callback=None):
        self.filepath = f"TICK_{instrument}_{round(time.time())}.txt"
        self.ticks = []

        self.instrument = instrument
        self.callback = callback

    def add_tick(self, the_tick):
        the_tick = the_tick.decode('utf-8').split(',snapshotId:')[0] + "}"
        self.ticks.append(the_tick)

        if self.callback is not None:
            self.callback(the_tick, self.instrument)

    def write_out(self):
        with open(self.filepath, "w") as f:
            to_write = "\n".join(self.ticks)

            f.write(to_write)
            f.flush()
            os.fsync(f.fileno())


def enqueue_output(out, ticker_storage):
    while True:
        current_tick = b""

        for line in iter(out.readline, b''):
            if line.startswith(b"<connected>"):
                continue

            elif line.startswith(b"<disconnected>"):
                ticker_storage.sync()
                return

            line = line.strip()
            current_tick += line
            try:
                if line.endswith(b"}"):
                    ticker_storage.add_tick(current_tick)
                    break

            except IndexError:
                pass