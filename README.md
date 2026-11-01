# MATHutrice

An LLM-based maths tutor that helps EPF first-year students practise mathematical tools. A student picks a notion, sits a positioning test, then trains one question at a time; the tutor scores each competence, diagnoses gaps and recommends another notion. A chat answers questions, streamed word by word.

Design Document for this fork: [EPF-MDE/MATHutrice#66](https://github.com/EPF-MDE/MATHutrice/issues/66).

It is a FastAPI application (`mathutrice/app.py`) with a SQLModel database (SQLite locally) and one OpenAI-compatible LLM endpoint, Mistral by default.

## Run it

Follow the smoke test: **[docs/smoke-test.md](docs/smoke-test.md)**. It installs the project with [uv](https://docs.astral.sh/uv/), creates `.env` from `.env.example`, starts the application and checks it in the browser and from the command line.

Every setting the application reads is listed, with its meaning, in [`.env.example`](.env.example). Your LLM key goes in `.env` only: `.env` is ignored by git and must never be committed.

## Check the package boundaries

```sh
uv run tach check
uv run python scripts/check_cycles.py
```

The rules they enforce are in [mathutrice/README.md](mathutrice/README.md).

## Layout

```
mathutrice/
  app.py               the FastAPI application: routes, sign-in, sessions
  models.py            the database tables
  database.py          the engine, built from DATABASE_URL
  fonctions_python/    question generation, grading, chat, LLM client
  lacune_evaluation/   gap diagnosis by the LLM
  templates/, static/  the pages
docs/
  smoke-test.md        how to run and check a fresh clone
  adr/                 architecture decisions
scripts/
  check_cycles.py      the cycle half of the Architecture Check
```

The vocabulary of the domain is in [CONTEXT.md](CONTEXT.md).

## License

MIT, see [LICENSE](LICENSE).
