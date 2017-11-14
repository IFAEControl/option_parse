import argparse

import yaml


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
    def __init__(self, config_file: str=None) -> None:
        self._config_file = None
        self._conf = None

        if config_file is not None:
            self.load(config_file)

    def load(self, config_file):
        """ Load config from file"""
        self._config_file = config_file
        with open(config_file) as f:
            self._conf = yaml.load(f.read()) or {}

    def set(self, config) -> None:
        """ set the given config """
        self._conf = config

    def dump(self, config=None, config_file=None):
        file = config_file or self._config_file
        conf = config or self._conf
        with open(file, "w+") as f:
            yaml.dump(conf, f, default_flow_style=False)

    def _set_value(self, v, d, *args):
        if len(args) > 1:
            if args[0] not in d:
                d[args[0]] = {}
            return self._set_value(v, d[args[0]], *args[1:])
        else:
            d[args[0]] = v

    def set_value(self, v, *args):
        """ Set a new value (v) to the given option """
        self._set_value(v, self._conf, *args)

    def _get_value(self, d, *args):
        if len(args) > 1:
            return self._get_value(d[args[0]], *args[1:])
        else:
            return d[args[0]]

    def get_value(self, *args):
        """ Return the requested value """

        return self._get_value(self._conf, *args)


class BaseOptions:
    """
        Basic class to manage user options from command line arguments and configuration file prioritizing
        command line arguments with a fallback to the configuration file.
    """

    def __init__(self, config_file: str, args_desc: dict) -> None:
        self.config = _BaseConfig(config_file)
        self._args = _BaseArgs(args_desc)

        # Modified options will be checked only against config values, not arguments
        self._modified_options: list = []

    def save_config(self) -> None:
        """ Save current config """
        self.config.dump()

    def get_value(self, *args):
        """ Return the requested value."""
        try:
            arg = self._args.get_value(*args)
            if args not in self._modified_options and arg is not None:
                return arg
        except AttributeError:
            pass

        return self.config.get_value(*args)

    def set_value(self, v, *args):
        """ Set a new value (v) to the given option """
        self.config.set_value(v, *args)
        self._modified_options.append(args)

    def get_or_set(self, v, *args):
        """ Try to read and return the given option, otherwise create it """

        try:
            return self.get_value(*args)
        except KeyError:
            self.set_value(v, *args)
            if v == "":
                print("{} must be defined".format(args[-1]))
                raise
            else:
                return v

    def __getitem__(self, key: str):
        return self.get_value(key)

    def __setitem__(self, key: str, value):
        self.set_value(value, key)
