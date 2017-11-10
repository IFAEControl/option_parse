import options

d = {
    "flag_names": [{"-t", "--test"}, {"-l", "--lol"}],
}

o = options.BaseOpt("/tmp/test.yml", d)
print(o.get_or_set("Default",  "test2", "test"))
#o["test2"]["test"] = "UpdateValue"
o.save_config()
