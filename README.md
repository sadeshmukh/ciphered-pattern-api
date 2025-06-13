# Ciphered Pattern API

A simple API to retrieve possible words given word patterns (as used in simple substitution ciphers).
Data was generated from the Phoenix word list (http://www.cryptogram.org/downloads/words/dict.new.zip), with frequencies from the Google Books ngram dataset (http://norvig.com/mayzner.html)

Thanks to DARINGFLAIR for the PDF that inspired this (https://www.cryptogram.org/downloads/Ranked-Pattern-Word-List-DARINGFLAIR.pdf).

## Setup

1. Create a virtual environment and install dependencies:

```bash
uv venv && uv pip install -r pyproject.toml
```

## Running the API

Start the server:

```bash
PORT=8000 uv run python main.py
```

The API will be available at http://localhost:8000.

Run with hot reload:

```bash
PORT=8000 uv run python main.py --dev
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
