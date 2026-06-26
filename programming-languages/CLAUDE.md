# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Study material for a course based on EOPL (*Essentials of Programming Languages*): a series of
small languages built as Scheme interpreters, grouped by EOPL chapter. Each language is described
as a *delta* over the previous one (LET is the full baseline; the rest add or change pieces).
`summary.md` is the canonical, self-contained doc (~125KB) — it documents every language plus
exam-reference cheatsheets and the `main.py`/`infer` study tooling (there is no separate README).
`type-infer-questions.md` holds worked type-inference problems.

## Layout

Each language lives in its own directory (`chapter3/let/`, `chapter4/implicit-refs/`, etc.) and is a
self-contained Racket/EOPL interpreter following the standard EOPL multi-file split:

- `lang.scm` — grammar (lexer + `define-datatype` AST via `sllgen`)
- `interp.scm` — `value-of` / `value-of-program`
- `data-structures.scm` — `expval` constructors/extractors, environment & proc representations
- `environments.scm` — environment ops
- `store.scm` — mutable store (chapter 4+ only)
- `checker.scm` / `inferrer.scm` + `unifier.scm` / `substitutions.scm` — type phase (chapter 7 only)
- `tests.scm` — `test-list` of `(name program expected)` triples
- `top.scm` — entry module wiring it all together; exports `run` and `run-all`
- `drscheme-init.scm` — EOPL `sllgen`/`define-datatype` shims

Top-level dirs: `chapter3/` (LET → PROC → LETREC, plus `lexaddr`), `chapter4/` (refs, mutable/call-by
variants), `chapter7/` (`checked`, `inferred`). `envs/` is the scratch area where `langs.py` builds
working copies; `features/` holds reusable feature diffs (see below); `ignore/` is git-ignored
coursework/PDFs.

## Running an interpreter / its tests

Requires **Racket** with the EOPL collection (`racket` on PATH). From inside a language directory:

```sh
racket -e '(require "top.scm") (run-all)'   # run that language's full test suite
```

A passing suite prints `No bugs found.`. The paths in `(require ...)` are relative, so commands must
be run from within the language's own directory.

## main.py — the study harness

`main.py` (pure stdlib, no external `diff`/`patch`) manages "features": a feature is a hand-edit to a
language captured as a portable unified diff in `features/<lang>-<feature>.diff`. Working envs always
live under `envs/`. Lang names accept unique suffixes (e.g. `ds-rep`); env folders are named
`<lang>-<env>`. The `infer` Hindley-Milner type checker is fully inlined into `main.py` (there is no
separate module).

```sh
python3 main.py list                           # known langs / envs / features
python3 main.py init <lang> <env>              # copy a pristine lang into envs/<lang>-<env>
python3 main.py import <feature> <env>         # apply features/<lang>-<feature>.diff onto the env
python3 main.py export <env> <feature>         # capture an env's edits back into a feature diff
python3 main.py diff <env>                      # print an env's current diff to stdout
python3 main.py test <env>                      # run one env's Racket test suite (racket -e ... run-all)
python3 main.py test-all                        # apply every feature to a fresh env, run its tests, clean up
python3 main.py export-all                      # regenerate features.md (repo root) from all diffs
python3 main.py smoke                           # test-all + export-all + infer on an example (no result checks)
python3 main.py infer [args...]                 # Hindley-Milner type inference (fully inlined; no external module)
```

`test <env>` just shells out to `racket -e '(require "top.scm") (run-all)'` in that env (a success
prints `No bugs found.`). `test-all` is the closest thing to CI: it does that for every feature on a
fresh env and reports PASS/FAIL, treating output as passing only if it contains `no bugs found` and
not `incorrect`. `smoke` is a quick end-to-end run of the harness with no result checks.

## Conventions when extending a language

- Adding a construct means touching the same trio in lockstep: grammar in `lang.scm`, an AST
  variant + `value-of` case in `interp.scm`, and any new `expval` kind in `data-structures.scm`.
- Add a corresponding entry to `test-list` in `tests.scm` so `run-all` exercises it.
- To make a change reusable across study sessions, develop it in an `envs/` env and `export` it as a
  feature diff rather than editing a canonical `chapter*/` language in place.
- Prefer changing the relevant data structure (e.g. add a field to the `procedure` datatype) over
  synthesizing an AST node inside `value-of` to reuse another construct's logic — the structural
  version is the one to keep.

## Reviewing the feature catalogue (features.md)

When asked to extract functions/tricks/concepts from the feature list, **skip edits to the run/test
mechanism** — they're not interesting. In particular, ignore changes to `top.scm`'s
`sloppy->expval`/`run`/`run-all` (e.g. teaching the harness to accept a new value kind). Focus on the
language itself: grammar, `value-of`, data structures, environments, and the store.
