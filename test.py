import options

d = {
    "flag_names": {"-t", "--test"},
}

o = options.BaseOpt("/tmp/test.yml", d)
print(o.get_or_set("Default",  "test2", "test3"))
print(o["test2"]["test3"])
print(o.get_value("test"))
o["test2"]["test3"] = "UpdateValue"
o.save_config()
