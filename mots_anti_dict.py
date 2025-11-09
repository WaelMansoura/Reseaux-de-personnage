
def load_words(file_path):
    words = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()               # remove whitespace/newline
            if not line or line.startswith("#"):
                continue                      # skip empty lines or comment lines
            words.append(line)
    return words


if __name__ == "__main__":
    anti_words = load_words("antidict.txt")
    for word in anti_words:
        print(word)