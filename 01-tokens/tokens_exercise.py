import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


def show(text):
    ids = enc.encode(text)
    pieces = [enc.decode([i]) for i in ids]
    print(f"{text!r}\n  {len(ids)} tokens -> {pieces}\n")


if __name__ == "__main__":
    show("hello")
    show(" hello")
    show("Hello")
    show("unbelievable")
    show("2024-11-19")
    show("def add(a, b): return a + b")
    show("Das ist ein sehr langes deutsches Wort: Donaudampfschifffahrt")
    show("hello          world\n\n\n\n")
