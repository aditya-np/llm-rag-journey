# 01 - Tokens

## Concept
(Explain in your own words: what is a token, why do LLMs use them, why do cost and context limits depend on them?)

## What I built
`tokens_exercise.py` - prints how different strings are split into tokens.

## Homework answers
1. Why do `"hello"`, `" hello"`, and `"Hello"` tokenize differently?
   - Three different tokens with three different IDs. The tokenizer has separate vocabulary entries for hello, hello (with the leading space), and Hello. It is case-sensitive and whitespace-sensitive, because the space is attached to the following word.
   - To see it, change show() to also print ids. You’ll get three different integers.
   - Why this matters later: To the model, Hello and hello are different inputs, which is one reason inconsistent casing and spacing in messy text hurts embeddings. Where a chunk is split, a leading space changes the token. Cleaning and chunking affect what the model sees at the integer level.
2. Non-English vs English tokens per word - what does it imply for cost and context budget?
   - Tokenizers are not applying “English usage” to other text. The vocabulary is learned from a training corpus by repeatedly merging the most frequent character sequences. Since that corpus is mostly English, common English words get their own tokens.
   - The same content costs more and fills the context window faster in Foreign Language than in English.
3. What does the excess-whitespace example say about why cleaning matters?
   - If the runs of spaces and newlines collapsed into only a few tokens, that’s the tokenizer compressing repeated characters. The bigger damage in real documents is the accumulated noise (broken line breaks, repeated headers, junk from PDF extraction), which wastes tokens and degrades embeddings.
   - Collapse runs of spaces/tabs to one space, and collapse 3+ newlines to 2. Preserves structure and removes noise.
4. Pages that fit in 128k tokens (at ~1.3 tokens/word), and why not to fill it?
   - 128k tokens would be 98k words at the above rate. Lets say a page has 500 words. Thats around 200 pages.
   - Reason on why not to fill it:
     - Cost
     - Latency - Nore input tokens, slower responses.
     - Accuracy - Models use information in the middle of very long prompts less reliably. Even when everything fits in the context window, the model doesn’t use all of it equally well. It tends to use information at the beginning and end of the prompt best and is least reliable on information in the middle. Researchers observed a U-shaped accuracy curve in a 2023 paper, “Lost in the Middle.” Newer models handle this better than older ones, but the effect hasn’t fully disappeared, so you should design for it.
     - Output shares the window - The context window is a budget for input and output together. Your prompt tokens and the model’s answer tokens both come out of the same limit. 
     - Reason why RAG exists is because of such cases, where only relevant chunks are retrived.

## What I learned / what broke
-

## How to run it
```bash
pip install -r requirements.txt
python 01-tokens/tokens_exercise.py
```
