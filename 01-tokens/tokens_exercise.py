import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


def show(text):
    ids = enc.encode(text)
    id_pieces = [i for i in ids]
    pieces = [enc.decode([i]) for i in ids]
    print(f"{text!r}\n  {len(ids)} tokens -> {pieces} ids -> {id_pieces}\n")


if __name__ == "__main__":
    show("hello")
    show(" hello")
    show("Hello")
    show("unbelievable")
    show("2024-11-19")
    show("def add(a, b): return a + b")
    show("Ich brauche ein salat")
    show("I need a salad")
    show("hello          world\n\n\n\n")
