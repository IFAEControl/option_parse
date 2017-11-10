import option_parse

d = [
    {
        "flag_name": {"-t", "--test"},
    },
    {
        "flag_name": {"-t2", "--test2"},
        "others": {"action": "store_true"},
    },
]

o = option_parse.BaseOptions("/tmp/test.yml", d)
print(o.get_or_set("Default",  "test2", "test"))
#o["test2"]["test"] = "UpdateValue"
print(o["test2"])
o.save_config()
