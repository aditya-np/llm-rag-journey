# LLM + RAG Journey

My structured, phase-by-phase path to learning LLMs, text cleaning, embeddings,
vector databases, and Retrieval-Augmented Generation (RAG) - built hands-on, with measured results.

## Pipeline I am learning

```
Raw docs -> Cleaning -> Chunking -> Embeddings -> Vector DB
User question -> Embedding -> Retrieval -> Context -> LLM -> Answer
                                                  \-> Evaluation (metrics)
```

## Progress

- [ ] 01 - Tokens
- [ ] 02 - Text cleaning
- [ ] 03 - LLMs and text generation
- [ ] 04 - Embeddings and vector databases
- [ ] 05 - RAG from scratch
- [ ] 06 - Evaluation and improvement

## Flagship projects (graduated from this journal)

- [ ] `rag-app` - end-to-end RAG app with citations and a live demo
- [ ] `rag-eval-lab` - evaluation-driven improvements with before/after metrics

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then add your API key
```

## Repo layout

Each lesson folder has a `README.md` with four sections: Concept, What I built,
What I learned / what broke, How to run it. Running notes live in `notes/`.
