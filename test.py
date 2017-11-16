import option_parse

d = [
    {
        "name": {"-t", "--test"},
    },
    {
        "name": {"-t2", "--test2"},
        "others": {"action": "store_true"},
    },
]

o = option_parse.BaseOptions("/tmp/test.yml", d)
print(o.get_or_set("Default",  "test2", "test", "test3").as_(str))
print("A=",o["test2"]["test"]["test3"])
o["test2"]["test"]["test3"] = "A"
print(o.get_value("test3").as_(str))
o.save_config()
