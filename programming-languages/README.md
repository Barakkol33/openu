# Programming Languages Summary

A study summary for the Open University _Programming Languages_ course, built on **EOPL**
(_Essentials of Programming Languages_). The course teaches **Scheme**, then uses it to build a
series of small languages by writing interpreters; each language is described as what it _adds or
changes_ versus the previous, so **LET** is explained in full and the rest are deltas.

Note: Here is a very good summary, which was helpful when building this summary: — https://summary-of-programming-languages.pages.dev/

This document has two main parts, plus an appendix:

- **[Learning the course](#learning-the-course)** — the bulk of the material: Scheme, then the
  interpreters chapter by chapter (Foundations → Ch.3 → Ch.4 → Ch.7). Read this to learn.
- **[Preparing for the exam](#preparing-for-the-exam)** — focused revision for the two exam question
  types: **feature development** (questions 1–2) and **type inference** (question 3). Pulls together
  the [feature-development toolkit](#important) (overview → grammar → interpreter + SDK) and the
  by-hand inference method.
- **[Appendix — variants & optimizations](#appendix--variants--optimizations)** — side branches off
  the main path (a scoping exercise, LEXADDR, call-by-reference, call-by-need).

**Study tooling in this repo** — three things make revision faster, each aimed at an exam question:

- **`main.py`** — a harness for the _feature-development_ drill (Q1–Q2). `init` a throwaway copy of a
  language, hand-edit it, and `test` it against its Racket suite in seconds, so you rehearse the exact
  exam motion — wiring a construct through grammar → interp → data-structures — instead of copying
  files around. Reference in [Part 1](#part-1--features-development-questions-1--2).
- **[features.md](features.md)** — a catalogue of worked language extensions, each a small annotated
  diff: a bank of _solved_ feature-development problems to read, replay, and learn the patterns from.
- **`infer`** — `python3 main.py infer '<prog>'` prints the full Hindley–Milner derivation step by
  step, so you can check your by-hand type-inference work for Q3 against the tool. Reference in
  [Part 2](#part-2--type-inference-question-3).

**The Mamans (course assignments).** The graded assignments split into two kinds, and each maps onto a
part of this doc. The early ones drill **Scheme itself** — for those, work from the [Scheme](#scheme)
introduction under _Learning the course_. The later ones are **feature development** or **type
inference**, exactly the shape of the exam — for those, use [Preparing for the exam](#preparing-for-the-exam)
([feature work](#part-1--features-development-questions-1--2) /
[inference](#part-2--type-inference-question-3)). Several solved feature Mamans are captured as diffs in
[features.md](features.md).

# Learning the course

Work through this to learn the material: first Scheme, then how each interpreter is built. The
languages are grouped by EOPL chapter and each is presented as a delta over the previous one.

## Foundations — inductive data, grammars, abstraction

The mathematical groundwork before any interpreter: how to _define_ the data a language is made of, how to _write
functions_ over it, and how to keep code independent of representation.

### Inductive definitions & BNF

Before writing an interpreter you define, mathematically, what data it accepts, using **inductive (recursive)
definitions** — complex structures built from base cases. We write them as **grammars** in BNF:

```text
Bintree ::= Int | (Symbol Bintree Bintree)          % a leaf, or a node with two sub-trees
LcExp   ::= Identifier                              % lambda-calculus expression:
          | (lambda (Identifier) LcExp)             %   a variable,
          | (LcExp LcExp)                           %   a lambda, or an application
```

- **Bound variable** — in `(lambda (x) …)` the declared identifier `x` becomes _bound_ at every occurrence inside
  the body; an identifier that isn't bound is _free_.

### Follow the grammar

The single most important rule in the course: **a function's structure must mirror the grammar's structure.**

The recipe:

1. Write **one function per non-terminal** in the grammar.
2. Inside it, use `cond`/`cases` with **one arm per production** (alternative) of that type.
3. Wherever a production contains an inductive sub-structure (a sub-tree, a sub-expression), make a **recursive
   call** in that arm.

Every `value-of`, `type-of`, and `occurs-free?` in this summary is an instance of this recipe.

### Data abstraction

**Data abstraction** is the strict separation between _how data is used_ (the **interface**) and _how it is stored_
(the **implementation**). If the interpreter is **representation-independent**, you can swap the internal
representation without breaking client code.

The interface has two kinds of operation:

- **Constructors** — build the type from raw data (`empty-env`, `extend-env`).
- **Observers** — ask about a value without changing it, split into:
  - **Predicates** — return a boolean: "is it an X?" (`zero?`, `lambda-exp?`).
  - **Extractors** — pull a specific piece out (`lambda-exp->body`).

`define-datatype` ([below](#define-datatype--cases)) generates the constructors and predicates for you.

**Before vs. after abstraction** — `occurs-free?` (does a variable occur free in a λ-expression?):

```scheme
;; ❌ before — tied to the list representation; using car/cadr breaks if the representation changes
(define occurs-free?
  (lambda (search-var exp)
    (cond
      ((symbol? exp) (eqv? search-var exp))
      ((eqv? (car exp) 'lambda)
       (and (not (eqv? search-var (car (cadr exp))))
            (occurs-free? search-var (caddr exp))))
      (else (or (occurs-free? search-var (car exp))
                (occurs-free? search-var (cadr exp)))))))

;; ✅ after — pattern matching through an abstract interface; oblivious to the physical representation
(define occurs-free?
  (lambda (search-var exp)
    (cases expression exp
      (var-exp (id) (eqv? search-var id))
      (lambda-exp (id body) (and (not (eqv? search-var id)) (occurs-free? search-var body)))
      (app-exp (rator rand) (or (occurs-free? search-var rator) (occurs-free? search-var rand))))))
```

## Scheme

### Basics

- Learning scheme site (if it helps you):
  https://jaredkrinke.github.io/learn-scheme/toc.html
- Code stored in `.scm` text files.
- Interpreter — Racket. Run in CLI: `racket program.scm`.
- File starts with a language line: `#lang scheme`.
- Everything is an **expression**; a program is a sequence of expressions, each evaluated in order.
- Prefix notation: the operator comes first — `(+ 1 2)`, `(f p1 p2 p3)`.

### Loading code

- `(require "utils.scm")` — load another `.scm` file from the same dir.
- `(require "utils.scm" "env.scm" eopl)` — load multiple files and the built-in `eopl` library (EOPL = _Essentials of Programming Languages_).

### Values & literals

- Numbers: `1`, `-1`, `6`.
- Booleans: `#t`, `#f`.
- Symbols (quoted): `'abc`, `'x` — an unevaluated name/atom.
- Quoted lists: `'(a b c)`, `'(3 2 1)`, nested `'(() (3) (2 1))`.
- Empty list: `'()`; the list of one empty list: `'(())`.

### Variables & functions

- Define a value/function: `(define name value)`.
- Lambda (anonymous function): `(lambda (arg1 arg2) body)`.
- Common pattern — bind a name to a lambda:
  ```scheme
  (define my_append1
    (lambda (lst1 lst2)
      (if (null? lst1) lst2
          (cons (car lst1) (my_append1 (cdr lst1) lst2)))))
  ```
- Call: `(my_append1 '(a b) '(x y z))`.
- Recursion replaces loops (the function calls itself, e.g. on `(cdr lst)`).

### Control flow

- **What counts as true?** Everything except `#f`. Numbers, `'()`, strings — all truthy in a test.
- `if`: `(if condition then-expr else-expr)`. The `else` branch is **mandatory** — the academic EOPL language has
  no one-armed `if`.
- `cond` (multi-branch): each clause is `(test result)`; `else` / `#t` as the catch-all.
  ```scheme
  (cond
    ((eqv? (car env) 'empty-env) #f)
    ((eqv? (car env) 'extend-env) ...)
    (#t #f))
  ```
- **Iron rule — check the type before the value.** Test `(number? n)` _before_ a size test like `(> n 0)`, or the
  comparison may blow up on a non-number.
- `let` — local bindings: `(let ((name value) …) body)`, e.g.
  ```scheme
  (let ((a 3) (b 4)) (+ a b))   ; => 7
  ```

#### The `let` family — binding scope

The three forms differ in **whether one binding can use another's value** — this is exactly the distinction the
chapter-3 interpreters make precise (`let` vs `letrec`):

- **`let`** — _parallel_. Every right-hand side is evaluated in the **outer** env, before any binding takes effect,
  so bindings in the same block **cannot** refer to each other.
  ```scheme
  (let ((x 5) (y (+ x 1))) y)     ; ERROR — x is not visible to y's expression
  ```
- **`let*`** — _sequential_. Sugar for nested `let`s, so each binding sees the ones **above** it (earlier → later,
  not the reverse).
  ```scheme
  (let* ((x 5) (y (+ x 1))) y)    ; => 6
  ```
- **`letrec`** — _recursive_. All names are in scope **inside every** right-hand side, but you can only safely _use_
  a sibling's value when the reference is **deferred** — i.e. the RHS is a `lambda`, so the lookup happens at call
  time. That's what `letrec` is for: self- and mutually-recursive procedures. (Conceptually the slots are created
  empty first, then filled; using a not-yet-filled sibling _immediately_ errors.)
  ```scheme
  (letrec ((fact (lambda (n) (if (zero? n) 1 (* n (fact (- n 1)))))))
    (fact 5))                     ; => 120  — fact sees itself
  (letrec ((even? (lambda (n) (if (zero? n) #t (odd?  (- n 1)))))
           (odd?  (lambda (n) (if (zero? n) #f (even? (- n 1))))))
    (even? 10))                   ; => #t   — even?/odd? see each other (deferred, inside lambdas)
  ```

**Choosing one (in interpreter branches too):** bindings independent → `let`; each needs the previous → `let*`;
a binding is a recursive `lambda` that refers to itself or a sibling → `letrec`. (That's why a local recursive
helper like `bind-all`/`value-of-begins` must sit in a `letrec` — it has to see its own name to recurse; a plain
`let` wouldn't.)

This is the same idea the interpreter chapter formalizes: plain `let` extends the env _after_ evaluating the value
([LET](#let)), while `letrec` must make the binding visible to its own body ([LETREC](#letrec)).

### Lists

A list is a chain of memory cells (cons cells / pairs). `cons` allocates one such cell:

- Build: `list`, `cons` (prepend an item to a list).
- Access: `car` (left of the cell — the element), `cdr` (right of the cell — the pointer to the rest),
  `cadr` (2nd), `caddr` (3rd), `cadddr` (4th).
- `append` — concatenate lists.
- `length` — number of elements.
- `map` — apply a function to every element, returning a new list:
  `(map (lambda (x) (* x x)) '(1 2 3))` ⇒ `'(1 4 9)`. The go-to tool for an `(arbno …)` field of sub-expressions:
  `(map (lambda (e) (value-of e env)) exps)`.
- `foldr` — **right fold**: collapse a whole list to one result by combining elements right-to-left.
  `(foldr f init lst)` walks to the end, starts from `init`, and folds back leftward — i.e.
  `(foldr f init '(a b c))` = `(f a (f b (f c init)))`. So `f` takes `(element acc-so-far)` and `init` is the
  value returned for the empty list. Examples: `(foldr + 0 '(1 2 3))` ⇒ `6`; `(foldr cons lst2 lst1)` rebuilds
  `lst1` onto `lst2`, i.e. `append`; with an `if` inside `f` it becomes `filter`. (`foldl` is the same idea but
  combines left-to-right; mind the dialect argument-order gotcha covered later.)

**`pair?` vs `list?` — a common exam trap:**

- `(pair? x)` — is `x` a single cons cell? Doesn't care what's inside or how it ends.
- `(list?  x)` — is `x` a _proper_ chain of pairs ending in the empty list `'()`? Checks recursively.

The difference shows up on a **dotted pair** — a cons cell whose `cdr` is _not_ a list:

```scheme
(cons 1 2)            ; => '(1 . 2)   a single cell, cdr is 2 (not a list)
(pair? (cons 1 2))    ; => #t         it IS one cons cell
(list? (cons 1 2))    ; => #f         but the chain doesn't end in '()

(list? '(1 2 3))      ; => #t         proper list: ends in '()
(pair? '(1 2 3))      ; => #t         also a cons cell (its first one)
(pair? '())           ; => #f         '() is the empty list, not a cell
(list? '())           ; => #t         the empty list IS a (zero-length) list
```

So every proper list (except `'()`) is also a pair, but not every pair is a list.

### Predicates & equality

- `null?` — empty list?
- `zero?` — equals 0?
- `even?` — even number?
- `number?` — is a number?
- `eqv?` — identity/symbol equality (used to compare symbols like `'extend-env`).
- `equal?` — deep structural equality.
- Comparisons: `=`, `>=`, etc.

### Arithmetic

- `+`, `-`, `*` in prefix form: `(- size 1)`, `(* x number)`, `(+ 1 (degree rest))`.

### Recursion & tail calls (TCO)

Since there are no loops, recursion does all the iterating — but _how_ you recurse decides the memory cost.

- **Stack recursion** — the recursive call is _not_ the last thing done; there's still work waiting (e.g.
  `(+ 1 (f …))`). Each call needs a new **stack frame** to remember that pending work → O(n) space.
- **Tail recursion (TCO)** — the recursive call is the **very last** action (in _tail position_), nothing waits
  on its result. The compiler reuses the same frame each time → **O(1) space**. Usually done with an
  **accumulator** parameter that carries the partial result.

```scheme
(define sum      (lambda (n) (if (zero? n) 0 (+ n (sum (- n 1))))))                ; stack: + waits → O(n)
(define sum-tco  (lambda (n acc) (if (zero? n) acc (sum-tco (- n 1) (+ acc n)))))  ; tail → O(1)
```

### Modules

Reusable library files use the module form instead of `#lang scheme`:

```scheme
(module utils (lib "eopl.ss" "eopl")
  (provide equal?? report-unit-tests-completed)
  ...)
```

- `(provide name ...)` — export bindings to files that `require` this module.
- `(module name (lib "eopl.ss" "eopl") ...)` — define a module on top of the EOPL library.

### Macros

Defined with `define-syntax` + `syntax-rules` (pattern → expansion). The `equal??` test macro errors if two expressions aren't equal, printing the _unevaluated_ source:

```scheme
(define-syntax equal??
  (syntax-rules ()
    ((_ x y)
     (let ((x^ x) (y^ y))
       (if (not (equal? x y))
           (eopl:error 'equal?? "~s is not equal to ~s" 'x 'y))))))
```

### define-datatype & cases

The `eopl` library's two workhorses for building tree-shaped data (used everywhere in the interpreters):

- `define-datatype` — define a tagged variant (sum) type:
  ```scheme
  (define-datatype poly poly?
    (poly-zero)
    (poly-complex (coefficient number?) (rest poly?)))
  ```
  Creates constructors (`poly-zero`, `poly-complex`) and a predicate (`poly?`); each field has a contract predicate.
- `cases` — pattern-match/destructure a datatype value, one branch per variant:
  ```scheme
  (cases poly polynom
    (poly-zero () -1)
    (poly-complex (coefficient rest) (+ 1 (degree rest))))
  ```
- `(list-of pred?)` — an EOPL helper that **builds a predicate** for a field that holds a _list_ where every element
  satisfies `pred?`. Use it as the contract when a variant stores a list:
  ```scheme
  (define-datatype expval expval?
    (num-val   (value number?))
    (tuple-val (vals (list-of expval?))))   ; vals = a list of ExpVals
  ```
  `(list-of expval?)` ≡ "a list, each element an `expval?`". So `(list-of number?)`, `(list-of symbol?)`, etc.
  Without it you'd only get a bare `list?` (no element check). Pairs with `map` in the matching `value-of` branch:
  `(tuple-exp (exps) (tuple-val (map (lambda (e) (value-of e env)) exps)))`.

> ⚠️ **Common trap — the `else` branch takes no field list.** Write `(else …)`, never `(else (x y) …)`.
> Putting a parenthesized variable list on `else` won't compile.

### Environments

An **environment** maps variable names to values — built up as nested tagged lists. This is the same idea the interpreters reuse.

- `(empty-env)` → `(list 'empty-env)` — the base, holds no bindings.
- `(extend-env var val env)` → `(list 'extend-env var val env)` — add one binding on top of an existing env.
- `(apply-env env var)` — walk the chain with `cond`/`eqv?`, return the value of the first matching `var`
  (innermost binding wins), or error if none is found.

```scheme
;; d=6, y=8, x=7, y=14  (the inner y=8 shadows the outer y=14)
(define e
  (extend-env 'd 6
  (extend-env 'y 8
  (extend-env 'x 7
  (extend-env 'y 14
  (empty-env))))))

(apply-env e 'd)   ; => 6
(apply-env e 'y)   ; => 8   (first match, not 14)
(apply-env e 'z)   ; => error: No binding for z
```

Because the env is just a tagged list, you can inspect it directly: `(car env)` is the tag
(`'empty-env` / `'extend-env`), and for an extend node `(cadr env)` is the var, `(caddr env)` the value,
`(cadddr env)` the rest of the env — the pattern `is-num?` uses to check a binding's type.

#### Procedural representation

The tagged list is just _one_ representation. Mathematically an environment **is** a function from names to values
(`g(var₁) = val₁`), so — by [data abstraction](#data-abstraction) — you can represent it directly **as a function**
instead of a data structure. Same interface, different implementation; client code (`apply-env`) doesn't change:

```scheme
(define empty-env                       ; a procedure that always reports "not found"
  (lambda () (lambda (search-var) (report-no-binding-found search-var))))

(define extend-env                      ; a procedure that answers for one var, else delegates
  (lambda (saved-var saved-val saved-env)
    (lambda (search-var)
      (if (eqv? search-var saved-var) saved-val (apply-env saved-env search-var)))))

(define apply-env                       ; "looking up" = just calling the environment
  (lambda (env search-var) (env search-var)))
```

**Recipe for a procedural representation:** find the lambdas that return a value of the type → make them the
constructors (closing over the type's free variables); find where a value is _used_ → replace with the matching
`apply`. Now client code is fully representation-independent.

### EOPL extensions

- `eopl:error` — raise an error: `(eopl:error 'apply-env "No binding for ~s" search-var)`.
- `eopl:printf` — formatted print (`~s` = value, `~%` = newline).
- `print` — print a value.

### Idioms

- **Recursion over lists** — base case `(null? lst)` / `(zero? n)`, recurse on `(cdr lst)`.
- **Inline unit tests** — every file ends with `(equal?? (f ...) expected)` lines that run on load.
- **Datatype + cases** — model a data structure (polynomial, environment) as a variant type and dispatch with `cases`.
- **Tagged-list environment** — represent an env as `(list 'extend-env var val env)` and walk it with `cond`/`eqv?`.

### Example program

Two functions touching most of the above — `#lang scheme`, `define`/`lambda`, `if`/`cond`/`let`, recursion,
list ops (`car`/`cdr`/`cons`/`append`/`length`/`foldr`), predicates (`null?`/`zero?`/`even?`/`number?`/`eqv?`/`equal?`)
and arithmetic. Save as `example.scm` and run with `racket example.scm`.

```scheme
#lang scheme

;; Sum only the even numbers in a list (recursion + cond + predicates + arithmetic).
(define sum-evens
  (lambda (lst)
    (cond
      ((null? lst) 0)                               ; base case: empty list
      ((not (number? (car lst)))                    ; skip non-numbers
       (sum-evens (cdr lst)))
      ((even? (car lst))                            ; even -> add it
       (+ (car lst) (sum-evens (cdr lst))))
      (#t (sum-evens (cdr lst))))))                 ; odd -> skip

;; Tag each list with its length, then keep only the non-empty ones.
;; (lambda, let, foldr, cons, append, length, zero?, if, eqv?)
(define label-nonempty
  (lambda (lists)
    (foldr
      (lambda (lst acc)
        (let ((n (length lst)))
          (if (zero? n)
              acc                                   ; drop empty lists
              (cons (append (list 'len n) lst) acc))))
      '()
      lists)))

;; --- run it ---
(print (sum-evens '(1 2 a 4 5 6)))                  ; => 12
(print (label-nonempty '((a b) () (x))))            ; => ((len 2 a b) (len 1 x))
(print (equal? (sum-evens '(2 4)) 6))               ; => #t
(print (eqv? (length '()) 0))                       ; => #t
```

## Chapter 3 — Expressions & Procedures

This is where the course's real subject begins, and it is meant to be read as **one continuous story**. From
here on we **write interpreters** for a family of small languages, with Scheme as the implementation language.
The first language, **LET**, is built in full — every file, end to end — because it is the skeleton every later
language reuses. After that, each language is told as a **delta**, always in the same four beats: _where we are_,
_what the language still can't do_, _the one new idea that fixes it_, and _the few lines that idea forces us to
change_. Nothing is ever rebuilt from scratch, so read them in order — each one only makes sense on top of the last.

The arc of the whole part:

- **Chapter 3** grows a functional core: binding (**LET**) → first-class procedures (**PROC**) → recursion
  (**LETREC**). (Lexical addressing, **LEXADDR**, is an optimization parked in the [Appendix](#appendix--variants--optimizations).)
- **Chapter 4** adds **mutable state** by introducing one new component — the _store_ — and reusing it three ways.
- **Chapter 7** adds a **type system** that runs _before_ evaluation.

Start with LET; everything after it is a small, named step.

### LET

**The starting point — and the foundation for everything else.** LET is small (arithmetic, `let`-binding,
conditionals), but the *machinery* it sets up — the scan→parse→evaluate pipeline, expressed values, the
environment, and `value-of` — is exactly what every later language inherits. So we walk it slowly and in full;
PROC, LETREC, and the chapter-4/7 languages will then only describe what they *add* to this. Learn it once here.
Source: [let](chapter3/let/).

**Example** — programs in the LET language (`%` starts a comment):

```text
let x = 3 in let y = 4 in -(x, y)        % nested let, subtraction   => -1
if zero?(-(11,11)) then 3 else 4         % conditional on zero?       => 3
```

#### How an interpreter is built

From here on Scheme is the _implementation_ language: we write interpreters for small target languages. The mental
model is the same for every language in the course — only the details change.

##### Vocabulary

The few terms that the rest of the chapter leans on:

- **Syntax** — the _form_ a program is allowed to take: which symbols, in which order. Split into two layers:
  - **Lexical syntax** — how characters group into **tokens** (the "words": numbers, identifiers, keywords,
    punctuation). Defined by the **lexical spec** (`the-lexical-spec`) and applied by the **lexer / scanner**.
  - **Grammatical syntax** — how tokens group into larger structures (expressions, programs). Defined by the
    **grammar** (`the-grammar`) and applied by the **parser**.
- **Token** — one indivisible lexical unit, e.g. the number `5`, the identifier `x`, the keyword `let`, the `(`.
  Whitespace and comments are tokens the lexer is told to **skip**.
- **Lexer / scanner** — turns the raw character string into a flat list of tokens. ("scan" = lexing.)
- **Parser** — turns that token list into a tree (the **AST**) by matching it against the grammar.
- **Grammar / production** — a set of rules; each rule (a **production**) says "this kind of structure is made of
  these pieces in this order" and names the AST node it builds.
- **AST (abstract syntax tree)** — the parsed program as a tree of data values, with the throwaway punctuation
  removed. This is what the interpreter actually walks. Here, an EOPL datatype (`expression`).
- **Semantics** — what a program _means_ / does when run. That's the job of `value-of` (the next files), as opposed
  to syntax, which is only about its shape.
- **Spec** — short for _specification_: a declarative description. The **lexical spec** and the **grammar** are both
  specs — you state the rules, and SLLGen generates the lexer and parser from them.

##### The pipeline

```
 source string                front end                        interpreter
"-(5, x)"   ──scan&parse──▶  AST value  ──value-of──▶  ExpVal (num-val / bool-val / …)
            (lexer+grammar)  (diff-exp …)              evaluates the tree
```

1. **scan** — split the text into tokens (lexer).
2. **parse** — match tokens against the grammar, producing an **AST** (an EOPL datatype value).
3. **value-of** — recursively walk the AST against an **environment** and produce a value.

##### File layout (one folder per language)

Listed in build order — each file only `require`s ones above it, so this is also the order to read them:

| file                  | requires                                            | role                                                                                |
| --------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `drscheme-init.scm`   | —                                                   | library setup / boilerplate                                                         |
| `lang.scm`            | drscheme-init                                       | lexical spec + grammar; SLLGen turns these into the parser **and** the AST datatype |
| `data-structures.scm` | — (PROC+ requires lang, for `expression?`)          | the **values** the interpreter computes (`expval`) and helper datatypes             |
| `environments.scm`    | data-structures                                     | `empty-env` / `extend-env` / `apply-env` / `init-env`                               |
| `interp.scm`          | drscheme-init, lang, data-structures, environments  | `value-of` — the evaluator                                                          |
| `tests.scm`           | —                                                   | test cases for `run-all`                                                            |
| `top.scm`             | drscheme-init, data-structures, lang, interp, tests | glue: `(define run (lambda (s) (value-of-program (scan&parse s))))` + `run-all`     |

##### Two ideas to hold onto

- **Expressed vs. denoted values** — _expressed_ = what an expression evaluates to (numbers, booleans, later
  procedures); _denoted_ = what a variable is bound to in the env. Often the same set, but conceptually distinct.
- **`value-of expr env`** is the heart of every interpreter: one `cases` branch per AST node. Constants return
  themselves, variables do `apply-env`, compound forms evaluate their sub-expressions and combine the results.

The rest of this chapter walks the files in build order — `lang.scm` → `data-structures.scm` → `environments.scm`
→ `interp.scm` → `top.scm` — building up exactly how a source string becomes a value.

#### 1. `lang.scm` — lexer & grammar

Two definitions handed to SLLGen, which generates both the parser (`scan&parse`) and the AST datatypes.

##### The lexical spec (characters → tokens)

Each entry is `(token-name (pattern) action)`. The scanner chops raw text into tokens; the _action_ says what to
do with each ([lang.scm](chapter3/let/lang.scm)):

```scheme
(define the-lexical-spec
  '((whitespace (whitespace) skip)                                  ; drop spaces/newlines
    (comment ("%" (arbno (not #\newline))) skip)                    ; "%..." to end of line, dropped
    (identifier (letter (arbno (or letter digit "_" "-" "?"))) symbol) ; a name → a Scheme symbol
    (number (digit (arbno digit)) number)                           ; digits → a number
    (number ("-" digit (arbno digit)) number)))                     ; negative number
```

Vocabulary you'll keep seeing:

- `whitespace` / `letter` / `digit` — built-in character classes.
- `(arbno X)` — "**arb**itrary **no**." of `X`, i.e. zero-or-more (like `X*`).
- `(or A B C)` — any one alternative. `(not #\newline)` — any char except newline.
- **action** — `skip` discards the token; `symbol` makes its value a symbol; `number` makes it a number; `string` keeps the text.

So `identifier` = a letter followed by any run of letters/digits/`_`/`-`/`?`, delivered to the parser as a symbol.

##### The grammar (tokens → AST), and the one rule that matters

Each entry is `(left-hand-side (right-hand-side …) production-name)`:

```scheme
(define the-grammar
  '((program (expression) a-program)                                ; a whole program is one expression
    (expression (number) const-exp)                                 ; 42
    (expression ("-" "(" expression "," expression ")") diff-exp)   ; -(e1, e2)
    (expression ("zero?" "(" expression ")") zero?-exp)             ; zero?(e)
    (expression ("if" expression "then" expression "else" expression) if-exp)
    (expression (identifier) var-exp)                               ; x
    (expression ("let" identifier "=" expression "in" expression) let-exp)))
```

**THE RULE that links `lang.scm` and `interp.scm`:** in a right-hand side,

> **Quoted strings (`"-"`, `"("`, `"let"`, …) are literal syntax — they carry no data.
> Everything else (`expression`, `number`, `identifier`) is _data-bearing_ and becomes a field of the AST node,
> in left-to-right order. The third element (`diff-exp`) is the node's constructor name.**

So `(expression ("-" "(" expression "," expression ")") diff-exp)` produces a node `diff-exp` with **two** fields
(the two `expression`s) — the `"-"`, `"("`, `","`, `")"` are just punctuation the parser expects but throws away.

`sllgen:make-define-datatypes` reads the grammar and **auto-defines** the `program` and `expression` datatypes —
which is why `interp.scm` can `(cases expression …)` without ever defining `expression` itself. To see exactly what
got generated, call `(show-the-datatypes)`.

###### Which grammar names are yours, and what can repeat

- **You name** the production/constructor (`diff-exp`) and the token categories (`identifier`, `number`) — just
  identifiers you pick. The only rule is **consistency**: a token used in the grammar must be defined in the lexical
  spec, with the same spelling. (The RHS data-bearing items, though, are left **unnamed** here — they're only
  _types_; you name them later in interp.scm.)
- **`program` and `expression` are not built-in** — they're nonterminal names too, but in practice you leave them
  alone. Two reasons: the **first** nonterminal listed is the start symbol (so `program` must come first, whatever
  it's called), and each nonterminal name becomes the **generated datatype name** — rename `expression` and you'd
  have to change every `(cases expression …)` in `interp.scm` to match. So they're load-bearing convention, not
  free-to-rename like the constructor names.
- **Multiple is normal**, in three different senses:
  - _Many productions per nonterminal_ — `expression` has `const-exp`, `diff-exp`, `if-exp`, … That's how a
    nonterminal offers alternatives; each is a separate AST variant.
  - _Many fields per production_ — `diff-exp` has 2, `if-exp` has 3, `let-exp` has identifier + 2 expressions.
  - _One field holding many items_ — wrap an item in `(arbno expression)` or `(separated-list expression ",")` and
    that single field becomes a **list** of sub-ASTs (e.g. a call with N arguments). In the branch that variable is a
    list, so you `(map (lambda (e) (value-of e env)) the-list)`.

###### The SLLGen interface — what you write vs. what's generated

**SLLGen** (Scheme LL Grammar engine) is the library that turns your two specs into a working front end. It marks a
clean boundary: you write _declarations_, SLLGen generates the _code_. Both specs are consumed **only here in
`lang.scm`**, by four library calls — nothing downstream ever refers to `the-grammar` / `the-lexical-spec` again:

```scheme
(sllgen:make-define-datatypes the-lexical-spec the-grammar)              ; → defines the AST datatypes
(define scan&parse  (sllgen:make-string-parser  the-lexical-spec the-grammar))  ; → string → AST
(define just-scan   (sllgen:make-string-scanner the-lexical-spec the-grammar))  ; → string → tokens (debug)
(define show-the-datatypes
  (lambda () (sllgen:list-define-datatypes the-lexical-spec the-grammar)))       ; → prints the datatypes (debug)
```

Note `scan&parse` is defined as a plain value, not as `(define (scan&parse s) …)` — yet it **is** a function.
`sllgen:make-string-parser` is a _higher-order_ function: it builds a parser from the specs and **returns that
procedure**, which you then name. `define` just binds a name to a value, and a procedure is a value like any other;
you still call it as `(scan&parse "let x = 1 in x")`. (Same idea as the [procedural representation](#procedural-representation).)

| you write (input)                 | SLLGen call                    | it generates (output)                      | used downstream by                                                                                                  |
| --------------------------------- | ------------------------------ | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `the-lexical-spec`, `the-grammar` | `sllgen:make-define-datatypes` | the `program` / `expression` **datatypes** | `interp.scm` — `program` → `value-of-program` `(cases program …)`; `expression` → `value-of` `(cases expression …)` |
| (same two specs)                  | `sllgen:make-string-parser`    | **`scan&parse`**                           | `top.scm` — `(run …)`                                                                                               |
| (same two specs)                  | `sllgen:make-string-scanner`   | `just-scan` (tokens only)                  | manual lexer debugging                                                                                              |

Only **two of the four are essential**: `make-string-parser` (gives `scan&parse`, the function you actually call to
run code) and `make-define-datatypes` — the latter binds no name but its **load-time side effect** defines the AST
datatypes, so without it `interp.scm` won't even compile. The remaining two (`just-scan`, `show-the-datatypes`) are
debug helpers you could delete.

So the **written/non-written seam** is exactly the SLLGen boilerplate: above it you author the lexer spec, the
grammar, and (in the other files) `value-of`; everything else — the datatype constructors/predicates, the
`scan&parse` pipeline — is generated for you and referenced only by its products, never by the specs themselves.

#### 2. `data-structures.scm` — values (`expval`)

A LET expression evaluates to an **expressed value** — here a number or a boolean
([data-structures.scm](chapter3/let/data-structures.scm)):

```scheme
(define-datatype expval expval?
  (num-val  (value number?))
  (bool-val (boolean boolean?)))

(define expval->num  (lambda (v) (cases expval v (num-val (n) n) (else (error …)))))
(define expval->bool (lambda (v) (cases expval v (bool-val (b) b) (else (error …)))))
```

- **Constructors** `num-val` / `bool-val` wrap a raw Scheme value into an `expval`.
- **Extractors** `expval->num` / `expval->bool` unwrap it (and error if the type is wrong).
- The interpreter always works through these wrappers, never on raw numbers — that's what keeps the language's
  types checked.

> **Note — the only literal production is `const-exp` (numbers).** Every number in the source enters through
> `(expression (number) const-exp)`, and `value-of` immediately wraps it in `num-val`. So from that point on
> _everything is an ExpVal_ — which is exactly why `diff-exp`/`zero?-exp` receive `num-val`s and must `expval->num`
> them before doing arithmetic.
>
> **Why no `const-bool-exp`?** Because booleans are never _written_ in the source language — there's no `#t`/`true`
> token in the grammar. A `bool-val` only ever _arises_ from a computation (`zero?-exp`) and is only ever _consumed_
> by `if-exp`. Since you can't type a boolean literal, there's nothing for a boolean constant production to parse.

#### 3. `environments.scm` — the environment

`empty-env` / `extend-env` / `apply-env` as in the [Scheme › Environments](#environments) section. `init-env`
seeds a few bindings so test programs have free variables to use
([environments.scm](chapter3/let/environments.scm)):

```scheme
(define init-env                       ; [ i=1, v=5, x=10 ]
  (lambda ()
    (extend-env 'i (num-val 1)
    (extend-env 'v (num-val 5)
    (extend-env 'x (num-val 10)
    (empty-env))))))
```

#### 4. `interp.scm` — `value-of`

`value-of` is one big `cases` over `expression`, and **every production name has a matching branch**, with field
names lined up to the data-bearing parts (same count, same order) ([interp.scm](chapter3/let/interp.scm)):

```scheme
(define value-of
  (lambda (exp env)
    (cases expression exp
      (const-exp (num) (num-val num))                       ; grammar: (number) → 1 field
      (var-exp (var) (apply-env env var))                   ; grammar: (identifier) → 1 field
      (diff-exp (exp1 exp2)                                  ; grammar: 2 expressions → 2 fields
        (let ((val1 (value-of exp1 env))
              (val2 (value-of exp2 env)))
          (num-val (- (expval->num val1) (expval->num val2)))))
      (zero?-exp (exp1)
        (if (zero? (expval->num (value-of exp1 env))) (bool-val #t) (bool-val #f)))
      (if-exp (exp1 exp2 exp3)                               ; 3 expressions → 3 fields
        (if (expval->bool (value-of exp1 env))
            (value-of exp2 env)
            (value-of exp3 env)))
      (let-exp (var exp1 body)                               ; identifier + 2 expressions → 3 fields
        (value-of body (extend-env var (value-of exp1 env) env))))))
```

##### What you can use from the grammar in a branch

A `cases` branch consumes _exactly_ what its production declared — nothing more is available:

- **The branch name** must be the production's constructor (its 3rd element): `const-exp`, `diff-exp`, `let-exp`, …
  SLLGen made one `expression` variant per production. A name that isn't a variant is an error; a variant with no
  branch means that expression has no evaluation rule (run-time "missing variant").
- **The branch variables** are **named here, by you** — the grammar left the RHS items unnamed, so this is where they
  get names. They bind left to right to the production's _data-bearing_ parts only (the literal strings are skipped),
  so `(let-exp (var exp1 body) …)` and `(let-exp (name rhs body) …)` are equally valid — only the **order and count**
  matter. The **kind** of each, however, is fixed by what the grammar wrote there:

| grammar part in the RHS | what the bound variable holds        | what you do with it                               |
| ----------------------- | ------------------------------------ | ------------------------------------------------- |
| `number`                | a Scheme number                      | use directly; wrap with `num-val`                 |
| `identifier`            | a Scheme symbol                      | `apply-env` it, or pass to `extend-env`           |
| `expression`            | a **sub-AST node** (not a value yet) | **recurse**: `(value-of it env)` to get its value |

Lining up the `let-exp` production with its branch makes the correspondence exact:

```
grammar:  (expression ("let" identifier "=" expression "in" expression) let-exp)
                             └─ var ─┘      └─ exp1 ─┘      └─ body ─┘
branch:   (let-exp (var exp1 body) …)
```

- `var` is the **symbol** `x` — handed to `extend-env`.
- `exp1` and `body` are **sub-expressions** (ASTs), _not_ values — you must `value-of` them. `exp1` is evaluated to
  get the bound value; `body` is evaluated in the extended env.

So per node you get a fixed branch name and a fixed set of fields whose kinds (number / symbol / sub-expression)
tell you whether to use them as-is or recurse with `value-of`. That's the whole contract between grammar and interpreter.

`value-of-program` just kicks it off in the initial env:

```scheme
(define value-of-program
  (lambda (pgm)
    (cases program pgm
      (a-program (exp1) (value-of exp1 (init-env))))))
```

Two recurring moves:

- **`(value-of sub-exp env)`** — to use a sub-expression's value, evaluate it first; this is the recursion.
- **`let-exp`** evaluates the bound expression, then evaluates the body in an env _extended_ with that binding.

#### 5. `top.scm` — running it

The top module loads all the pieces and wires the pipeline into one entry point
([top.scm](chapter3/let/top.scm)):

```scheme
(define run                                  ; String -> ExpVal
  (lambda (string)
    (value-of-program (scan&parse string))))  ; parse (lang.scm) then evaluate (interp.scm)

(define run-all                              ; run every case in tests.scm
  (lambda () (run-tests! run equal-answer? test-list)))
```

So `(run "let x = 5 in -(x, 1)")` scans & parses the string into an AST, then `value-of-program` evaluates it to
`(num-val 4)`. That's the whole interpreter, end to end.

##### The big picture — one flow

**Set up once (at load time)** — SLLGen and the `define`s create the machinery:

- `sllgen:make-define-datatypes` (specs working in the background) → defines the `program` and `expression` datatypes.
- `sllgen:make-string-parser` → **`scan&parse`** : `String → program` (an AST).
- `run` : `String → ExpVal`.

**Then, per run:**

```
user: program text (String)
   │  run
   ▼
scan&parse  ──builds──▶  program (AST)
   │  value-of-program  (cases program → pulls out the inner expression)
   ▼
expression (AST)
   │  value-of  (recursively unwraps each node…)
   ▼
ExpVal   ◀── the bottom: num-val / bool-val / …
```

`value-of` keeps unwrapping the `expression` that `scan&parse` built until it bottoms out in an **ExpVal**. And
because **every** branch of `value-of` returns an ExpVal, the function has a single, uniform return type — which is
exactly why every result has to be _wrapped_ (`num-val`, `bool-val`, …): any expression can be a sub-expression of
any other, so they must all speak the same currency.

##### Then why ever _unwrap_ an ExpVal?

It feels backwards to wrap a value and then immediately unwrap it — but the wrap and the unwrap serve different
masters:

- **Wrapping** is for `value-of`'s _caller_: a uniform `ExpVal` so results compose.
- **Unwrapping** (`expval->num`, `expval->bool`) is for Scheme's _primitives_: when a branch actually has to **compute**,
  it needs the raw Scheme value inside. Scheme's `-` subtracts numbers, not `(num-val 5)` objects; `if` branches on
  `#t`/`#f`, not `(bool-val #t)`.

So inside a branch the dance is **unwrap → compute → re-wrap**:

```scheme
(diff-exp (e1 e2)
  (num-val                                  ; 3. re-wrap so value-of still returns an ExpVal
    (- (expval->num (value-of e1 env))      ; 1. unwrap each sub-result to a raw number
       (expval->num (value-of e2 env)))))   ; 2. compute with Scheme's real `-`
```

Bonus: unwrapping is also a **dynamic type check** — `expval->num` errors if it's handed a `bool-val`, which is how
the language catches `-(1, zero?(0))` at run time. You wrap to stay uniform, and unwrap exactly when you must touch
the underlying value.

##### Who builds, who unwraps — and how often

There are **two** things being built and unwrapped, on very different schedules:

| layer                                   | built by                                  | unwrapped by                               | how often                                                     |
| --------------------------------------- | ----------------------------------------- | ------------------------------------------ | ------------------------------------------------------------- |
| **AST node** (`diff-exp`, `let-exp`, …) | `scan&parse` (the parser)                 | `value-of`, via `cases`                    | **once each** — the tree is built once, then walked once      |
| **ExpVal** (`num-val`, `bool-val`, …)   | constructors _inside_ `value-of` branches | extractors (`expval->num`, `expval->bool`) | **constantly** — wrapped and unwrapped in nearly every branch |

- The **AST is build-once / unwrap-once**: `scan&parse` constructs each node a single time, and `value-of` destructures
  (unwraps) each node a single time as it walks down.
- The **ExpVal churns**: every computing branch unwraps its sub-results to raw Scheme values, computes, and re-wraps —
  so ExpVals are built and unwrapped over and over throughout one evaluation.

In one line: **`scan&parse` builds the AST; `value-of` (driven by `run`) unwraps the AST once per node, and builds &
unwraps ExpVals all the time, in every branch.**

### PROC

**Where we are:** LET can compute with numbers and booleans and bind them to names — but a *function* is not yet
a value. You can't hand one to another function or return one. **PROC adds exactly that:** procedures become
first-class expressed values. **The one new idea is the _closure_** — a procedure has to remember the
environment it was *defined* in, so its free variables still resolve correctly when it's eventually called
somewhere else. Everything else carries over from LET unchanged; what follows is only the delta. Source:
[proc-ds](chapter3/proc-ds/) (and [proc-rep](chapter3/proc-rep/)).

**Example**

```text
let f = proc (x) -(x, 1) in (f 30)       % bind a procedure, then call it   => 29
((proc (x) proc (y) -(x, y)  5) 6)       % curried 2-arg proc, applied      => -1
```

**Grammar** — two new productions:

```scheme
(expression ("proc" "(" identifier ")" expression) proc-exp)   ; proc (x) body   — define
(expression ("(" expression expression ")")        call-exp)   ; (rator rand)    — call
```

**Values** — a procedure is a new kind of expressed value, so `expval` gains a `proc-val` variant, and there's a
new `proc` datatype for the closure itself:

```scheme
(define-datatype expval expval?
  (num-val  (value number?))
  (bool-val (boolean boolean?))
  (proc-val (proc proc?)))                       ; NEW

(define-datatype proc proc?
  (procedure (var symbol?) (body expression?) (env environment?)))  ; closure = param + body + captured env

(define expval->proc (lambda (v) (cases expval v (proc-val (p) p) (else (error …)))))  ; NEW extractor
```

**`value-of`** — two new branches, plus a helper `apply-procedure`:

```scheme
(proc-exp (var body)
  (proc-val (procedure var body env)))           ; capture the *current* env → a closure

(call-exp (rator rand)
  (let ((proc (expval->proc (value-of rator env)))
        (arg  (value-of rand env)))
    (apply-procedure proc arg)))

(define apply-procedure
  (lambda (proc1 val)
    (cases proc proc1
      (procedure (var body saved-env)
        (value-of body (extend-env var val saved-env))))))   ; run body in the captured env + the arg
```

Key ideas this introduces:

- **Closure** = code + the env it was _defined_ in. `proc-exp` captures `env`; `apply-procedure` runs the body in
  that `saved-env`, not the caller's.
- **Lexical scoping** — free variables resolve in the definition env (the captured one). (Dynamic scoping would use
  the caller's env instead; EOPL uses lexical.)
- **Currying** — only one parameter per `proc`, so multi-arg functions are nested: `proc(a) proc(b) …`, called `((f a) b)`.

### LETREC

**Where we are:** PROC's closure captures the environment as it stands at definition time — but at that instant
the function isn't bound to its own name yet, so it can't call *itself*. **LETREC fixes exactly this one gap:** a
function's own name must be visible inside its own body. **The new idea is to tie the knot lazily** — rebuild the
closure each time the name is looked up, always over the same recursive environment, so it can find itself.
Source: [letrec](chapter3/letrec/).

**Example**

```text
letrec f(x) = if zero?(x) then 0 else -((f -(x,1)), -2)
in (f 4)                                 % recursion: f adds 2, x times      => 8
```

**Grammar** — one new production (name, parameter, body, and the expression to run):

```scheme
(expression ("letrec" identifier "(" identifier ")" "=" expression "in" expression) letrec-exp)
```

**Environment** — gains a new variant so the env can describe a recursive binding without a circular literal.
`apply-env` builds the closure **on demand** when the name is looked up (this is the trick — _JIT binding_):

```scheme
;; in apply-env, when the env node is an extend-env-rec:
(extend-env-rec (p-name b-var p-body saved-env)
  (if (eqv? search-sym p-name)
      (proc-val (procedure b-var p-body env))   ; build closure over the SAME rec env → self-reference
      (apply-env saved-env search-sym)))
```

**`value-of`** — one new branch; it just installs the recursive binding and runs the body:

```scheme
(letrec-exp (p-name b-var p-body letrec-body)
  (value-of letrec-body
    (extend-env-rec p-name b-var p-body env)))
```

Key idea: the procedure's env must contain the procedure itself. Instead of a circular data structure, the closure
is _re-created each time the name is resolved_, always closing over the same recursive env — so it can call itself.

**Recap — what chapter 3 taught (the shape of the whole story so far)**

- One AST variant ↔ one `value-of` (and `cases`) branch.
- A closure is _code + the env it was born in_ — that captured env is the whole point.
- Recursion needs the binding to see itself: build the closure lazily on lookup (LETREC).
- Names matter only until runtime; lexical addressing turns them into indices for speed.

## Chapter 4 — State & References

**Where we are:** everything in chapter 3 was purely functional — evaluating an expression produced a value and
changed nothing, so the same expression always meant the same thing. **Chapter 4 adds mutable state:** the
ability to *change* a value over time. It does this with **one new component, the _store_** — a separate,
mutable array of locations that models memory — and then tells three sub-stories on top of that same store:
references the program manages by hand (**EXPLICIT-REFS**), then those references hidden inside ordinary
variables (**IMPLICIT-REFS**), then a compound mutable data type built from cells (**MUTABLE-PAIRS**). Read them
in that order — each leans on the previous. (The parameter-passing disciplines that also build on the store —
call-by-reference and call-by-need — are in the [Appendix](#appendix--variants--optimizations).)

The store lives in [store.scm](chapter4/explicit-refs/store.scm) and is reused by every chapter-4 language:

```scheme
;; the-store is a global mutable Scheme list; a reference is just an integer index
(define empty-store (lambda () '()))
(define reference?  (lambda (v) (integer? v)))
(define newref      (lambda (val) … append val, return its index))   ; allocate
(define deref       (lambda (ref) (list-ref the-store ref)))         ; read
(define setref!     (lambda (ref val) … rebuild store with val at ref)) ; write
(define initialize-store! (lambda () (set! the-store (empty-store)))) ; reset per run
```

`value-of-program` now calls `(initialize-store!)` before evaluating, so each run starts with empty memory.

### EXPLICIT-REFS

**The first use of the store:** references are exposed directly, and the *program* allocates, reads, and writes
them by hand with `newref` / `deref` / `setref`. A reference is just a new kind of expressed value you can pass
around. This is the store at its most visible — later languages will hide exactly this machinery. Source:
[explicit-refs](chapter4/explicit-refs/).

**Example**

```text
let x = newref(17) in                    % allocate a box holding 17
begin
  setref(x, -(deref(x), 1));             % mutate it: 17 - 1
  deref(x)                               % read it back                     => 16
end
```

**Grammar** — new forms for sequencing and the three store operations:

```scheme
(expression ("begin" expression (arbno ";" expression) "end") begin-exp)  ; sequence side effects
(expression ("newref" "(" expression ")") newref-exp)                     ; allocate
(expression ("deref"  "(" expression ")") deref-exp)                      ; read
(expression ("setref" "(" expression "," expression ")") setref-exp)      ; write
```

**Data structures** — `expval` gains a reference value: `(ref-val (ref reference?))`, plus `expval->ref`.

**`value-of`** — the new forms map straight onto the store interface:

```scheme
(newref-exp (exp1) (ref-val (newref (value-of exp1 env))))
(deref-exp  (exp1) (deref (expval->ref (value-of exp1 env))))
(setref-exp (exp1 exp2)
  (begin (setref! (expval->ref (value-of exp1 env)) (value-of exp2 env))
         (num-val 23)))                ; setref returns a dummy value
```

**Key ideas**

- **The store = memory.** State lives outside both values and the environment, in a global mutable array.
- **References are values** — you can pass them around, store them, return them.
- **`begin`** sequences effects, since now evaluation order is observable.
- **Refernce implementation** — this is usually irrelevant, but know that references are actually indexes into the list of values, each time a value is appended and the new index is returned.

### IMPLICIT-REFS

**Where we are:** EXPLICIT-REFS made the programmer juggle boxes by hand. IMPLICIT-REFS hides them — **the big
shift is that every variable is now itself a reference** into the store. So `newref`/`deref`/`setref` disappear
from the language, replaced by ordinary variables plus a single assignment form, `set`; the allocation and
dereferencing move *into* the variable semantics. Source: [implicit-refs](chapter4/implicit-refs/).

**Example** — no `newref`/`deref`; a plain variable is already mutable:

```text
let x = 0 in
begin
  set x = 4;                             % assign
  set x = -(x, 1);                       % read + assign
  x                                                                          => 3
end
```

**Grammar** — the three explicit ops are _gone_; one assignment form replaces them:

```scheme
(expression ("set" identifier "=" expression) assign-exp)   ; mutate a variable
```

**Data structures** — the environment now binds each name to a **location**, not a value:
denoted value = _reference_, expressed value = _value_. (The `extend-env` field changes from `expval?` to
`reference?`.)

**`value-of`** — allocation and dereferencing become automatic:

```scheme
(var-exp (var) (deref (apply-env env var)))                 ; auto-deref on every use
(let-exp (var exp1 body)
  (value-of body (extend-env var (newref (value-of exp1 env)) env)))  ; let allocates a location
;; apply-procedure likewise does (newref arg) — a fresh location per call → call-by-value
(assign-exp (var exp1)
  (begin (setref! (apply-env env var) (value-of exp1 env)) (num-val 27)))
```

**L-value vs. R-value** — the same variable means two things depending on position:

- **R-value** (a _read_, e.g. `x` in `-(x,1)`) — look the name up, then auto-`deref` to get its value.
- **L-value** (a _write_, e.g. `x` in `set x = 10`) — look the name up to get its **location**, then `setref!`
  straight into it.

**Recursion here uses `extend-env-rec*`** — because the env maps names directly to store locations, the recursive
binder builds closures dynamically and stores them _in the store_ via `newref`. ⚠️ A consequence: IMPLICIT-REFS
supports **recursive functions only, not recursive data** structures.

> ⚠️ **Gotcha — the `procedure` constructor lives in _two_ files.** Closures are built in `interp.scm`
> (`proc-exp`) **and** in [`environments.scm`](chapter4/implicit-refs/environments.scm) — `extend-env-rec*`
> manufactures a fresh `procedure` for each letrec name on lookup. So if you ever **change the `procedure`
> datatype** (add a field — a guard, a static-var list, a self-name…), you must update **both** call sites or the
> letrec one will fail with a "`procedure` expects N arguments, given N-1" arity error. Same applies to any datatype
> whose constructor is invoked outside `interp.scm`.

**Key ideas**

- **Denoted = location, expressed = value.** A variable _names a box_; reading it dereferences, `set` writes it.
- **Call-by-value via fresh locations** — each `let`/argument gets its own `newref`, so assignments don't leak.
- `set x = e` is the explicit `newref`/`deref`/`setref` machinery, hidden inside the variable semantics.

### MUTABLE-PAIRS

**Where we are:** so far the store has held single values. MUTABLE-PAIRS shows the same store can back **compound
mutable data** — a pair whose two halves live in store cells, so they can be updated in place and shared between
places. The point is that pairs aren't primitive: they're built out of the store you already have. Source:
[mutable-pairs](chapter4/mutable-pairs/).

**Example** — note `left(p)`/`right(p)` take parens, but `setleft p = e`/`setright p = e` do not:

```text
let p = newpair(22, 33) in
begin
  setright p = 99;                       % mutate the right half
  -(right(p), left(p))                   % 99 - 22                           => 77
end
```

**Grammar** — make/read/write the two halves:

```scheme
(expression ("newpair" "(" expression "," expression ")") newpair-exp)
(expression ("left"  "(" expression ")") left-exp)
(expression ("right" "(" expression ")") right-exp)
(expression ("setleft"  expression "=" expression) setleft-exp)
(expression ("setright" expression "=" expression) setright-exp)
```

**Data structures** — `expval` gains `(mutpair-val (p mutpair?))`. A `mutpair` is defined behind an **interface**
([pairvals.scm](chapter4/mutable-pairs/pairvals.scm): `make-pair` / `left` / `right` / `setleft` / `setright`)
with **two interchangeable representations**:

- [pairval1.scm](chapter4/mutable-pairs/pairval1.scm) — a datatype holding **two** store refs: `(a-pair (newref v1) (newref v2))`.
- [pairval2.scm](chapter4/mutable-pairs/pairval2.scm) — **one** ref to the first of two _adjacent_ cells; `right` is `(deref (+ 1 p))`.

**`value-of`** — each form calls the interface, e.g.:

```scheme
(newpair-exp (e1 e2) (mutpair-val (make-pair (value-of e1 env) (value-of e2 env))))
(left-exp (e1) (left (expval->mutpair (value-of e1 env))))
(setleft-exp (e1 e2)
  (begin (setleft (expval->mutpair (value-of e1 env)) (value-of e2 env)) (num-val 82)))
```

**Key ideas**

- **Compound mutable data** is built from store cells — pairs aren't primitive.
- **Interface vs. representation** — one API, two implementations you can swap without touching `interp.scm`.
- **Sharing/aliasing** — handing the same `mutpair-val` to two places means both see mutations.

## Chapter 7 — Types

**Where we are:** until now a bad program like `-(1, zero?(0))` was only caught *while running*, when an
extractor was handed the wrong kind of value (recall [why ever unwrap](#then-why-ever-unwrap-an-expval)).
**Chapter 7 catches those errors before evaluation even starts**, with a **static type system**: a pass that
walks the AST up front and rejects ill-typed programs. The elegant part is that it **mirrors the interpreter** —
where `value-of : Exp × Env → Value`, the type pass is `type-of : Exp × Tenv → Type`: the same traversal, the
same kind of environment, computing types instead of values. Two versions follow: **CHECKED** makes you write
the type annotations; **INFERRED** works them out for you.

### CHECKED

Statically type-checks a PROC/LETREC language; the programmer writes type annotations. Source:
[checked](chapter7/checked/).

**Example** — types are written explicitly; the checker computes the program's type or rejects it:

```text
letrec int f(x : int) = if zero?(x) then 0 else -((f -(x,1)), -2)
in (f 4)                                 % type-checks  : int

proc (f : (int -> bool)) (f 3)           % : ((int -> bool) -> bool)

if zero?(0) then 1 else zero?(1)         % REJECTED: branches are int vs bool
```

**Grammar** — annotations on binders, plus a new `type` nonterminal:

```scheme
(expression ("proc" "(" identifier ":" type ")" expression) proc-exp)        ; annotated parameter
(expression ("letrec" type identifier "(" identifier ":" type ")" "=" expression
             "in" expression) letrec-exp)                                     ; result + param types
(type ("int") int-type)
(type ("bool") bool-type)
(type ("(" type "->" type ")") proc-type)                                     ; function type
```

**Data structures** — `expval` is unchanged (types are erased at run time); a `type` datatype is generated from
the `type` productions.

**Checker** ([checker.scm](chapter7/checked/checker.scm)) — `type-of` is structured exactly like `value-of`,
over a **type environment** (`tenv`, names → types), using `check-equal-type!` to enforce constraints:

```scheme
(diff-exp (e1 e2)
  (check-equal-type! (type-of e1 tenv) (int-type) e1)
  (check-equal-type! (type-of e2 tenv) (int-type) e2)
  (int-type))
(if-exp (e1 e2 e3)
  (check-equal-type! (type-of e1 tenv) (bool-type) e1)        ; condition must be bool
  (let ((t2 (type-of e2 tenv)) (t3 (type-of e3 tenv)))
    (check-equal-type! t2 t3 exp) t2))                        ; branches must agree
(proc-exp (var var-type body)
  (proc-type var-type (type-of body (extend-tenv var var-type tenv))))
;; check-equal-type! errors via report-unequal-types when (equal? ty1 ty2) is false
```

**Key ideas**

- **Static vs. dynamic** — type errors are caught _before_ running, by structure, not by hitting a bad value.
- **`type-of` mirrors `value-of`** — same AST traversal, same kind of environment (`tenv` instead of `env`).
- **Annotations required** — every parameter and `letrec` carries a `: type`; the checker only _verifies_, it
  doesn't guess.

### INFERRED

Same idea as CHECKED, but the types are **inferred** by unification (Hindley–Milner style) — annotations become
optional, written `?`. Source: [inferred](chapter7/inferred/).

**Example** — write `?` for any type and let unification solve it:

```text
proc (x : ?) -(x, 1)                     % inferred: (int -> int)

let f = proc (x : ?) -(x, 1) in (f 4)    % inferred: int

letrec ? f (x : ?) = (f f) in 33         % REJECTED: occurs-check (infinite type)
```

**Grammar** — annotations become _optional_, and types may contain **type variables**:

```scheme
(optional-type ("?") no-type)          ; leave it to the inferrer
(optional-type (type) a-type)          ; or give a concrete type
(type ("%tvar-type" number) tvar-type) ; an internal type variable
;; proc/letrec now use optional-type wherever CHECKED used type
```

**Data structures** — the `type` datatype gains `tvar-type` (a type variable). Two new modules:

- [substitutions.scm](chapter7/inferred/substitutions.scm) — a **substitution** maps type variables → types;
  `apply-subst-to-type` resolves a type against it, `extend-subst` adds a binding.
- [unifier.scm](chapter7/inferred/unifier.scm) — `unifier` makes two types equal by binding type variables
  (with an _occurs check_ to reject infinite types like `t = (t -> int)`), returning an extended substitution.

**Inferrer** ([inferrer.scm](chapter7/inferred/inferrer.scm)) — `type-of` returns an **answer** = a
`(type, substitution)` pair, threading the substitution and calling `unifier` to record constraints:

```scheme
(zero?-exp (e1)
  (cases answer (type-of e1 tenv subst)
    (an-answer (t1 subst1)
      (an-answer (bool-type) (unifier t1 (int-type) subst1 exp)))))   ; constrain arg = int
(proc-exp (var otype body)
  (let ((arg-type (otype->type otype)))         ; ?  → a fresh tvar;  a type → itself
    (cases answer (type-of body (extend-tenv var arg-type tenv) subst)
      (an-answer (res subst) (an-answer (proc-type arg-type res) subst)))))
```

**Key ideas**

- **Inference vs. checking** — instead of demanding annotations, generate **fresh type variables** for unknowns and
  _solve_ for them.
- **Unification** is the engine: each expression contributes equations between types; `unifier` solves them, binding
  variables in a growing **substitution**.
- **Answers thread a substitution** — every `type-of` step carries the accumulated constraints forward; the final
  type is read off by applying the substitution.

# Preparing for the exam

The exam is reference-limited (**course book + study guide only**) and has three questions in two
flavours — feature development and type systems:

- Questions that deal with implementing changes in different languages ​​and a question about type systems.
- The permitted reference material: Course book + study guide only
- Question 1 - Chapter 3 - LET or PROC
- Question 2 - Chapter 4 - IMPLICIT-REFS or EXPLICIT-REFS (note: EXPLICIT-REFS has rarely ever appeared).
- Question 3 - Chapter 7 - Algorithm for type-checking a program
- Resources for practicing for the exam:
  - Sample exercises in the study guide, including full solutions on the course website.
  - Exercises in the body of the book. From simple to complex level exercises (marked with asterisks).
  - Past tests

## Part 1 — Features Development (questions 1 & 2)

Questions 1 and 2 ask you to _implement a change_ to a language: Q1 over Chapter 3 (LET / PROC) and
Q2 over Chapter 4 (EXPLICIT-REFS / IMPLICIT-REFS). The [Important](#important) section below is the
toolkit, in working order: a **feature overview**, then **writing the grammar**, then **writing the
interpreter** (with the full branch SDK). Worked feature diffs are catalogued in [features.md](features.md).

### Important

The core you must be fluent in for Q1–Q2, in the order you actually work: understand the new
construct, write its **grammar**, then write its **interpreter**.

#### 1. Feature overview

Q1 extends a Chapter-3 language (LET / PROC), Q2 a Chapter-4 one (EXPLICIT-REFS / IMPLICIT-REFS). A
feature is a **delta across files, usually these**:

- **`lang.scm`** — a grammar production (rarely a lexer rule); SLLGen auto-generates the matching `*-exp` AST node.
- **`interp.scm`** — a `cases` branch in `value-of` for that node.
- **`data-structures.scm`** — a new `expval` variant **only if** the feature introduces a new _kind_ of value
  (a list, a closure with extra state, …); otherwise reuse `num-val`/`bool-val`.
  - Note: if the new expval has multiple members, it usually helps to define a new datatype as well.

Every branch has the same shape — **unwrap → compute → re-wrap**: `value-of` each sub-expression,
`expval->…` it to a raw Scheme value, compute in Scheme, then wrap the result back in `num-val`/`bool-val`/…
so the branch returns an `ExpVal`. (A field that's already a raw `symbol`/`number` — like `var` in `let-exp` —
is used as-is.)

**The whole drill — `pair(e1, e2)` and `fst(p)`** (this one introduces a new `expval`):

1. **`data-structures.scm`** — add the new `expval` variant and its extractor (a 2-member value, so it earns its own fields).
2. **`lang.scm`** — add the grammar production(s); `"pair"`/`"fst"` are just literals, so no lexer change.
3. **`interp.scm`** — add the matching `cases` branch(es), following unwrap → compute → re-wrap.

```scheme
;; data-structures.scm
(define-datatype expval expval?
    ...
    (pair-val (l expval?) (r expval?))
)

(define expval->pair (lambda (v)
  (cases expval v
    (pair-val (l r) (list l r))
    (else (expval-extractor-error 'pair v))
  )
))

;; lang.scm
(define the-grammar
  ....
  (expression ("pair" "(" expression "," expression ")") pair-exp)
  (expression ("fst"  "(" expression ")")                fst-exp)
)

;; interp.scm
(define value-of
  ...
  (pair-exp (e1 e2) (pair-val (value-of e1 env) (value-of e2 env)))
  (fst-exp  (e)     (car (expval->pair (value-of e env))))
)
```

Then **test** — `(run "fst(pair(3, 4))")` ⇒ `(num-val 3)`. A feature that reuses `num-val`/`bool-val` (e.g.
`add(e1, e2)` returning a sum) just skips step 1. Worked diffs for every construct: [features.md](features.md).

##### Book/guide page references:

| Language                  | Book pages | Guide pages   |
| ------------------------- | ---------- | ------------- |
| LET                       | 69         | 105           |
| PROC (data-structure rep) | 79         | 114           |
| EXPLICIT-REFS             | 111        | 148           |
| IMPLICIT-REFS             | 118        | 152 (partial) |

#### 2. Writing the grammar (`lang.scm`)

Read the production carefully — separate **terminals** (literal strings / keywords) from **non-terminals**
(`expression`, or a category you define), and spot which pieces carry data. **Count the data-bearing parts** —
that is exactly the field count your `cases` branch will take (literals are dropped). A new **keyword** is just a
literal string (no lexer change); only a genuinely new **token kind** (e.g. string literals) needs a lexical rule.

**Repetition → list fields.** `(arbno X)` ("zero or more") and `(separated-list X ",")` turn that piece into a
**single field that is a Scheme list**:

```scheme
(expression ("begin" expression (arbno ";" expression) "end") begin-exp)
;; node (begin-exp exp1 exps): exp1 : Exp, exps : list of Exp
```

- **Multiple symbols → parallel, index-aligned lists**: `(arbno identifier "=" expression)` yields `vars` and
  `exps` (a multi-binding `let`). `separated-list` behaves the same.
- Such a field is **always a list** — even for zero or one element — so handle `'()` (`null?`); never assume a single value.
- A `separated-list`'s **last argument is the separator and must be a terminal** (a string).

**Need ≥ 1 (`{X}+`)?** SLLGen has no one-or-more operator. Prefer **mandatory-first + `arbno`-rest** —
`X (arbno X)` (or `X (arbno "," X)`): the parser rejects zero outright, and the count is `(+ (length rest) 1)`.
This is often not optional: SLLGen builds an LL(1) parser, so a production that _starts_ with a nullable `arbno`
has no token to commit on and can collide with another rule (`grammar not LL(1): shift conflict`); a leading
literal fixes it. When you must use `(separated-list X ",")` (which matches empty), enforce ≥1 in the branch with
a `null?` guard. (To _count_ a repeated bare literal like `"&"`, make it a non-terminal — `(amp ("&") an-amp)` —
since literals capture nothing.)

**Your own non-terminals.** A feature can add a whole category, not just `expression` productions:

```scheme
(type-name ("number") type-name-number)                     ; field-less keyword variants (switch)
(option () option-empty)  (option ("const") option-const)   ; an empty alternative ⇒ optional syntax (const)
```

SLLGen generates a `type-name` / `option` datatype you `cases` on. An empty alternative makes a keyword
**optional**; a set of keyword variants makes a small tag category (used by `switch`, `const`, `guard`). To match
a _syntactic_ type tag against a _runtime_ value, map **both** through their own `cases` into one shared symbol
alphabet, then `eqv?` (see the `switch`/reflection patterns below).

**Lexer tweaks** are rare — e.g. admit a leading `_` in the `identifier` rule for a wildcard:

```scheme
(identifier ((or letter "_") (arbno (or letter digit "_" "-" "?"))) symbol)   ; tuples: let [x, _] = <10,20>
```

#### 3. Writing the interpreter (`interp.scm`) + the SDK

Add the `cases` branch and follow **unwrap → compute → re-wrap**. `(value-of exp env)` always returns a
**wrapped `ExpVal`** — `expval->…` it before Scheme can operate on it. The extractor doubles as a runtime type
check: `expval->num` errors on a `bool-val`, which is how `-(1, zero?(0))` is rejected. (Full discussion:
[why ever unwrap an ExpVal](#then-why-ever-unwrap-an-expval).)

```scheme
;; ❌ (- (value-of e1 env) (value-of e2 env))          ; can't subtract ExpVal records
;; ✅ (num-val (- (expval->num (value-of e1 env))      ; unwrap, compute, re-wrap
                  (expval->num (value-of e2 env))))
```

##### The branch SDK — everything callable inside a branch

**1 · Your inputs** — what's in scope: the **field variables** `f1 f2 …` from the `cases` pattern (sub-`Exp`s,
symbols, or numbers per the grammar — see [what you can use from the grammar](#what-you-can-use-from-the-grammar-in-a-branch));
**`env : Env`**; and the store (ch. 4+), a global reached through the store API below.

**2 · Recursion** — turn a sub-`Exp` into a value:

| call                 | type                 | use                                        |
| -------------------- | -------------------- | ------------------------------------------ |
| `(value-of exp env)` | `Exp × Env → ExpVal` | evaluate a sub-expression — your main move |

**3 · Constructors** (build the result; `data-structures.scm`):

| constructor    | wraps              | available in   |
| -------------- | ------------------ | -------------- |
| `(num-val n)`  | a Scheme number    | all            |
| `(bool-val b)` | a Scheme boolean   | all            |
| `(proc-val p)` | a `proc` (closure) | PROC+          |
| `(ref-val r)`  | a store reference  | EXPLICIT-REFS+ |

**4 · Extractors** (unwrap an operand; error on type mismatch) — the inverse:

| extractor          | `ExpVal →`     |
| ------------------ | -------------- |
| `(expval->num v)`  | Scheme number  |
| `(expval->bool v)` | Scheme boolean |
| `(expval->proc v)` | a `proc`       |
| `(expval->ref v)`  | a `Ref`        |

**5 · Environment** (`environments.scm`):

| call                                   | type                                              | use                                                       |
| -------------------------------------- | ------------------------------------------------- | --------------------------------------------------------- |
| `(apply-env env var)`                  | `Env × Sym → ExpVal` (or `Ref` in IMPLICIT-REFS+) | look a variable up                                        |
| `(extend-env var val env)`             | `Sym × ExpVal × Env → Env`                        | bind one name                                             |
| `(extend-env-rec name b-var body env)` | `… → Env`                                         | (LETREC) recursive binding                                |
| `(extend-env-rec* … )`                 | `… → Env`                                         | (IMPLICIT-REFS) recursive binding via the store           |
| `(empty-env)` / `(init-env)`           | `→ Env`                                           | base / preloaded env (usually only in `value-of-program`) |

**6 · Procedures** (PROC+):

| call                       | type                     | use                                 |
| -------------------------- | ------------------------ | ----------------------------------- |
| `(procedure var body env)` | `Sym × Exp × Env → proc` | **build** a closure (capture `env`) |
| `(apply-procedure p arg)`  | `proc × ExpVal → ExpVal` | **call** a closure                  |

**7 · Store** (chapter 4+; `store.scm`) — cells hold **`ExpVal`s**, so wrap on write / unwrap on read:

| call                  | type               | use                                                          |
| --------------------- | ------------------ | ------------------------------------------------------------ |
| `(newref val)`        | `ExpVal → Ref`     | allocate a cell — `(newref (num-val 5))`                     |
| `(deref ref)`         | `Ref → ExpVal`     | read a cell — `(expval->num (deref r))`                      |
| `(setref! ref val)`   | `Ref × ExpVal → ⊥` | overwrite a cell (returns a dummy)                           |
| `(initialize-store!)` | `→`                | reset memory — called by `value-of-program`, not in branches |

Specialised: `make-pair`/`left`/`right`/`setleft`/`setright` (MUTABLE-PAIRS); `a-thunk` + `value-of-thunk` (CALL-BY-NEED).

**8 · Errors & dispatch:** `(eopl:error 'who "msg ~s" arg)` raises a runtime error (extractors call this on
mismatch). `(cases <type> v …)` destructures any datatype — not just the AST: `cases proc` inside
`apply-procedure`, `cases expval` inside an extractor.

**9 · Scheme you'll lean on** (the interpreter is written in Scheme; full reference in the [Scheme chapter](#scheme)):
`let`/`let*` to name unwrapped operands; `if`/`cond`; arithmetic/comparison (`+ - * /`, `= < >`, `zero?`) wrapped
back into `num-val`/`bool-val`; `cons`/`car`/`cdr`/`null?`/`map`/`length`/`list-ref` for list-valued fields;
`eqv?`/`equal?` to compare symbols; `lambda`; and `letrec` for a local recursive helper over a list field:

```scheme
(begin-exp (exp1 exps)                       ; consume an (arbno …) list: return the last value
  (letrec ((vob (lambda (e es)
                  (let ((v (value-of e env)))
                    (if (null? es) v (vob (car es) (cdr es)))))))
    (vob exp1 exps)))
```

To **aggregate** a list field to one value, `foldl`/`foldr` (unwrap each, re-wrap once):
`(num-val (foldl (lambda (e acc) (+ (expval->num (value-of e env)) acc)) 0 exps))`. ⚠️ Argument order differs by
dialect: Racket `foldl`/`foldr` pass `(element acc)`, R6RS/EOPL `fold-left` passes `(acc element)`. For a plain
sum of raw numbers, `(apply + lst)`.

##### Types & where they're defined

Who defines each type the interpreters use — **Scheme** primitive, the **EOPL library**, **SLLGen** (from the
grammar), or one of **your** files.

| type / datatype                                                                     | defined by                      | where (file · line)                                                                                                                        |
| ----------------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `number`, `boolean`, `string`, `symbol`, pair/list + their `?` predicates           | **Scheme** (runtime primitives) | — built into Racket                                                                                                                        |
| `define-datatype`, `cases`, `eopl:error`, `eopl:printf`                             | **EOPL library**                | `(lib "eopl.ss" "eopl")`                                                                                                                   |
| `program`, `expression` (+ every `*-exp` variant), the `type`/`type-name` datatypes | **SLLGen**, from the grammar    | generated by `sllgen:make-define-datatypes` ← [`lang.scm` `the-grammar`](chapter3/let/lang.scm#L23)                                        |
| `expval` (`num-val`, `bool-val`, `proc-val`, `ref-val`, …) + extractors             | your file                       | [`data-structures.scm:11`](chapter3/let/data-structures.scm#L11) (variants added per language)                                             |
| `proc` (closure: `procedure`)                                                       | your file                       | [`data-structures.scm:53`](chapter3/proc-ds/data-structures.scm#L53) (PROC+)                                                               |
| `environment` (`empty-env` / `extend-env` / `extend-env-rec`)                       | your file                       | [`data-structures.scm:44`](chapter3/let/data-structures.scm#L44); a `define-datatype` from LETREC on                                       |
| `reference` (= an integer index) + `the-store`                                      | your file                       | [`store.scm:39`](chapter4/explicit-refs/store.scm#L39) (ch. 4+)                                                                            |
| `mutpair` · `thunk` (`a-thunk`)                                                     | your file                       | [`pairval1.scm:13`](chapter4/mutable-pairs/pairval1.scm#L13) · [`data-structures.scm:121`](chapter4/call-by-need/data-structures.scm#L121) |

Rules of thumb: a **`*-exp`** node or the `type` datatype → **SLLGen** made it (never `define-datatype` those); a
**value** the interpreter computes (`expval`, `proc`, `thunk`, `mutpair`) → **you** wrote it in `data-structures.scm`;
plumbing (`environment`, `reference`, `substitution`, …) → **you**, in the matching support file; any `?` predicate
you didn't define (`number?`, `symbol?`, `null?`) → **Scheme**.

##### Recurring patterns

- **Marker value (wrap-on-bind, strip-on-read).** Tag a stored value with a wrapper variant; unwrap it at
  `var-exp` so the rest of the interpreter never sees the tag (but `set` still can):
  `(var-exp (var) (strip-const (deref (apply-env env var))))`.
  [const](features.md#implicit-refs--const), [guard](features.md#implicit-refs--guard).
- **Optional syntax** via a nullable non-terminal (`option-empty`), then `cases` on which variant you got.
  [const](features.md#implicit-refs--const), [guard](features.md#implicit-refs--guard).
- **Runtime type reflection.** One helper maps any `ExpVal` to a type symbol; expose it as ops or dispatch on it:
  `(define expval-type-of (lambda (v) (cases expval v (num-val (n) 'num) (bool-val (b) 'bool) (proc-val (p) 'proc))))`.
  [type](features.md#proc-ds--type), [switch](features.md#implicit-refs--switch).
- **Overloading.** `proc-val` carries a _list_ of procs; `apply-procedure` runs the first whose param type matches
  the argument's runtime type. [overload-proc](features.md#implicit-refs--overload-proc).
- **Persistent state.** Give a value a `reference?` field and `setref!` it to keep a cursor/counter across uses.
  [generator](features.md#implicit-refs--generator).
- **Dynamic binding.** Thread the call-site `env` into `apply-procedure` and use it instead of the closure's
  `saved-env`. [dynamic-binding](features.md#proc-ds--dynamic-binding).
- **Lazy / deferred evaluation (4 moves).** A constructor **defers** (returns an `unevaluated-val` holding the
  unrun pieces **and the env**); an `evaluate` helper turns a deferred value into a real one (else passes through);
  an `evaluate-ref` helper forces the value behind a store ref and `setref!`s it back (memoize once); the
  **consumer** (not `var-exp`) forces — special-casing a `var-exp` operand so it can grab the ref with `apply-env`
  and write the forced value back. [letlazy](features.md#implicit-refs--letlazy), [map](features.md#implicit-refs--map).
- **Inspect an operand's AST shape** with `cases expression` instead of evaluating it — when behavior depends on
  _what kind_ of expression an operand is (e.g. "is it a bare variable?"):
  `(cases expression e1 (var-exp (v) <use (apply-env env v)>) (else <(value-of e1 env)>))`.
- **Loop / accumulate over a list.** Walk a list field, optionally filtering (by type) or skipping/breaking on a
  guard, building a sum or a new `list-val`. [fold](features.md#proc-ds--fold),
  [forsum](features.md#2024b98--proc-ds--forsum), [foreach](features.md#2025c93--proc-ds--foreach),
  [do](features.md#2023b99--let--do), [forproc](features.md#2024b84--implicit-refs--forproc).
- **Statement (no useful value).** A construct whose result is irrelevant returns a fixed dummy
  (`(num-val 27)`, `901`/`902`); observe its effect through mutation.
  [event](features.md#2025c93--implicit-refs--event), [forproc](features.md#2024b84--implicit-refs--forproc).
- **Aggregate value + access.** Build a `list-val`/`tuple-val` from a `(separated-list …)`, then consume it by
  index or positional destructuring (`_` skips). [map](features.md#2025b84--implicit-refs--map),
  [tuples](features.md#2021b57--proc-ds--tuples), [arr](features.md#2021b78--explicit-refs--arr).
- **Variable-arity proc/call.** Params and args are lists; bind/dispatch by **count** (`extend-env*`, with a
  length check). [overload-count](features.md#proc-ds--overload-count).

## Right before the test

### Insightful exercises to view

Each teaches an unique technique — worth a final read:

- **[tuples](features.md#2021b57--proc-ds--tuples)** — destructuring `let [a, _, c] = <e1,e2,e3>`: adds a
  `tuple-val`, a _second_ `let`-target form, and `_`-skip via a lexer tweak — one keyword (`let`) parsing two
  different shapes.
- **[generator](features.md#2021b87--implicit-refs--generator)** — a value that carries a store `reference?`
  (its cursor) _inside_ the `expval`, so `::g` advances persistent state across calls and `??g` tests exhaustion.
- **[const](features.md#2023b84--implicit-refs--const)** — wrap-on-bind / strip-on-read marker value: reads see
  through the `const-val` tag but `set` on it errors; `(f const v)` re-wraps the argument as const before handing
  it to `apply-procedure`.
- **[enum](features.md#2024b84--proc-ds--enum)** — multiple enum definitions plus a `match` that must be
  **exhaustive**: you actually check every enum symbol is covered (a real semantic check, not just dispatch).
- **[exception](features.md#2023b84--let--exception)** — `try`/`catch`/`finally`/`throw` with **no host-language
  `raise`**: exceptions are `excp-val` values that every branch must check-and-propagate, so it touches almost the
  whole interpreter.
- **[overload-proc](features.md#2025b91--implicit-refs--overload-proc)** — dispatch by argument type needs a richer
  `proc-val` (one slot per type) plus an `empty-proc` sentinel to initialize the unfilled slots; calling an empty
  slot errors.
- **[multiptr](features.md#2024b98--implicit-refs--multiptr)** — multi-level pointers (`&&&x` / `***p`): the
  value-and-deref design is non-trivial, and the **number of `&`/`*` is counted off the grammar** (a `{X}+`
  repetition counted via the leading-literal trick).

### Reminders & Gotchas

- List sections you'll change — the trio in the [feature overview](#1-feature-overview).
- **Read your code line-by-line** to verify it's correct — assume you forgot something.
- **Name the type of every variable** as you read — most bugs here are type confusions the loose syntax hides:
  is each binding an `Exp`, an `ExpVal`, a raw Scheme value, a datatype variant, a `Ref`, a list, or an env? Then
  check every use matches (`value-of` wants an `Exp`; `expval->…`/`apply-procedure` want an `ExpVal`/`proc`;
  `deref`/`setref!` want a `Ref`).
- Check your solution against **all** the examples; a draft on paper first helps.
- **`symbol` vs `string`.** Names from the lexer's `identifier` rule, and any `'tag` you build, are **symbols**, not
  strings. Predicate with `symbol?`, you can compare with `equal?` as long as you care only about the values and not it being the exact same about object.
- **Identifier vs expression** - A field that _names a variable_ is looked up with `apply-env` (then
  `expval->…`); a _sub-expression_ field is computed with `value-of` first.
- **Build with the variant constructor, not the type name** — `(enmtyp ids)`, never `(enumtype ids)`; the type name
  is only the predicate / `cases` head.
- **Parallel lists:** validate equal length before zipping (`for/proc`'s `[ids]`/`[exprs]`, `letrec`'s names/bodies)
  — a `car`/`cdr` walk off the shorter list errors confusingly mid-iteration.
- **Validate given list length if required** - Using the grammar itself or inside the interpreter.
- **`define-datatype` field guards run at construction.** A sentinel like `'none` can't go into a `proc?` field.
  Either widen the predicate — `(lambda (x) (or (proc? x) (eqv? x 'none)))` — or add a variant
  (`(define-datatype maybe-proc … (no-proc) (a-proc (p proc?)))`) so `cases` makes absence explicit.
- A `separated-list`'s **last argument is the separator and must be a terminal** (a string).
- Use `let`/`let*`/`letrec` (or external helpers) to keep long branches short and readable.
- Don't add stray parens — `( )` means a procedure call and will both confuse and break the solution.

### Useful information

It will be useful for you to include this in the guide:

```
# Pages
| Language      | Book | Guide      |
| ------------- | ---- | ---------- |
| let           | 69   | 105        |
| proc          | 79   | 114        |
| explicit-refs | 111  | 148        |
| implicit-refs | 118  | 152 (some) |

# let, proc
(define-datatype t t? (name (p1 t1?) (p2 t2?)))
(cases type v (c1 (p1 p2) exp1) (else exp2))
(apply-env env var) -> expval
(value-of expval1 env) -> expval
(map func lst) -> list
(cons item lst) -> [item] + lst
(list-ref lst index) -> lst[index]
(member value lst) -> slice of lst from index to the end or #f
(foldr f init '(a b c)) -> `(f a (f b (f c init)))` [f is (lambda (elem acc))]
(extend-env var val env)
(procedure var body env)
(apply-procedure proc1 arg)
(equal? v1 v2)
(arbno X), (separated-list exp ",")
(cond (bool1 exp1) (else exp2))
(eopl:printf "message")
(eopl:error 'location "message")
- `symbol` type exmaples - 'num, 'a,
- Count length of char in grammar - must use non terminal
- Complex type -
  (define proc-or-none?(lambda (x)
    (or (proc? x) (eqv? x 'none))))
- Read code very carefully line-by-line to verify it is correct, assume I forgot something

(define extend-env* (lambda (vars vals env2)
  (if (null? vars)  # assumes (length vars) = (length vals)
    env2
    (extend-env (car vars) (car vals) (extend-env* (cdr vars) (cdr vals) env2))
  )
))

# Refs
(newref expval1) -> reference
(deref ref) -> expval
(setref! ref expval1)
# implicit-refs
(apply-env env var) -> ref
(deref (apply-env env var)) -> expval
- Lazy calculation
  - Store in expval using "expression?" type
  - Rewrite in var:
    Check if var using "(cases expression (var-exp (v) ...))"
    If var then get ref using "(apply-env env var)"
    Rewrite value using `setref!`

## tuples example
# lang
(expression ("let" let-target "=" expression "in" expression) let-exp)
(let-target (identifier) single-target)
(let-target ("[" (separated-list slot ",") "]") multi-target)
(slot (identifier) named-slot)
(slot ("_") wild-slot)
# interp
(let-exp (target exp body)
  (cases let-target target
    (single-target (id)  (...))
    (multi-target(slots) (...))
  )
)

# Infer
- Apply current subs on equation
- Write current subs and apply equation on them
- Write new equation in subs
- Flip sides of equations if needed, drop "t = t"
- Compare function types if needed to extract other types
- Possible results:
  - Type
  - Type with var
  - Contradiction like int = bool
  - Contradiction like t1 = t1 -> t2
```

##### `main.py` — the practice harness

Copies a pristine language into a scratch **env** under `envs/`, lets you hand-edit it into a **feature**, and
captures/replays that feature as a portable diff — so every change becomes a reusable, testable artifact.

```sh
python3 main.py init proc-ds tuples           # envs/proc-ds-tuples <- pristine proc-ds
python3 main.py test proc-ds-tuples           # run that env's Racket test suite
python3 main.py export proc-ds-tuples tuples  # capture edits -> features/proc-ds-tuples.diff
python3 main.py import tuples proc-ds-try      # replay a feature onto another env
python3 main.py test-all                       # apply every feature, run tests, report PASS/FAIL
python3 main.py export-all                      # regenerate features.md from all diffs
```

### Nice to know

The remaining cheatsheets — reach for them when a specific feature calls for it.

#### Language evolution (chapters 3–4)

| feature           | LET   | PROC                   | LETREC                  | EXPLICIT-REFS        | IMPLICIT-REFS                 |
| ----------------- | ----- | ---------------------- | ----------------------- | -------------------- | ----------------------------- |
| procedures        | ❌    | ✅ (anonymous, `proc`) | ✅ recursive (`letrec`) | ✅ recursive         | ✅ via `extend-env-rec*`      |
| recursion         | ❌    | ❌                     | ✅                      | ✅                   | ✅ (functions only, not data) |
| env binds         | value | value                  | value                   | value or reference   | **reference only**            |
| uses the store    | ❌    | ❌                     | ❌                      | ✅ manual (`newref`) | ✅ automatic (every var)      |
| mutable variables | ❌    | ❌                     | ❌                      | ✅ via `setref`      | ✅ via `set`                  |
| closures          | ❌    | ✅                     | ✅ (+ recursion)        | ✅                   | ✅                            |

(MUTABLE-PAIRS / CALL-BY-REFERENCE / CALL-BY-NEED build on IMPLICIT-REFS — same store model, adding mutable pairs
and the parameter-passing disciplines below.)

#### Denoted vs. expressed values

**ExpVal** = what `value-of` returns. **DenVal** = what the environment binds a name to. They coincide until the
store appears, where DenVal becomes a _reference_.

| language                   | DenVal (env binds)                                                                       | ExpVal (value-of returns)             |
| -------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------- |
| **LET**                    | Int + Bool                                                                               | Int + Bool                            |
| **PROC**                   | Int + Bool + Proc                                                                        | Int + Bool + Proc                     |
| **LETREC**                 | Int + Bool + Proc                                                                        | Int + Bool + Proc                     |
| **LEXADDR**                | Int + Bool + Proc _(by position, not name)_                                              | Int + Bool + Proc                     |
| **EXPLICIT-REFS**          | Int + Bool + Proc + **Ref**                                                              | Int + Bool + Proc + **Ref**           |
| **IMPLICIT-REFS**          | **Ref** _(a location)_                                                                   | Int + Bool + Proc + Ref               |
| **MUTABLE-PAIRS**          | **Ref**                                                                                  | Int + Bool + Proc + Ref + **MutPair** |
| **CALL-BY-REFERENCE**      | **Ref**                                                                                  | Int + Bool + Proc + Ref + MutPair     |
| **CALL-BY-NEED**           | **Ref** → (Thunk or value) in the store                                                  | Int + Bool + Proc + Ref + MutPair     |
| **CHECKED** / **INFERRED** | same runtime as LETREC (Int + Bool + Proc); statically a **Tenv** maps names → **Types** | Int + Bool + Proc                     |

- **Chapter 3** — DenVal = ExpVal: the env stores values directly.
- **EXPLICIT-REFS** — references are ordinary expressed values you make by hand, so DenVal is still = ExpVal (now
  _including_ Ref).
- **IMPLICIT-REFS onward** — the pivot: DenVal becomes **Ref only**; reading a variable dereferences. This is what
  enables assignment and aliasing.
- **CALL-BY-NEED** — the location may hold a **Thunk** until first forced; a Thunk is _not_ an ExpVal (never escapes
  the store).
- **Types** — at run time they behave like LETREC; the checker adds a _static_ **Tenv** (names → Types).

#### Parameter-passing modes

All routed through one helper, `value-of-operand`, which decides what to hand the procedure:

| mode                             | what's passed                      | effect                                       |
| -------------------------------- | ---------------------------------- | -------------------------------------------- |
| **call-by-value** (EOPL default) | the value, in a **fresh** location | inside changes don't leak out                |
| **call-by-reference**            | the caller's **existing** location | aliasing — inside changes _do_ leak out      |
| **call-by-name**                 | an unevaluated **thunk**           | recomputed on _every_ use (lazy, no caching) |
| **call-by-need**                 | a thunk, **memoized**              | lazy, but computed at most once              |

#### `print` / `display` — a side-effecting builtin (returns a dummy)

Adding a `print(e)` that evaluates `e`, displays it, and yields a throwaway value — the same _effect-then-dummy_
shape as `setref`/`set` (see [why `begin` + `num-val`](#explicit-refs)):

```scheme
;; grammar (lang.scm) — one new production:
(expression ("print" "(" expression ")") print-exp)

;; interp (interp.scm) — unwrap nothing extra; just display the value and return a dummy:
(print-exp (e)
  (let ((v (value-of e env)))           ; evaluate the argument to an ExpVal
    (begin
      (eopl:printf "~s~%" v)            ; SIDE EFFECT — print it (`~s` = value, `~%` = newline)
      (num-val 1))))                    ; dummy ExpVal so value-of still returns one
```

Usage: `print(-(8,3))` prints `#(struct:num-val 5)` and evaluates to `(num-val 1)`.

Notes:

- `eopl:printf` is the EOPL print procedure (Scheme-level); for a raw Scheme value use `display`/`(eopl:printf
"~s~%" x)`. To print the _unwrapped_ number instead of the `num-val` record, unwrap first:
  `(eopl:printf "~s~%" (expval->num v))`.
- Like every store/effect op, it must still **return an `ExpVal`** — hence the dummy `(num-val 1)`. Sequence several
  with the target language's `begin … end`.
- This is purely a side effect; it doesn't change the value of `e` (it returns the dummy, not `v`). If you'd rather
  print _and pass the value through_, return `v` instead of `(num-val 1)`.

## Part 2 — Type inference (question 3)

Question 3 is the Hindley-Milner type-inference algorithm for the **INFERRED** language. The language
itself — grammar, substitutions, the unifier, how `type-of` threads a substitution — is described
under [INFERRED](#inferred) in the course material; what follows is _how to run the algorithm by
hand_.

### Step 1 — give each variable and non-trivial sub-expression a type variable

The whole expression is `t0`; each bound variable gets its own (`tf`, `tx`, …) and each compound
sub-expression gets `t1, t2, …`. Literals (`3`, `0`) get **no** variable — their type is just `int`.

### Step 2 — generate the constraints

The inferrer walks the AST **bottom-up** (`tₑ` = the type of `e`). The nodes that call `unifier`
**emit an equation**; the rest just build or propagate a type:

| expression                      | constraints emitted (`unifier` calls) | meaning                                                                                   |
| ------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------- |
| `42` (const)                    | `t_res = int`                         | a literal is `int` outright                                                               |
| `x` (var)                       | `t_res = tenv(x)`                     | looked up in the type environment                                                         |
| `zero?(E)`                      | `t_E = int`; `t_res = bool`           | tests an int, yields a bool                                                               |
| `-(E1, E2)`                     | `t₁ = int`, `t₂ = int`; `t_res = int` | arithmetic needs numeric inputs                                                           |
| `if E1 then E2 else E3`         | `t₁ = bool`, `t₂ = t₃`; `t_res = t₂`  | condition is bool; both branches agree                                                    |
| `let x = E1 in Body`            | `t_x = t₁`, `t_res = t_body`          | no equation — just extends the tenv                                                       |
| `proc (x : ?) Body`             | `t_res = tₓ → t_body`                 | builds a function type (`tₓ` = the annotation, or a fresh tvar if `?`)                    |
| `(Rator Rand)`                  | `t_rator = t_rand → t_res`            | **the critical rule:** the function's type must match arg→result; `t_res` is a fresh tvar |
| `letrec ? p(x : ?) = Body in E` | `t_Body = t_r`; `t_res = t_E`         | the body must match the declared result type (`t_r` = `p`'s result annotation)            |

### Step 3 — unify (the two-column worksheet)

Keep two columns: **Equations** (still to solve) and **Substitution** σ (solved so far — every
left-hand side is a variable). Start with every equation on the left and σ empty. Take each `L = R`
and apply the **first** matching rule:

1. **Apply σ to the equation first** — replace any variable already bound in σ by its binding.
2. **Identity** (`int = int`, `t2 = t2`) → **discard**.
3. **A variable on one side** → move `L = R` into σ (if only `R` is the variable, **switch sides**
   first: `int = tx` ⟶ `tx = int`). On moving, **propagate** the binding through all of σ. **Occurs
   check:** refuse `t = R` when `t` appears _inside_ `R` (e.g. `tf = tf -> int`) → no solution.
4. **Neither side a variable** → both function types → **decompose** `a -> b = c -> d` into `a = c`,
   `b = d`. Any other mismatch (`int = bool`, `int = a -> b`) → clash → no solution.

When the Equations column is empty, σ is the solution; the type is `t0` with σ fully applied.

**Worked example** — `proc (f) proc (x) -((f 3),(f x))`. Variables: `t0`=whole, `t1`=`proc(x)…`, `t2`=`-(…)`,
`t3`=`(f 3)`, `t4`=`(f x)`. Equations:

```text
(1) t0 = tf -> t1      (2) t1 = tx -> t2      (3) t3 = int
(4) t4 = int           (5) t2 = int           (6) tf = int -> t3      (7) tf = tx -> t4
```

Worksheet (only the meaningful action per equation is shown):

| take | equation         | action                                            | substitution after                                                    |
| ---- | ---------------- | ------------------------------------------------- | --------------------------------------------------------------------- |
| (1)  | `t0 = tf -> t1`  | LHS var → move                                    | `t0 = tf -> t1`                                                       |
| (2)  | `t1 = tx -> t2`  | move; propagate `t1`                              | `t0 = tf -> (tx -> t2)`, `t1 = tx -> t2`                              |
| (3)  | `t3 = int`       | move                                              | …, `t3 = int`                                                         |
| (4)  | `t4 = int`       | move                                              | …, `t4 = int`                                                         |
| (5)  | `t2 = int`       | move; propagate `t2`                              | `t0 = tf -> (tx -> int)`, `t1 = tx -> int`, `t2 = int`                |
| (6)  | `tf = int -> t3` | apply σ → `tf = int -> int`; move; propagate `tf` | `t0 = (int -> int) -> (tx -> int)`, …, `tf = int -> int`              |
| (7)  | `tf = tx -> t4`  | apply σ → `int -> int = tx -> int`; **decompose** | → new eqns `int = tx`, `int = int`                                    |
|      | `int = tx`       | switch → `tx = int`; move; propagate `tx`         | `t0 = (int -> int) -> (int -> int)`, `t1 = int -> int`, …, `tx = int` |
|      | `int = int`      | identity → discard                                | (done)                                                                |

Result: **`t0 = ((int -> int) -> (int -> int))`**.

### Step 4 — failures & insights

- **Type clash** — `if x then -(x,1) else 0` forces `tx = bool` (the condition) _and_ `tx = int` (from
  `-(x,1)`); applying σ gives `bool = int` → **untypable**.
- **Occurs check** — `proc (f) zero?((f f))` gives `tx = tx -> t8`; `tx` occurs inside its own
  right-hand side → infinite type → **untypable**. This is exactly what the occurs check in rule 3 prevents.
- **Monomorphic lock-in** — base INFERRED has no real polymorphism: `proc (x : ?) x` infers `tx -> tx`,
  but once you apply it to an `int`, `tx` is **locked to `int`** for the rest of the program.

**Common mistakes:** forgetting to apply σ _before_ classifying an equation; dropping an equation whose
variable is on the right (switch sides instead); propagating a binding only into `t0` rather than all of
σ; treating `int = int` / `t = t` as an error; skipping **decomposition** of `a -> b = c -> d`.

### CLI reference — `infer`

`python3 main.py infer '<program>'` type-infers an INFERRED program and prints the whole derivation —
fresh type variables, the generated constraints, then unification step by step (the same by-hand
method above) — so you can check your hand-worked answer against the tool. A bracketed
`[sub in equation: …]` marks a step where applying the substitution left the equation unchanged. Add
`--brief` for just the final type, or run it with no program to print the surface-syntax reference.

```
$ python3 main.py infer 'proc (x : ?) -(x,1)'
========================================================================
PROGRAM:  proc (x : ?) -(x, 1)
========================================================================

Initial type environment (free vars):  x:int  v:int  i:int
Constants have no type variable (a literal is `int`).

--- Step 0: a type variable for every variable and compound sub-expression ---
  tx   = type of   x   (variable)
  t0   = type of   proc (x : ?) -(x, 1)
  t1   = type of   -(x, 1)

--- Step 1: constraints generated from the AST ---
  C1   tx = int                [- needs int operands]
  C2   t1 = int                [- yields an int]
  C3   t0 = (tx -> t1)         [proc builds arg -> result]

--- Step 2: unification (apply subs, then solve each equation) ---
  1) choose equation:   tx = int   [- needs int operands]
     [sub in equation:   tx = int]
     new/changed subs:  { tx -> int }
  2) choose equation:   t1 = int   [- yields an int]
     [sub in equation:   t1 = int]
     new/changed subs:  { t1 -> int,  tx -> int }
  3) choose equation:   t0 = (tx -> t1)   [proc builds arg -> result]
     sub in equation:   t0 = (int -> int)
     new/changed subs:  { t0 -> (int -> int),  t1 -> int,  tx -> int }

--- Final subs ---
  { t0 -> (int -> int),  t1 -> int,  tx -> int }

========================================================================
TYPE OF PROGRAM:  t0   (= (int -> int))
========================================================================
```

# Appendix — variants & optimizations

Branches off the main LET → PROC → LETREC and store progressions: a worked scoping exercise, a
compile-time optimization (LEXADDR), the alternative parameter-passing disciplines
(call-by-reference, call-by-need), and an error-handling extension (exceptions). Each is presented
as a delta on the chapter it extends.

## Nested shadowing — which binding wins? (PROC)

**Q.** Evaluate `((proc (x) proc (x) (x 12) 7) proc (x) -(x,8))`.

It's tempting to think the **first** `proc (x)` (the one applied first, binding `x = 7`) sets the value that the
body sees. It doesn't — under lexical scoping the **innermost** binding shadows the outer one.

**Parse.** The rator is itself a call `(F 7)`:

```
call( rator = call( proc(x, proc(x, (x 12))),  7 ),   rand = proc(x, -(x,8)) )
```

**Eval** (each `proc` captures the current env; each application _prepends_ a new frame; `lookup` returns the
**first** match, front→back):

```
(F 7)                : apply proc(x, proc(x,(x 12))) to 7
                       ρ1 = [x=7] ρ0,  body proc(x,(x 12)) → closure C2 (saved env ρ1)
rand                 : proc(x,-(x,8)) → closure C3
apply C2 to C3       : ρ2 = [x=C3] ρ1 = [x=C3] [x=7] ρ0
                                          ▲inner    ▲outer (set first, now buried)
  (x 12)             : lookup x in ρ2 → C3   (the x=7 is shadowed, never reached)
                       (C3 12) → -(12,8) = 4
```

**A. `4`** — not `3`, and not an error.

**Takeaway.** _Set first ≠ wins._ `extend-env` only ever adds a frame **in front**, and `apply-env` returns the
**first** match, so the binding created **last** (the lexically closest `proc (x)`) is the one the body sees. The
probe that proves it: the body uses `x` as a _function_ (`(x 12)`), so if the outer `x = 7` had won you'd get an
error (`(7 12)`); getting `4` shows the inner `x` (the proc) won. (See [the `let` family](#the-let-family--binding-scope)
and [PROC](#proc).)

## LEXADDR

Same language as PROC, but variable **names are compiled away** into _lexical addresses_ before execution: a
`(depth)` index saying how many scopes out the binding lives. Adds a whole **translator pass** between parse and
eval. Source: [lexaddr](chapter3/lexaddr/).

**Example** — source is identical to PROC; the translator rewrites each variable to its address first:

```text
% source
let x = 37 in proc (y) -(y, x)
% after translation — inside the proc body, y is 0 scopes out, x is 1:
%let 37 in %lexproc -(%nameless-var 0, %nameless-var 1)
```

**Pipeline now has three stages** ([top.scm](chapter3/lexaddr/top.scm)):

```
scan&parse  →  translation-of-program  →  value-of-translation
 (names)        (names → addresses)         (runs nameless code)
```

**Grammar** — new "nameless" productions the translator emits (the `%` keywords mark compiled forms):

```scheme
(expression ("%nameless-var" number) nameless-var-exp)   ; a variable, as a depth index
(expression ("%let" expression "in" expression) nameless-let-exp)
(expression ("%lexproc" expression) nameless-proc-exp)
```

**Translator** ([translator.scm](chapter3/lexaddr/translator.scm)) walks the AST with a **static
environment** (`senv` = just a list of the names in scope) and replaces each variable with its address:

```scheme
(var-exp (var)   (nameless-var-exp (apply-senv senv var)))   ; name → index
(let-exp (var exp1 body)
  (nameless-let-exp (translation-of exp1 senv)
                    (translation-of body (extend-senv var senv))))  ; push name onto senv
(proc-exp (var body)
  (nameless-proc-exp (translation-of body (extend-senv var senv))))
```

**`value-of`** now runs against a **nameless environment** (just a list of values — no names). Lookup is plain
indexing, no symbol comparison:

```scheme
(nameless-var-exp (n) (apply-nameless-env nameless-env n))   ; index into the list
(nameless-let-exp (exp1 body)
  (value-of body (extend-nameless-env (value-of exp1 nameless-env) nameless-env)))
(nameless-proc-exp (body)
  (proc-val (procedure body nameless-env)))
```

Key ideas:

- **Two environments, two phases.** `senv` (compile time) holds _names_ to compute addresses; `nameless-env`
  (run time) holds _values_ and is indexed by those addresses.
- **De Bruijn indices.** A lexical address is `(depth, position)`: **depth** = how many enclosing scopes (shells)
  out the binding lives; **position** = which slot within that frame. This simplified LET-based language binds one
  variable per scope, so a single **depth** number suffices.
- **Why** — at run time the env is a flat list, so lookup is immediate `list-ref` (O(1)) instead of walking and
  comparing symbol strings (O(n)); names exist only until translation.

## CALL-BY-REFERENCE

Same surface language as MUTABLE-PAIRS, but **changes how arguments are passed**: a variable argument shares the
caller's location instead of getting a fresh copy. Source: [call-by-reference](chapter4/call-by-reference/).

**Example** — a real swap, because `a` and `b` are passed by reference:

```text
let swap = proc (x) proc (y)
             let t = x in begin set x = y; set y = t end
in let a = 33 in let b = 44 in
   begin ((swap a) b); -(a, b) end       % a,b swapped → 44 - 33   => 11
                                         % (call-by-value would give 33 - 44 = -11)
```

**Grammar / data structures** — unchanged from the previous language.

**`value-of`** — the difference is one helper, `value-of-operand`, used by `call-exp` instead of plain `value-of`:

```scheme
(define value-of-operand
  (lambda (exp env)
    (cases expression exp
      (var-exp (var) (apply-env env var))      ; pass the EXISTING location (alias!)
      (else (newref (value-of exp env))))))    ; non-variables still get a fresh location
;; apply-procedure then binds the parameter directly to that ref (no extra newref)
```

Compare IMPLICIT-REFS, where the argument was _always_ `(newref arg)` — a fresh box (call-by-value).

**Key ideas**

- **Call-by-value vs. call-by-reference** — the whole difference is "fresh location" vs. "share the caller's".
- **Aliasing** — callee and caller variables can name the same box, so `set` inside the proc is visible outside.
- A `swap(x, y)` procedure now actually swaps the caller's variables; non-variable args still get fresh refs.

## CALL-BY-NEED

Lazy evaluation: arguments are passed **unevaluated as thunks**, forced on first use, then **memoized**. Source:
[call-by-need](chapter4/call-by-need/).

**Example** — the argument is a type error, but it's never used, so it's never forced:

```text
let f = proc (x) 11
in (f -(1, zero?(0)))                    % bad arg ignored → no error        => 11
                                         % (call-by-value would crash forcing -(1, bool))
```

**Grammar** — unchanged from CALL-BY-REFERENCE.

**Data structures** — a `thunk` captures a delayed expression with its env; thunks live in the store (behind refs):

```scheme
(define-datatype thunk thunk? (a-thunk (exp1 expression?) (env environment?)))
```

**`value-of`** — arguments become thunks; `var-exp` forces and caches:

```scheme
(define value-of-operand
  (lambda (exp env)
    (cases expression exp
      (var-exp (var) (apply-env env var))      ; share ref (as call-by-reference)
      (else (newref (a-thunk exp env))))))     ; delay everything else

(var-exp (var)
  (let* ((ref1 (apply-env env var)) (w (deref ref1)))
    (if (expval? w)
        w                                       ; already forced
        (let ((v1 (value-of-thunk w)))          ; force the thunk…
          (begin (setref! ref1 v1) v1)))))       ; …and memoize it back into the store
```

**Key ideas**

- **Lazy / call-by-need** — an argument is evaluated only if and when used, not at the call.
- **Memoization** — the first force writes the value back, so later uses are O(1) (this is what distinguishes
  call-by-_need_ from call-by-_name_, which would re-evaluate each time).

The **four parameter-passing modes** (call-by-value / reference / name / need) are compared in the
[Parameter-passing modes](#parameter-passing-modes) cheatsheet.

## Exceptions (LET)

Errors stop **aborting** the program; instead they become **exception values that propagate**, and
`try` / `catch` / `finally` / `throw` let you intercept them. Crucially there is **no** Scheme
`raise`/`with-handlers`/`dynamic-wind` — the LET interpreter is direct-style (pre-continuations), so
`value-of` simply **returns** an `excp-val` and every composite expression checks for one and bails
out. Source: feature `let-exception` (exam 2023b-84).

**Example** — a type error inside the `let` binding propagates as a value, so the body `78` is never reached:

```text
let t = -(6, zero?(9)) in 78    % zero?(9) is a bool → -(6,bool) → "not a number"
                                % => (excp-val (Exception "not a number"))
```

…and catching one (`finally` runs but its value is discarded):

```text
try { -(if -(4,6) then 70 else 20, 45) }   % -(4,6) = -2 used as a bool test → "not a boolean"
catch [not a boolean] : 13 ;
finally : 200 ;                            % => 13
```

**Grammar** — `throw`, `try`, and the four exception keywords (each a single literal token so the grammar stays LL(1)):

```scheme
(expression ("throw" except) throw-exp)
(expression ("try" "{" expression "}"
             (arbno "catch" "[" except "]" ":" expression ";")
             (arbno "finally" ":" expression ";"))
            try-exp)
(except ("general") except-general)        ; + not-a-number / not-a-boolean / environment
```

**Data structures** — an exception is just another expressed value:

```scheme
(define-datatype exception exception? (Exception (msg string?)))
;; expval gains:  (excp-val (exn exception?))
```

**`value-of`** — exceptions are born at the error sites and propagate via two helpers:

```scheme
(define need-num                          ; "I need a number here"
  (lambda (v k)
    (cases expval v
      (excp-val (e) v)                     ; already an exception → pass it up unchanged
      (num-val (n) (k n))                  ; a number → continue with k
      (else (excp-val (Exception "not a number"))))))   ; wrong type → raise

(diff-exp (e1 e2)                          ; short-circuits on the first exception operand
  (need-num (value-of e1 env)
    (lambda (n1) (need-num (value-of e2 env)
      (lambda (n2) (num-val (- n1 n2)))))))

(let-exp (var e1 body)                     ; a throwing binding skips the body
  (let ((v1 (value-of e1 env)))
    (if (excp-val? v1) v1 (value-of body (extend-env var v1 env)))))

(throw-exp (excpt) (excp-val (Exception (except->msg excpt))))

(try-exp (exp1 excpts excptexps finexps)   ; body; first matching catch; finally always
  (let* ((r (value-of exp1 env))
         (h (if (excp-val? r) (handle-exn r excpts excptexps env) r)))
    (begin (run-finally finexps env) h)))
```

`apply-env` returns `(excp-val (Exception "environment"))` for an unbound variable (instead of
`eopl:error`); `handle-exn` runs the first `catch` whose message matches and otherwise returns the
exception unchanged, so it keeps propagating.

**Key ideas**

- **Exceptions are values.** `value-of` may return an `excp-val`; the whole interpreter is written to
  notice one and get out of the way. No host-language control flow is used.
- **`need-num` / `need-bool`** centralize the "propagate-else-extract-else-raise" rule, so each
  arithmetic/condition branch stays one line and short-circuits automatically.
- **`finally` always runs** — because everything is plain value passing, "always" is just "evaluate
  it before returning the result"; no `dynamic-wind` is needed. A `catch` handler that itself
  `throw`s propagates naturally (its `value-of` is another `excp-val`).
- **No top-level handler** — an uncaught exception is simply the program's result, so
  `value-of-program` is unchanged.
