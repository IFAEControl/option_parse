import argparse

import yaml


class _BaseArgs:
    def __init__(self, args_desc):
        self._parser = argparse.ArgumentParser()

        for arg in args_desc:
            flags = []
            if "flag_name" in arg:
                for flag in arg["flag_name"]:
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
        atr = getattr(self._user_args, args[-1])
        if type(atr) == bool and atr == False:
            try:
                o_atr = getattr(self._user_args, "no_"+args[-1])
                if type(o_atr) == bool and o_atr == True:
                    return False
            except:
                pass

        return atr


class _BaseConfig:
    def __init__(self, config_file):
        self._config_file = config_file
        with open(config_file, "r") as f:
            self._conf = yaml.load(f.read()) or {}

    def dump(self, config_file=None):
        file = config_file or self._config_file
        with open(file, "w+") as f:
            yaml.dump(self._conf, f, default_flow_style=False)

    def _set_value(self, v, d, *args):
        if len(args) > 1:
            if args[0] not in d:
                d[args[0]] = {}
            return self._set_value(v, d[args[0]], *args[1:])
        else:
            d[args[0]] = v

    def set_value(self, v, *args):
        self._set_value(v, self._conf, *args)

    def _get_value(self, d, *args):
        if len(args) > 1:
            return self._get_value(d[args[0]], *args[1:])
        else:
            return d[args[0]]

    def get_value(self, *args):
        return self._get_value(self._conf, *args)


class BaseOptions:
    def __init__(self, config_file, args_desc):
        self._config = _BaseConfig(config_file)
        self._args = _BaseArgs(args_desc)

        # Modified options will be checked only against config values, not arguments
        self._modified_options = []

    def save_config(self):
        self._config.dump()

    def get_value(self, *args):
        try:
            arg = self._args.get_value(*args)
            if args not in self._modified_options and arg is not None:
                return arg
        except:
            pass

        return self._config.get_value(*args)

    def set_value(self, v, *args):
        self._config.set_value(v, *args)
        self._modified_options.append(args)

    def get_or_set(self, v, *args):
        try:
            return self.get_value(*args)
        except KeyError:
            self.set_value(v, *args)
            if v == "":
                print("{} must be defined".format(args[-1]))
                raise
            else:
                return v

    def __getitem__(self, key):
        return self.get_value(key)

    def __setitem__(self, key, value):
        self.set_value(value, key)
