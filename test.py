from option_parse import AppOptions

conf_desc = {
    "a": {
        "b": {"default": 100},
    },
}

args = [
    {
        "name": {"-t", "--test"},
    },
    {
        "name": {"-t2", "--test2"},
        "others": {"action": "store_true"},
    },
]


opt = AppOptions("option_parse", "test", conf_desc, args)

print(opt["test2"])
print(opt["test"])
print(opt["b"])
opt["a"]["b"] = 101
print(opt["b"])
opt.save_config()