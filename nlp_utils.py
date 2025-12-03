def read_file(path):
    with open(path, "r", encoding="utf8") as f:
        return f.read()
    
def load_anti_dict(path="antidict.txt"):
    s = set()
    try:
        with open(path, "r", encoding="utf8") as f:
            for line in f:
                # remove inline comments and surrounding whitespace
                content = line.split("#", 1)[0].strip()
                if not content:
                    continue
                s.add(content.lower())
        return s
    except FileNotFoundError:
        return set()