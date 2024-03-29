import base64
from os.path import exists


class ConfigFile(object):
    def __init__(self, path, defaults={}, separator="="):
        if not exists(path):
            with open(path, "w") as f:
                f.write("")

        self.path = path
        self.separator = separator

        changed = False
        self._data = self.load_values()
        for key, value in defaults.items():
            if key not in self._data:
                self._data[key] = value
                changed = True

        if changed:
            self.sync()

        self.functions = {}

    def key_function(self, key, function):
        self.functions[key] = function

    def load_values(self):
        values = {}
        with open(self.path, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "").replace("\"", "")
                if line == "":
                    continue

                sep_index = line.find(self.separator)
                if sep_index == -1:
                    continue

                key = line[:sep_index].strip()

                try:
                    value = line[sep_index+1:].strip()
                except IndexError:
                    continue


                values[key] = value

        return values

    def sync(self):
        to_write = ""
        for key, value in self._data.items():
            to_write = f"{to_write}{key} {self.separator} {value}\n"

        with open(self.path, "w") as f:
            f.write(to_write)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def __contains__(self, item):
        return item in self.keys()

    def __getitem__(self, key):
        try:
            the_function = self.functions[key]

        except KeyError:
            the_function = lambda x: x

        return the_function(self._data[key])

    def __setitem__(self, key, value):
        self._data[key] = value


default_values = {"public_key": "None", "private_key": "None", "nodejs_executable":"C:\Program Files\\nodejs\\node.exe"}

MY_ACCOUNT = ConfigFile("config.cfg", default_values)

cancel = False
if MY_ACCOUNT["public_key"] == "None":
    print("Public key empty. Please edit config.cfg with your BTCMarket public API key.")
    cancel = True

if MY_ACCOUNT["private_key"] == "None":
    print("Private key empty. Please edit config.cfg with your BTCMarket private API key.")
    cancel = True

if cancel:
    raise AssertionError


public_func = lambda x: x.encode("utf-8")
MY_ACCOUNT.key_function("public_key", public_func)

private_func = lambda x: base64.standard_b64decode(x.encode("utf-8"))
MY_ACCOUNT.key_function("private_key", private_func)