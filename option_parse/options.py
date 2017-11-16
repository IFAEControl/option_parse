import argparse
from pydoc import locate

import yaml


class _Unsigned:
    def __new__(cls, val):
        if val < 0:
            raise ValueError("unsigned variable can not be negative")

        return val


class _Value:
    def __init__(self, value):
        self._val = value

    def as_(self, t):
        if type(t) == str:
            if t == "unsigned":
                return self.as_unsigned()
            elif t == "unsigned_float":
                return self.as_unsigned_float()
            else:
                t = locate(t)
                return t(self._val)
        else:
            return t(self._val)

    def as_unsigned(self) -> _Unsigned:
        return _Unsigned(int(self._val))

    def as_unsigned_float(self) -> _Unsigned:
        return _Unsigned(float(self._val))

    def __getitem__(self, key: str):
        return self._val[key]

    def __setitem__(self, key: str, value):
        self._val[key] = value


class _BaseArgs:
    def __init__(self, args_desc: dict) -> None:
        if args_desc is None:
            return
        self._parser = argparse.ArgumentParser()

        for arg in args_desc:
            flags = []
            if "name" in arg:
                for flag in arg["name"]:
                    flags.append(flag)

            if "others" in arg:
                self._parser.add_argument(*flags, **arg["others"])
                if "action" in arg["others"] and arg["others"]["action"] == "store_true":
                    o_flags = []
                    for f in flags:
                        if f.startswith("--"):
                            o_flags.append("--no-"+f[2:])
                        elif f.startswith("-"):
                            o_flags.append("-n"+f[1:])
                    
                    self._parser.add_argument(*o_flags, **arg["others"])
            else:
                self._parser.add_argument(*flags)

        self._user_args = self._parser.parse_args()

    def get_value(self, *args):
        """ Read the given command line argument if present, if not return None """
        if self._user_args is None:
            return None

        atr = getattr(self._user_args, args[-1])
        if type(atr) == bool:
            if atr is False:
                try:
                    o_atr = getattr(self._user_args, "no_"+args[-1])
                    if type(o_atr) == bool and o_atr is True:
                        return False
                except AttributeError:
                    pass
            elif atr is True:
                return True
        else:
            return atr


class _BaseConfig:
    def __init__(self, conf_desc: dict, config_file: str=None) -> None:
        self._conf_desc = conf_desc
        self._config_file = None
        self._conf = None
        if config_file is not None:
            self.load(config_file)

    def _set_default(self, desc, conf):
        for i in desc.keys():
            if type(conf) == dict:
                if "default" not in desc[i]:
                    if i not in conf:
                        conf[i] = {}
                        self._set_default(desc[i], conf[i])
                    else:
                        self._set_default(desc[i], conf[i])

                elif i not in conf or conf[i] is None:
                    conf[i] = desc[i]["default"]

    def load(self, config_file):
        """ Load config from file"""
        self._config_file = config_file
        with open(config_file) as f:
            self._conf = yaml.load(f.read()) or {}

        self._set_default(self._conf_desc, self._conf)

    def set(self, config) -> None:
        """ set the given config """
        self._conf = config

    def dump(self, config=None, config_file=None):
        """ Save current config """
        file = config_file or self._config_file
        conf = config or self._conf
        with open(file, "w+") as f:
            yaml.dump(conf, f, default_flow_style=False)

    def _set_value(self, v, desc, d, *args):
        if len(args) > 1:
            if args[0] not in d:
                d[args[0]] = {}
            return self._set_value(v, desc[args[0]], d[args[0]], *args[1:])
        else:
            if args[0] in d and "type" in desc[args[0]]:
                t = desc[args[0]]["type"]
                d[args[0]] = _Value(v).as_(t)
            else:
                d[args[0]] = v

    def set_value(self, v, *args):
        """ Set a new value (v) to the given option """
        self._set_value(v, self._conf_desc, self._conf, *args)

    # TODO: Check if there are multiple end-keys
    def _get_value(self, desc, d, *args):
        if type(d) != dict:
            return None

        if args[0] not in d:
            for i in d.keys():
                value = self._get_value(desc[i], d[i], *args)
                if value is not None:
                    return value
        else:
            if len(args) > 1:
                return self._get_value(desc[args[0]], d[args[0]], *args[1:])
            else:
                if "type" in desc[args[0]]:
                    return _Value(d[args[0]]).as_(desc[args[0]]["type"])
                else:
                    return d[args[0]]

    def get_value(self, *args):
        """ Return the requested value """

        v = self._get_value(self._conf_desc, self._conf, *args)
        if v is None:
            raise KeyError("Key not found")
        else:
            return v


class BaseOptions:
    """
        Basic class to manage user options from command line arguments and configuration file prioritizing
        command line arguments with a fallback to the configuration file.
    """

    def __init__(self, config_file: str, conf_desc: dict, args_desc: dict) -> None:
        self.config = _BaseConfig(conf_desc, config_file)
        self._args = _BaseArgs(args_desc)

        # Modified options will be checked only against config values, not arguments
        self._modified_options: list = []

    def save_config(self) -> None:
        """ Save current config """
        self.config.dump()

    def get(self, *args):
        """ Return the requested value."""
        try:
            arg = self._args.get_value(*args)
            if args not in self._modified_options and arg is not None:
                return arg
        except AttributeError:
            pass

        return self.config.get_value(*args)

    def set(self, v, *args):
        """ Set a new value (v) to the given option """
        self.config.set_value(v, *args)
        self._modified_options.append(args)

    # FIXME: Return a recursable
    def __getitem__(self, key: str):
        return self.get(key)

    def __setitem__(self, key: str, value):
        self.set(value, key)
