# Software Tests Summary

We can almost never run a program on *every* possible input (there are far too many). So testing is really about **choosing a small, smart set of inputs** that still gives us confidence the program is correct. A **coverage criterion** is just a rule that tells you *which* inputs (or paths, or combinations) you must exercise — e.g. "run every line at least once" or "make every `if` go both true and false". Most of this guide is a tour of different such rules, how to satisfy them, and how they compare in strength. Keep asking two questions while you read: *"What must this criterion make me test?"* and *"How few tests can I get away with?"*

**How to read this doc.** Each section has: **Key definitions** (the vocabulary), **The recipe** (the mechanical steps to answer an exam question), a **Worked example**, **Exam patterns & gotchas** (traps that lose points), and a **Cheat sheet** (the compressed version to memorize). If a term looks unfamiliar, look for a `> **Plain words:**` note near its first use.

## Topics

| #   | Topic                                                                                                   | Exam frequency |
| --- | ------------------------------------------------------------------------------------------------------- | -------------- |
| 1   | [Mutation Testing](#1-mutation-testing)                                                                 | Q1 every exam  |
| 2   | [Control Flow & Coverage Criteria](#2-control-flow--coverage-criteria)                                  | every exam     |
| 3   | [Data Flow Testing](#3-data-flow-testing)                                                               | most exams     |
| 4   | [Subsumption — Master Cheat Sheet](#4-subsumption--master-cheat-sheet)                                  | every exam     |
| 5   | [Combinatorial / Pairwise (AETG, IPO/IPOG)](#5-combinatorial--pairwise-testing-aetg--ipoipog)           | every exam     |
| 6   | [Symbolic Execution](#6-symbolic-execution)                                                             | every exam     |
| 7   | [Concolic Testing (DART, CUTE)](#7-concolic-testing-dart--cute)                                         | most exams     |
| 8   | [FSM-based Testing (UIO, DS, W)](#8-fsm-based-testing-uio-ds-w-set)                                     | every exam     |
| 9   | [Black-box (ECP, BVA, Decision Tables, Domain)](#9-black-box-techniques-ecp-bva-decision-tables-domain) | sometimes      |
| 10  | [JUnit & Tooling (Pitest, JaCoCo)](#10-junit--tooling-reference-pitest-jacoco)                          | support        |
| 11  | [Exam Playbook & Master Cheat Sheets](#11-exam-playbook--master-cheat-sheets)                           | —              |

---

## 1. Mutation Testing

> **Plain words:** Mutation testing checks *how good your tests are* (not the program). The idea: deliberately break the program in tiny ways — each broken copy is a **mutant** — then see whether your test suite notices. A good suite should fail on a broken program. If a mutant slips through with all tests still passing, your tests have a blind spot. Think of it as "planting bugs on purpose to check that your bug-detector actually detects."

**Key definitions:**

- **Mutant** — a copy of program `P` with _one_ small, still-compilable change, written `Pᵢ`. "Syntactically-valid change" just means the edit still compiles/runs (you can't test a program that won't build). Examples: swap an operator (`>` → `>=`, `+` → `-`), or change a boundary. One mutant = one tiny change.
- **Killed (dead) mutant** — at least one test in your suite `T` gives a _different output_ on the mutant `Pᵢ` than on the original `P`. That difference is the test "catching" the planted bug. **Survived** — no test noticed the change (all tests give the same result on `Pᵢ` as on `P`). Surviving mutants point at weak spots in your tests.
- **Equivalent mutant** — the change happens to make _no difference at all_: `Pᵢ` and `P` behave identically on _every possible input_ (e.g. rewriting `a*b` as `b*a`). No test can ever kill it because there is nothing to catch — it's not really a different program. Deciding in general whether two programs always agree is **undecidable** ("undecidable" = no algorithm can answer it correctly for every case; you must argue each one by hand).
- **Mutation score** = `100 × D / (N − E)` — D = killed, N = total mutants, E = equivalent. It's the percentage of *killable* mutants your suite actually killed. Equivalents are removed from the **denominator** (they were never killable, so counting them would unfairly punish the suite), and never counted as killed. Higher score = stronger test suite.
- **Competent-programmer hypothesis** — the assumption that real programmers write *almost*-correct code, so real bugs are small slips (a wrong operator, an off-by-one), not wild rewrites. **Coupling effect** — the observation that tests catching these small planted bugs also tend to catch bigger, more complex bugs. Together these justify why testing with *single* tiny changes is worthwhile.
- A mutant survives if **either**: (1) no test even executes the mutated line, **or** (2) a test runs the line but the final _output_ comes out the same anyway (this case includes equivalent mutants). "iff" = "if and only if".

**The recipe (per mutant):**

0. **Precondition:** run the suite `T` against the original `P` first — every test must pass. A failing test means **fix `P` and retest**, not a killed mutant. The whole process iterates: after adding tests, re-run until the score clears the chosen threshold.
1. **Locate** the mutated line and the exact change (e.g. `>` → `>=`).
2. **Find a reaching input** — an input that (a) actually runs the mutated line, AND (b) makes the mutated expression compute a different value there than the original would. Step (b) is called **infection**: the internal state is now "infected" (wrong) at that point. Just running the line isn't enough; the value has to actually diverge.
3. **Propagate:** an infected internal value is useless unless it changes what the program finally *outputs/returns* — that's **propagation** (the wrong value has to travel out to where a test can see it). Check the return value / output actually differs for that input. If for _every_ input the output stays identical → the change never shows ⇒ **equivalent** (add to E). Otherwise it is **killable**.
4. **Killed?** A mutant is killed iff the _existing_ test suite contains an input from step 2/3 whose asserted value now mismatches. If none → it **survives**.
5. **Count:** N = total mutants, E = equivalents, D = killed.
6. **Score** = `100·D/(N−E)`.
7. **To reach 100%:** for each surviving non-equivalent mutant, add a test whose input flips the mutated expression's outcome AND whose assertion checks the differing result. Boundary-adjacent inputs (the two values straddling a comparison) kill the most mutants per test.

**Worked example:** method `compute(a,b)` with mutants `a*b→a/b`, `a*b→b*a`, `a*b+a→a*b+b`. The `a*b→b*a` mutant is **equivalent** (multiplication is commutative ⇒ no input distinguishes it). Of the 2 non-equivalent mutants, the given suite kills 1 → **score = 1/2 = 50%** (denominator excludes the equivalent one). Adding `assertEquals(3, compute(1,2))` kills the survivor → 100%.

**Exam patterns & gotchas:**

- **Equivalent-mutant arguments that recur:** (a) _commutativity/algebra_ — `a*b`→`b*a` is equivalent. (b) _unreachable difference_ — the mutated value differs only on an input a guard already excludes (e.g. mutating `purchases>=0` when the spec guarantees `purchases≥0`, so the only differing input `0` never changes the output). (c) `>`→`>=` is equivalent only when the boundary value can never occur. Always justify by exhibiting either a _distinguishing input_ (not equivalent) or an _argument that no input distinguishes them_ (equivalent).
- **Score formula:** memorize `100·D/(N−E)`. Equivalents leave the denominator; they are NOT killed. If a question says "considering the equivalent mutants," it means _exclude them from the denominator_.
- **Killing test must assert the differing output**, not just execute the line. Trap: a test can give _full statement/branch coverage yet leave a mutant alive_ because its assertion is too weak. The fix adds the boundary input (e.g. `foo(0)`).
- **Branch coverage ≠ mutants all killed:** 100% branch coverage does NOT guarantee killing all CONDITIONALS*BOUNDARY mutants — you cover both branches without testing the \_boundary value* distinguishing `>` from `>=`. Counterexample: `if(x>0)` tested with x=5 and x=−5 covers both branches but x=0 (where `>` vs `>=` differ) is untested → mutant survives.
- **Writing a surviving mutant on purpose:** pick a comparison, test only inputs _far_ from the boundary so the boundary swap doesn't change any asserted result.

**Cheat sheet — Pitest default mutators:**

| Mutator (NAME)                                      | What it does                                           | Example                              |
| --------------------------------------------------- | ------------------------------------------------------ | ------------------------------------ |
| **Conditionals Boundary** (`CONDITIONALS_BOUNDARY`) | `<`↔`<=`, `>`↔`>=`                                     | `a<b` → `a<=b`                       |
| **Negate Conditionals** (`NEGATE_CONDITIONALS`)     | flip the whole relational op                           | `==`→`!=`, `>`→`<=`, `>=`→`<`        |
| **Math** (`MATH`)                                   | swap arithmetic op                                     | `*`→`/`, `+`→`-`, `%`→`*`, `<<`→`>>` |
| **Increments** (`INCREMENTS`)                       | `++`↔`--`                                              |                                      |
| **Invert Negatives** (`INVERT_NEGS`)                | `-x` → `x`                                             |                                      |
| **Return Values** (`*_RETURNS`)                     | mutate returns: `true`↔`false`, `0`→`1`, non-null→null |                                      |
| **Void Method Calls** (`VOID_METHOD_CALLS`)         | delete a void call                                     |                                      |

Exact boundary table (memorize): `<→<=`, `<=→<`, `>→>=`, `>=→>`.
Exact negate table: `==→!=`, `!=→==`, `<=→>`, `>=→<`, `<→>=`, `>→<=`.

---

## 2. Control Flow & Coverage Criteria

> **Plain words:** "Control flow" = the order in which statements run and the branch points (`if`, loops) that decide the route. We draw the program as a map — the **Control Flow Graph (CFG)** — and then pick coverage rules that say how thoroughly the map must be walked: every box? every fork-direction? every combination of conditions in a fork? The rules get progressively stronger (and need more tests). The recurring exam skills are: *draw the CFG*, *pick the smallest test set that satisfies a given rule*, and *say how many tests each rule needs*.

**Key definitions:**

- **CFG (Control Flow Graph)** — a diagram of the program's possible routes. Three node shapes: **computation** (rectangle = straight-line code that just runs top to bottom), **decision** (diamond = a condition, with a True edge and a False edge coming out), **merge** (circle = where two branches rejoin). Assume one **entry** and one **exit**; number every node so you can name paths like `1,2,3`.
- **Statement (node) coverage** — every node runs at least once. This is the _weakest_ rule (bare minimum: "no line of code went completely untested").
- **Branch (edge/decision) coverage** — every decision is taken **both** ways: each `if` goes True at least once and False at least once. **Subsumes statement** (see §4 — it forces every node to run too, so it's strictly stronger).
- **Basic-condition coverage** — in a compound condition like `a && b`, each _elementary_ (atomic) part `a` and `b` is individually made both True and False at some point. _Incomparable with branch_ (neither one guarantees the other — see §4).
- **Branch-and-condition** — satisfy branch coverage AND basic-condition coverage at the same time.
- **Compound-condition** — test _every combination_ of the atomic conditions in one decision. With N atoms that's up to **2ᴺ** combinations (short-circuit evaluation — where `&&`/`||` stops early once the result is decided — removes some impossible combinations).
- **MC/DC (Modified Condition/Decision Coverage)** — for _each_ atomic condition, show it matters *on its own*: find two tests that differ in **only that one condition** and produce **opposite** overall decision results (proving that condition alone can flip the outcome). This needs about **N+1** tests for N conditions — far fewer than the 2ᴺ of compound-condition — because each test is reused across several conditions. Required by aviation-safety standards **DO-178B / ED-12B**.
- **Boundary-interior** — a way to tame loops (which otherwise create infinitely many paths). It splits the loop paths into two classes:
  - **Boundary tests** = paths that *enter the loop but exit after at most one iteration* (this class also includes the path that skips the loop entirely). **These are exactly what you get by unfolding the CFG into a tree up to the first repeated node** (the loop condition on its 2nd arrival), then stopping and exiting — provide one feasible path for every branch of that tree. In this course, the boundary set is the expected answer.
  - **Interior tests** = the *more general* case: paths that iterate **2+ times, where the first two iterations differ** from each other. These need you to unfold *further* (a second iteration), so stopping at the first repeated node does **not** produce them. Mentioned for completeness; usually not required.
  - Quick test (from the course clarification): take a feasible path that starts with the unfolded prefix — *one iteration then exit → boundary; two-or-more differing iterations → interior.* Also aim for full branch coverage on any branches **outside** the loop.
- **Loop-boundary adequacy** — a simpler loop rule: run each loop **0 times, exactly 1 time, and more than 1 time** (the three qualitatively different loop behaviors).

> **⚠️ Loop-boundary vs boundary-interior — don't confuse them** (the word "boundary" means different things):
> | | **Loop-boundary** | **Boundary-interior** |
> |---|---|---|
> | Cares about | iteration **count** | iteration **paths** |
> | Requirement | run loop **0, 1, >1** times | every subpath of the CFG unfolded to the first repeated node (the *boundary* tests) |
> | Granularity | coarse — ignores which body path runs | fine — distinguishes the body's branches (`if`-T vs `if`-F count separately) |
> | Strength | **base** of the hierarchy; **incomparable** with statement | **near the top**; **subsumes branch** |
>
> Here "boundary" is a false friend: a *loop-boundary* "boundary" is an **iteration-count edge case** (0/1/many); a *boundary-interior* "boundary" test is a **path that barely enters the loop**. Example `while(c){ if(d) X else Y }`: loop-boundary just needs it run 0×, 1×, ≥2× (3 tests, indifferent to `d`); boundary-interior forces both the `X` and `Y` body paths.
- **Subsumption:** "A subsumes B" means A is at least as strong — any test set that satisfies A automatically satisfies B, for *every* program. (Full treatment in §4.)

**The recipe:**

_Drawing the CFG:_ one node per basic block; each `if`/loop condition = a diamond with T/F edges; loop back-edge returns to the condition node; merge after branches. Number nodes; label which source line each represents (line numbers are required).

_Branch coverage + denominator:_ denominator = **number of outgoing edges from decision nodes** = 2 × (number of decisions counted as branches). Example: two `if`s → **4 branches**. Pick a minimal input set hitting each diamond's T and F.

_Boundary-interior (the high-value recipe):_

1. Draw CFG, identify the loop condition node.
2. **Unfold into a tree**, expanding until you reach a node you've _already visited_ (the loop-condition node on its second arrival), then stop and exit the loop.
3. Enumerate every root-to-leaf subpath. **Always include the path that does NOT enter the loop** (condition false on first arrival).
4. For each subpath, find a _feasible_ concrete input. If a prefix is infeasible (e.g. inner index can't exceed outer on iteration 1), state "infeasible" and continue.
5. Each path starts at entry, ends at exit. The set should be **minimal**.

_Compound vs basic condition counting:_

- Compound-condition tests for a single decision with N elementary conditions = up to **2ᴺ**. To "need >100": use **N=7** (`2⁷=128 > 100`) elementary conditions in one decision.
- Basic-condition tests for that same decision = **2** (all-true row + all-false row suffice).

**Worked example:**

```java
void checkNumbers(int[] numbers) {
  2: for (int i=0; i<numbers.length; i++)
  3:   if (numbers[i] % 2 == 0)        // even?
  4:     if (numbers[i] > 10)          // >10?
  5:       System.out.println(...);
  8: (exit)
}
```

Nodes: 2=loop cond, 3=outer if, 4=inner if, 5=print, 8=exit. Unfold to first repeated node → **minimal boundary-interior set:**

```
1,2,3(F),8                          input []   → exit immediately, no print
1,2,3(T),4(T),5(T),6,7,3(F),8       input [12] → prints "12 is even and >10"
1,2,3(T),4(T),5(F),7,3(F),8         input [2]  → even, not >10, nothing printed
1,2,3(T),4(F),7,3(F),8              input [3]  → odd, nothing printed
```

Note the **first path (loop not entered, empty array)** is mandatory and the most-missed.

**Exam patterns & gotchas:**

- **State the boundary-interior definition exactly** ("every subpath until reaching a repeated node").
- **Don't forget the loop-not-entered path** — always part of the boundary set.
- **Nested loops are out of scope** — only single-loop unfolding needed.
- **Infeasible prefixes:** when a tree prefix can't be satisfied (closest-pair: `i<n` true but `j<n` false on first iteration → contradiction), write "infeasible" with the reason; don't invent inputs.
- **Subsumption facts to quote:**
  - boundary-interior **subsumes branch** (covering every subpath including in-loop branches covers every T/F edge).
  - branch **subsumes statement**; statement does NOT subsume branch.
  - branch does **NOT** subsume compound-condition: `if(a&&b)` with (T,T)→1 and (T,F)→0 gives full branch coverage but never tests (F,T) or (F,F).
  - **basic-condition and branch are incomparable.**
  - **loop-boundary and statement have NO subsumption either way** — see §4 for the both-directions counterexample.
- **MC/DC test count = N+1**, NOT 2ᴺ.

**Cheat sheet — criteria, denominators, subsumption:**

| Criterion            | Obligation (denominator)                            | # tests (rough) | Subsumes                      |
| -------------------- | --------------------------------------------------- | --------------- | ----------------------------- |
| Statement            | each node/basic block                               | —               | (weakest)                     |
| Branch               | each decision edge = **2 × #decisions**             | ≥ #edges        | statement                     |
| Basic condition      | each elem. cond. T & F = **2 × #elem-conds**        | 2 (often)       | — (incomparable w/ branch)    |
| Branch-and-condition | branch ∪ basic-condition                            |                 | branch, basic-cond            |
| Compound condition   | every combination per decision = **≤ 2ᴺ**           | up to 2ᴺ        | branch-and-condition          |
| MC/DC                | 2 obligations per elem. condition                   | **~N+1**        | branch-and-condition          |
| Boundary-interior    | each subpath of CFG unfolded to first repeated node | varies          | branch                        |
| Loop-boundary        | loop runs **0, 1, >1**                              | 3 per loop      | — (incomparable w/ statement) |
| Path / all-paths     | every path                                          | ∞ w/ loops      | everything                    |

**Subsumption ladder (strong → weak):** all-paths ⊃ boundary-interior ⊃ {MC/DC, compound-condition, cyclomatic, LCSAJ} ⊃ branch-and-condition ⊃ branch ⊃ statement; basic-condition and loop-boundary sit at the base, _incomparable_ to branch/statement respectively.

---

## 3. Data Flow Testing

> **Plain words:** Control-flow testing cared about *which lines run*. Data-flow testing cares about *the life of each variable's value*: where it's **set** (given a value) and where it's later **used**. The worry is a broken link between them — e.g. code sets `x` but a bug means a stale or wrong `x` gets used downstream. So we pair up every "here's where `x` is set" with every "here's where that `x` is read", and require tests that actually travel from the set to the use. Vocabulary below is just names for "set" (**definition**), "read" (**use**), and "a route from set to read that doesn't overwrite `x` on the way" (**def-clear path**).

**Key definitions:**

- **Definition** `d_n(x)` ("def"): `x` is _given a value_ at node n — the left-hand side of `x = …`, a parameter receiving its argument at entry, or reading input into `x`. Parameters count as defined at the entry node.
- **Use** `u_n(x)`: `x`'s value is _read_ (on the right-hand side of an assignment, inside a condition, or as a call argument). Two flavors:
  - **c-use (computation use)** — the value feeds a *computation* or output (an assignment, a `return`, a `print`); attached to a **NODE**. E.g. `return x+10` is a c-use of `x`.
  - **p-use (predicate use)** — the value is used to *decide a branch*; attached to an **EDGE** — and it counts on **both** the True and False out-edges of that decision. E.g. `if(flag)` is a p-use of `flag`.
- **def-clear path w.r.t. `x`** ("w.r.t." = with respect to): a route where none of the _in-between_ nodes reassign or clear `x`. Meaning: the value set at the start is *still the same value* when it reaches the end — the link is intact.
- **`d_m(x)` reaches `u_n(x)`**: there exists a def-clear path from the def at m to the use at n — i.e. the value set at m can actually arrive, unchanged, at the use at n.
- **du-path** (definition-use path, n1…nk): a def-clear path from a *definition* of `x` to a *use* of `x`. Precisely: n1 has a def of `x`, and **either** nk has a c-use and the path is **simple** (no repeated nodes except possibly the endpoints), **or** the last edge has a p-use and the path up to it is **loop-free**.
- A node like `x = x+1` is *both* a **use** of `x` (the old value, on the right) **and** a **def** of `x` (the new value, on the left) — order matters: it reads, then overwrites.

**The recipe (mechanical):**

1. **Draw the CFG**, number nodes, force a single entry/single exit (add an exit edge if a `return` dangles).
2. **Annotate each node**: list `d_i(var)` for every assigned variable, and the uses. Predicate node → p-use on **both** out-edges; assignment/return/print node → c-use in the node.
3. **Build the def-use table**: for every (def, use) pair of the same variable, find a def-clear path connecting them. Each such pair is one **obligation** — a thing some test must exercise. The full list of pairs is your obligation set (the checklist to tick off).
4. **Satisfy a criterion:** the criteria below differ only in *how many* of those def→use pairs you must cover. They range from lazy (`all-defs`: reach *some* use of each def) to thorough (`all-du-paths`: cover *every* route to *every* use). Read the table as "for each definition of `x`, how much must I cover?"

| Criterion                  | Obligation per definition `d(x)`                                                          |
| -------------------------- | ----------------------------------------------------------------------------------------- |
| **all-defs**               | one def-clear path from each def to **some** (any one) use it reaches                     |
| **all-c-uses**             | a def-clear path from each def to **every c-use** it reaches                              |
| **all-p-uses**             | a def-clear path from each def to **every p-use** (both edges) it reaches                 |
| **all-c-uses/some-p-uses** | all c-uses; if a def reaches **no** c-use, then at least one p-use                        |
| **all-p-uses/some-c-uses** | all p-uses; if a def reaches **no** p-use, then at least one c-use                        |
| **all-uses**               | a def-clear path to **every** use (all c-uses AND all p-uses)                             |
| **all-du-paths**           | **every** def-clear du-path (cycle-free / simple-cycle) to every use — may be exponential |

5. **Feasibility check**: drop infeasible paths; you rarely hit 100%.

**Worked example (proves All-C-Uses/Some-P-Uses ⊉ All-P-Uses/Some-C-Uses):**

```
void foo(int x, int y) {        // node 1: d(x), d(y)
  if (x > 0 && y < 0) {         // node 2: p-use of x,y  (edges 2->3 True, 2->4 False)
    if (x > 10) { return; }     // node 3: p-use of x    (edge 3->5)
  } else {
    print(x, y);                // node 4: c-use of x,y
  }
}                               // 5: return, 6: exit (edge 5->6 added for single exit)
```

- Defs: `d_1(x), d_1(y)`. Uses: nodes 2 & 3 are **p-uses**; node 4 holds the **c-uses**.
- **all-p-uses/some-c-uses** satisfied by **1-2-3-5-6**: def-clear to every p-use; NEVER reaches node 4 → **c-uses at 4 missed**.
- **all-c-uses/some-p-uses** satisfied by **1-2-4-6**: def-clear to every c-use; NEVER takes True branch to node 3 → **p-use at 3 missed**.
- Conclusion: suite {1-2-4-6} satisfies all-c-uses/some-p-uses but fails all-p-uses/some-c-uses → **does not subsume.** (Symmetric ⇒ the two are _incomparable_.)

**Worked example #2 (full branch coverage WITHOUT all-defs):**

```
1 int foo(int w, int y) {
2   int x, z = MAX_INT-1;     // d(x), d(z)
3   if (w < 0) 4: x++;  else 6: z++;     // u+d of x / u+d of z
8   if (y < 0) 9: x++;  else 11: z++;    // u+d of x / u+d of z
13  return 0; }
```

Tests **{w=-1, y=1}** and **{w=1, y=-1}** together take both T and F of each `if` ⇒ **full branch coverage**. But the **def of x at line 2** reaching the use at line 9 needs `w≥0` (skip line 4) AND `y<0` — neither test does this. So **all-defs is NOT satisfied** at 100% branch coverage.

**Exam patterns & gotchas:**

- p-use lives on the EDGE (count both T and F edges); c-use lives in the NODE. A predicate node has **no defs** by assumption.
- A node like `x = x + 1` is simultaneously a **c-use** and a **def** of x; that def kills earlier defs through it.
- "all-defs" only needs **some** use per def — easy to satisfy, easy to break with branch coverage.
- all-c-uses and all-p-uses are **incomparable**.
- For "/some" criteria: the "some" clause only fires when a def reaches **zero** uses of the other kind.
- all-du-paths can be exponential; when asked to "list all du-paths," include both branches around a diamond.

**Cheat sheet — criteria table (slide CFG `1:d(x) → {2:u(x),3:u(x)} → 4 → {5:u(x),6}`):**

| Criterion    | Requires                 | Satisfying path(s)        |
| ------------ | ------------------------ | ------------------------- |
| all-defs     | d*1(x) to \_some* use    | `1,2,4,6`                 |
| all-uses     | d_1(x) to u_2, u_3, u_5  | `1,2,4,5,6` + `1,3,4,6`   |
| all-du-paths | every cycle-free du-path | `1,2,4,5,6` + `1,3,4,5,6` |

---

## 4. Subsumption — Master Cheat Sheet

> **Plain words:** "Subsumption" ranks coverage criteria by strength. Saying **A subsumes B** means: *if you've satisfied A, you've automatically satisfied B* — A is the tougher bar, so passing it gets B for free. (Example: branch coverage subsumes statement coverage — take every `if` both ways and you can't help but run every line.) The exam skill is almost always the *opposite* direction: **disprove** a claimed subsumption by inventing one small program + one test suite that satisfies A yet misses B. This section is the toolkit for that.

**Key definitions:**

- **A subsumes B** ("A includes B"): for **every** program P, **every** test suite that satisfies A on P also satisfies B on P. A is then _strictly stronger_. (Note the "for every program" — a single program where A implies B is *not* enough; it must always hold.)
- **Equivalent**: A subsumes B _and_ B subsumes A (they demand the same coverage). **Incomparable**: neither subsumes the other (each can be satisfied while missing something the other requires).
- Caution: subsumption is a _logical_ relation only — "A is stronger on paper". It does **not** guarantee A finds more real bugs in practice.

**The recipe — to disprove "A subsumes B", find ONE program P + ONE suite T with: T satisfies A on P, but T does NOT satisfy B on P.**

1. Pick the obligation B requires that A does **not**.
2. **Build a tiny program** where that exact obligation can be isolated — a single extra statement, branch, def-use pair, or loop iteration A can skip.
3. **Construct the smallest suite T** meeting all of A's obligations while deliberately avoiding B's distinguishing obligation.
4. **Verify both claims explicitly**: (a) T satisfies A (enumerate A's obligations, show each met); (b) T misses ≥1 of B's obligations (name it).
5. For "no subsumption in BOTH directions" (incomparability), repeat with a **second** program/suite swapping roles.

**Worked example (loop-boundary ⇎ statement, both directions):**

```
1 int foo(int x, int y) {
2   while (x > 0)
3     x--;
4   if (y == 0)
5     return x;
6   return y; }
```

_Direction 1 (loop-boundary adequate, NOT statement adequate):_ suite `foo(0,0)` (loop 0×), `foo(1,0)` (1×), `foo(2,0)` (>1×). All keep `y==0` ⇒ **statement 6 never executed** ⇒ loop-boundary ⊉ statement.
_Direction 2 (statement adequate, NOT loop-boundary adequate):_ suite `foo(0,0)` (loop 0×, hits line 5) + `foo(1,1)` (loop 1×, hits line 6). **Every statement** executed, but loop **never runs >1** ⇒ statement ⊉ loop-boundary. The two are **incomparable**.

**Exam patterns & gotchas:**

- The counterexample MUST include **both code and the explicit suite**; state for each test which obligation it covers.
- Branch = "all-edges"; statement = "all-nodes"; decision ≡ branch. Branch subsumes statement; **statement does NOT subsume branch** (an `if` with no else).
- **MC/DC subsumes branch.** **Basic-condition vs branch: incomparable.**
- **Boundary-interior subsumes branch.**
- **Loop-boundary (0,1,many) is at the BASE** — incomparable with statement; do not confuse with boundary-interior.

**Cheat sheet — BOTH diagrams (A → B means "A subsumes B", i.e. A stronger):**

STRUCTURAL hierarchy:

```
            Path  +  Boundary-Interior            (top: theoretical, often infeasible)
                       |
        +--------------+---------------+
        |              |               |
   Cyclomatic       MC/DC        LCSAJ / Compound-condition
        |              |
        +------ Branch-and-condition ------+
                       |
                    Branch  (= all-edges = decision)
                       |
        +--------------+--------------+
        |                             |
    Statement                  Basic-condition          Loop-boundary
   (= all-nodes)               (incomparable                (0,1,many;
                                with branch)            incomparable w/ statement)
```

Core spine: **Path ⊃ … ⊃ MC/DC ⊃ Branch-and-condition ⊃ Branch ⊃ Statement.** Branch ⊃ Statement is tested most.

DATAFLOW hierarchy (Rapps–Weyuker "includes"); top = strongest:

```
                         All-Paths
                        /    |     \
              All-DU-Paths   |    Required k-Tuples
                   |         |          |
                All-Uses     |          |
                /       \     |          |
  All-C-Uses/      All-P-Uses/Some-C-Uses
  Some-P-Uses          /        \        |
        \             /          \       |
         \           /        All-P-Uses |
          \         /              |
          All-Defs            All-Edges (branch)
                                   |
                              All-Nodes (statement)
```

Linear reading (⊃ = subsumes): **all-paths ⊃ all-du-paths ⊃ all-uses ⊃ {all-c-uses/some-p-uses, all-p-uses/some-c-uses} ⊃ {all-c-uses, all-defs, all-p-uses} ⊃ all-branches ⊃ all-statements.** Note: **all-c-uses and all-p-uses are incomparable**; **all-c-uses/some-p-uses and all-p-uses/some-c-uses are incomparable**; all-p-uses subsumes all-edges.

**Quick disproof template:** _"To show A does not subsume B: program P = [smallest code isolating B's extra obligation]; suite T = [tests meeting every A-obligation]. T satisfies A because [list A-obligations, each met]. T fails B because it never [the B-obligation A is blind to — an unexecuted statement / untaken edge / unexercised def-use pair / a loop iteration count]. Hence A ⊉ B."_

---

## 5. Combinatorial / Pairwise Testing (AETG & IPO/IPOG)

> **Plain words:** Suppose a feature has several settings (parameters), each with a few possible values — say Table ∈ {Coffee, Desk, Kitchen}, Color ∈ {Brown, White, Red}, Size ∈ {Small, Medium}. Testing *every* combination is `3×3×2 = 18` tests here, and explodes fast with more parameters. The insight behind **pairwise (2-way) testing**: most bugs are triggered by *one* setting or the *interaction of two* settings, rarely by three-plus at once. So we don't need every full combination — we only need every **pair** of values (from any two parameters) to appear together in *at least one* test. That collapses the suite dramatically (often to a handful of tests) while still catching the vast majority of interaction bugs. **AETG** and **IPO/IPOG** are two algorithms that build such a small test set.

### What you're GIVEN and what you PRODUCE

- **Given:** a list of **parameters**, and for each one its **set of allowed values** (its "domain"). ⚠️ **Parameters can have any number of values, and different counts each** — e.g. P1 has 3 values, P2 has 3, P3 has 2. This is normal and the exams test it deliberately. There is **no special formula** for the multi-valued case — the mechanics below are identical; the only effect of a bigger domain is *more pairs to cover* and *uneven pair counts* when you tally.
- **Produce:** a small set of **tests** (each test = one value chosen for *every* parameter) such that for **every pair of parameters**, **every** combination of one value from each appears in **at least one** test.

**Key definitions.**

- **t-way / pairwise (t=2):** for every group of `t` parameters, every value-combination of those `t` appears in ≥1 test. Pairwise is the `t=2` case (every *pair*). "At least once" — it does **not** need to be balanced/equal counts.
- **Pair:** a specific (value-of-Pi, value-of-Pj) with i≠j. E.g. `(Table=Coffee, Size=Small)`. Pairs are always across **two different** parameters.
- **π (pi) = the set of pairs still _uncovered_.** This is your running checklist / bookkeeping object. The moment a test covers a pair, cross it off π. **You stop when π is empty** — every pair covered. Keeping π correct is where most exam marks are won or lost.
- **Covering array `CA(N; t, k, v)`:** the produced test set — `N` tests, `k` parameters, `v` values, covering all `t`-way combos. Its size grows only **logarithmically in the number of parameters** (why pairwise scales so well).
- **Orthogonal array `L_Runs(Levels^Factors)`** e.g. `L4(2³)` = 4 runs, 3 factors, 2 levels. Like a covering array but *stronger/balanced*: **every pair appears the exact same number of times.** Sometimes handed to you as a ready-made starting seed (see "Orthogonal-array seed" below).

### First skill: "list all pairs to add when extending to a new parameter"

A very common sub-question: "you already have a pairwise set covering P1, P2; now add a new parameter P3 — list all pairs that must be covered." **Answer = only the pairs that involve the new parameter** (the P1–P2 pairs are already done, don't re-list them). That is: every value of P3 × every value of each existing parameter.

> **Formula:** pairs to add = `Σ over each existing Pj of ( |Pj| × |P3| )`.
> **Example (multi-valued):** P1={Coffee,Desk} (2), P2={Brown,White,Red} (3), new P3={S,M,L} (3) → P1×P3 = `2×3 = 6` pairs + P2×P3 = `3×3 = 9` pairs = **15 pairs** to add.

**AETG — the recipe** _(builds one complete test at a time, greedy)_:

1. **Build π** = every pair across every parameter-pair. Count = `Σ_{i<j} |Pi|·|Pj|`. (Optional binary convention: seed with all-0s / all-1s tests first and remove their pairs.)
2. **Repeat until π is empty.** Each pass builds exactly ONE new test:
3. **Pick the first (parameter, value):** the one appearing in the **most remaining pairs of π**. In practice: tally, for each parameter-value, how many uncovered pairs still contain it (an "occurrence count" table), and take the max. Ties → first in listed order.
4. **Generate `m` candidate tests.** Each candidate fills the *remaining* parameters in some **order** (given by the question, or random). `m` is a knob (e.g. m=1 or m=3).
5. **Greedy per-parameter fill:** going through that candidate's order, for each next parameter choose the **value that forms the most pairs still in π with the values already fixed so far.** ⚠️ Only look **back** at already-assigned parameters, never ahead. Ties → first value. *(Multi-valued changes nothing here — you simply have more values to try; count each and take the max.)*
6. **Score each finished candidate** = total pairs in π it covers (re-count over the *whole* test).
7. **Keep the max-score candidate** (ties → first); add it as a test, remove all its pairs from π. Back to step 2.

**IPO / IPOG — the recipe** _(adds one parameter at a time; deterministic)_:

1. **Initialization:** write out the **full** set of tests covering all pairs of the first two parameters (P1×P2 = every combination).
2. **For each next parameter Pᵢ (P3, then P4, …):**
   - **a. Build π** = all pairs `(value of an earlier parameter Pj, value of Pᵢ)` — i.e. exactly the "pairs involving the new parameter" from the skill above.
   - **b. Horizontal growth:** go down the **existing** tests and *append* a value of Pᵢ to each one, choosing the Pᵢ-value that covers the **most pairs still in π** (ties → first). Remove covered pairs from π after each. *(You have at most as many existing tests as rows; if Pᵢ has more values than there are rows, some values only get placed in vertical growth.)*
   - **c. Vertical growth:** whatever pairs remain in π after horizontal growth get their **own new tests**. For each leftover pair `(Pj=a, Pᵢ=b)`: if there's already a vertical-growth row you can complete (its Pj slot is `a` or blank, its Pᵢ slot is `b` or blank), fill the blanks; **otherwise add a brand-new row** with `Pj=a, Pᵢ=b` and **`*` (don't-care / "any value")** in every other position.
   - **d.** Replace leftover `*` with any valid value, then move to the next parameter.

**Worked example A — binary AETG (counting candidates).** 4 binary params; after 3 tests, π has 7 pairs left:

```
π = { p0p1:(1,0) ; p0p2:(1,1) ; p0p3:(1,1) ; p1p2:(0,0),(1,1) ; p1p3:(0,1) ; p2p3:(1,1) }   (7 pairs)
```

First fixed (in most pairs): **p2=1**. Two candidate orders:

- **Candidate 1, order p2,p1,p0,p3:** p1=1 (covers p1p2), p0=1 (covers p0p2), p3=1 (covers p0p3, p2p3) → test `(1,1,1,1)`, **new pairs = 4**.
- **Candidate 2, order p2,p0,p3,p1:** p0=1 (p0p2), p3=1 (p0p3, p2p3), p1=0 (p0p1, p1p3) → test `(1,0,1,1)`, **new pairs = 5**.
- **Chosen: Candidate 2 (5 > 4).** Resulting `π = { p1p2:(0,0), p1p2:(1,1) }` (2 left).

**Worked example B — multi-valued AETG (uneven domains).** P1={C,D,K} (3 values), P2={B,W,R} (3), P3={S,M} (2). Starting fresh, first test already fixed to P1=**C**.

- Fill P3 (order P1,P3,P2): with P1=C fixed, P3=S covers pair (C,S)=1, P3=M covers (C,M)=1 — **tie → pick S**.
- Fill P2: with (C,S) fixed, B covers {(C,B),(B,S)}=2, W covers 2, R covers 2 — **tie → pick B**.
- Test = **(C, B, S)**, covering 3 new pairs. ⇒ Multi-valued is purely mechanical: enumerate values, tally pairs, take the max, break ties by listed order. Bigger domains just mean more values to try and more pairs to eventually cover.

**Special-parameter twists** (recurring "adapt the algorithm" sub-questions):

- **Fault-prone parameter — "each value of P3 must appear ≥ twice with every other value":** change π construction — **put every pair that involves P3 into π twice**; leave the other pairs at multiplicity one. Run growth/greedy normally, but **remove only ONE copy** of a doubled pair each time a test covers it — so the pair must be covered twice before it leaves π. (Works for both IPO and AETG. Do **not** try to reason about final test counts; manipulating π is the clean way.)
- **Critical parameter — "(P2,1) must appear in ≥ 75% of tests":** this is a *frequency* constraint, not a pair constraint, so **don't fiddle with π counts** (you don't know the final test count in advance). Instead, in AETG: when choosing the first (param,value) of each new test, if (P2,1) is currently in < 75% of tests so far, **force-select it**; and after all pairs are covered, keep **adding redundant tests containing (P2,1)** until the 75% threshold is met.
- **Orthogonal-array seed:** if you're handed an orthogonal array (or any set of prebuilt tests), use it as the **starting tests**: build the full pair list, **strike out every pair those seed tests already cover**, then run AETG/IPO only on what's left → far fewer iterations. (Note: naively *duplicating* an OA's columns to fake more parameters does **not** cover the cross-half pairs — a classic "why doesn't this work" question.)

**Exam patterns & gotchas.**

- **m=1 vs m=3:** larger `m` → more candidates per step → **fewer total tests** but **more computation**. m=1 is fast but yields a bigger suite. AETG is **non-deterministic** (random orders); IPOG is **deterministic**.
- **Multi-valued parameters are not special** — no formula changes. The only visible effect: uneven pair counts (a 3-value parameter shows up in more pairs than a 2-value one), so occurrence tallies come out lopsided. Just count carefully.
- **Counting traps (#1 point-loser):** (a) when picking a value, count pairs only against **already-assigned** parameters; (b) a pair scores only if it's **still in π**; (c) re-count the candidate's score over the **whole** finished test; (d) in IPO, try to **reuse a `*`/blank row before adding a new one**; (e) **remove covered pairs from π after every assignment** — forgetting this double-counts.
- **"List all pairs for a new parameter" = only pairs involving that parameter** (see the formula above). Don't re-list already-covered pairs.

**Cheat sheet — AETG vs IPOG:**

|                     | **AETG**                                       | **IPO / IPOG**                       |
| ------------------- | ---------------------------------------------- | ------------------------------------ |
| Unit added per step | one complete test                              | one parameter                        |
| Strategy            | greedy, m candidates, keep best                | init → horizontal → vertical growth  |
| Determinism         | non-deterministic                              | deterministic                        |
| Complexity          | higher                                         | lower                                |
| Flexibility         | —                                              | extend existing set; `*` don't-cares |
| Knob                | m = #candidates (bigger → fewer tests, slower) | —                                    |

---

## 6. Symbolic Execution

> **Plain words:** Instead of running the program on *actual numbers*, run it on *symbols* that stand for "any input". As you walk one path through the code, you track two things: **PV** = what each variable now equals *in terms of those symbols* (e.g. `c1 = X*X`), and **PC** = the list of conditions the inputs must satisfy to have taken this exact path (e.g. `X > Y`). At the end, the PC is a set of equations; if a solver can find numbers satisfying it, those numbers are a real test input that drives this path — and if the PC is contradictory (unsatisfiable), the path is **impossible** and needs no test. This is how you prove things like "this ERROR line can never be reached".

**Key definitions.**

- **Symbolic value** — instead of a concrete number, each input is given an uppercase symbol standing for "whatever the caller passes" (`x→X`, `arr→A`, its length → `SIZE_OF_A`). Literal constants (like `1`, `0`) stay as themselves.
- **Symbolic state / PV (Program Variables)** — the current value of every variable written as a formula in those symbols. An **assignment** updates PV (e.g. after `c1 = x*x`, PV has `c1 = X*X`); it never touches the PC.
- **Path condition (PC)** — the running list of branch conditions joined by AND (`/\`), recording what must be true to follow this path. Taking a branch's **True** side appends the condition; taking the **False** side appends its **negation** (`!condition`).
- **Feasibility / SAT** — a path is *feasible* (a real input can follow it) exactly when its PC is **satisfiable**. You hand the PC to a constraint solver, which answers **SAT** (+ a concrete example — "here are numbers that work"), **UNSAT** (no numbers can satisfy it), **UNKNOWN**, or **TIMEOUT**. UNSAT ⇒ path infeasible ⇒ that code is unreachable via this path.
- **Reaching ERROR** — to check whether a specific `ERROR` line can run, AND together the conditions of exactly the branches on the route to it, and test that PC for satisfiability.

**The recipe — columns `line | PV | PC`:**

1. **Entry:** bind every parameter to its symbol in PV. PC empty.
2. **Assignment:** update only PV (substitute current symbols), e.g. `c1 = X*X`.
3. **Branch:** nothing in PV; append constraint to PC with `/\`. **Convention: take the FALSE branch first**, then negate that last constraint to flip to True on the next run. Simplify and say so (`X != X+1 ≡ TRUE`, `X == X+1 ≡ FALSE`).
4. **Return/ERROR:** write symbolic return value in PV, or mark `ERROR`.
5. After each run: state the **symbolic return value** and the **full PC**; then negate the last branch and re-run.

**Worked example — unreachable ERROR:**

```
void foo(double x){ c1 = x*x; if (c1+1==0){ if (c1-1==0){ ERROR; }}}
```

| line  | PV        | PC                           |
| ----- | --------- | ---------------------------- |
| entry | x = X     |                              |
| c1    | c1 = X\*X |                              |
| if1   |           | X\*X + 1 == 0                |
| if2   |           | X*X + 1 == 0 /\ X*X - 1 == 0 |

- **Full PC to ERROR:** `X*X + 1 == 0 /\ X*X - 1 == 0`.
- **Reachable? NO.** `X*X + 1 == 0` forces `X*X = -1`, impossible for real X (would need imaginary `i`); also both `v+1==0` and `v-1==0` can't hold at once. Canonical **unreachable-error** pattern.
- **Branch-coverage denominator:** two `if`s ⇒ `2 × 2 = 4`.

**Worked example — false-branch-first:**

```
runSymbolic(int x,int y){ if(x>y) x=y+1; else y=x+1; if(x==y) ERROR; return x+y; }
```

Run 1 (false branch first ⇒ `X<=Y`, line `y=x+1` runs):
| line | PV | PC |
|---|---|---|
| entry | x=X, y=Y | |
| if1(F) | | X <= Y |
| y=x+1 | y = X+1 | |
| if2(F) | | X <= Y /\ X != X+1 ≡ X <= Y |
| return | 2\*X + 1 | |

Symbolic return `2*X+1`, PC `X <= Y`. Negate last → aim at ERROR: PC becomes `X <= Y /\ X == X+1 ≡ FALSE` ⇒ **infeasible**, ERROR unreachable on this branch.

**Exam patterns & gotchas.**

- **Branch denominator** = `2 × #decisions` (loop conditions count).
- **Unreachable errors:** spot UNSAT PCs — `x*x+1==0`, `v+1==0 /\ v-1==0`, `x>0 /\ y>0 /\ x+y<0`. Answer "not reachable" + algebraic reason; never invent an input.
- **Satisfying input:** if SAT, give one concrete tuple (for `X<=Y`: `x=0,y=0`). Out-of-bounds example: bug `arr[b+1]` at `b==3` ⇒ out-of-bounds read at index 4.
- **MC/DC variant:** build MC/DC cases first, then one symbolic run per case, adding each basic condition's required truth value to the PC. For `a /\ b /\ c`: runs `a/\b/\c`, `!a/\b/\c`, `a/\!b/\c`, `a/\b/\!c`. If MC/DC impossible for a condition, fall back to ordinary symbolic execution.
- Assignments update PV only; branches update PC only — never both on one row.

**Cheat sheet.**

- Columns `line | PV | PC`. Conjunction `/\`, negation `!`/`¬`. Inputs UPPERCASE; array length `SIZE_OF_A`.
- **False branch first**; negate-last-constraint to explore sibling; simplify & state equivalences; always write explicit symbolic return + full PC; give satisfying input only when SAT.
- Branch denominator = `2 × #decisions`.

---

## 7. Concolic Testing (DART & CUTE)

> **Plain words:** Pure symbolic execution (§6) breaks down when the maths gets too hard for the solver — a non-linear formula, a function whose source you don't have, a messy pointer. Concolic testing fixes this by running the program on **real inputs and symbols at the same time** ("**conc**rete + symb**olic**" = concolic). It keeps the symbolic PC to reason about paths, but whenever the solver gets stuck it just plugs in the *actual concrete value* from the real run and moves on. To reach a new path it takes the last branch condition and flips it, then asks the solver for an input satisfying the flipped condition — repeat until you hit the target (e.g. ERROR).

**Key definitions.**

- **Concolic = concrete + symbolic, side by side.** The real (concrete) values keep the program running; the symbolic side reasons about paths. When the solver can't cope (an opaque/non-linear function, a pointer), you **fall back to the concrete value** instead of getting stuck.
- **DART (Directed Automated Random Testing)** — start from random inputs, record the branch conditions hit, then negate them one at a time to steer execution down not-yet-taken paths. For a black-box function it just substitutes the concrete number the function actually returned.
- **CUTE (Concolic Unit Testing Engine)** — extends this to pointers and dynamic data structures (linked lists, trees) using **logical addresses**: rather than reasoning about raw memory addresses (which change run to run), it treats "same value ⇒ same logical location". NULL tests become symbolic constraints like `P==NULL`, `PN==NULL`.
- **Pointer symbol notation** (how a pointer chain maps to symbols): `p→P`, `p->v→PV` (the value field), `p->next→PN` (the next pointer), `p->next->v→PNV`, `p->next->next→PNN`, … — i.e. append a letter per field you follow.

**The recipe — columns `line | concrete state | PV (symbolic) | PC`:**

1. **Pick initial input** —
   - **Linked-list / int-from-zero:** first random int starts at **0**, increment by 1 until the PC holds; pointers start `NULL`.
   - **Black-box arithmetic:** initial `x,y = 1`.
2. **Run the table:** concrete column = real values / data-structure graph; PV = symbols; PC appends each branch constraint with `/\`, mark `(True)/(False)`. Black-box `result = f(x)`: PV gets token `THIRD_PARTY_FUNCTION`; concrete column gets the _actual computed number_.
3. **Report:** concrete input, concrete output, symbolic PC.
4. **Negate the last branch constraint**, solve for next input (increment int from 0 until PC holds; grow list by one cell when `->next != NULL` needed).
5. **Repeat until ERROR.** Linked-list NULL-check ⇒ **4 iterations**; black-box equality ⇒ **2 tables**.

**Worked example — CUTE, logical addresses, start ints at 0, 4 iterations:**

```
void bar(cell* p){ if (p==NULL || p->next==NULL) return; if (p->v > p->next->v) ERROR; }
```

| iter | concrete                   | PC                                                           |
| ---- | -------------------------- | ------------------------------------------------------------ |
| 1    | `p=NULL`                   | `P == NULL` (True) → return                                  |
| 2    | 1-cell list (`next=NULL`)  | `P==NULL \|\| PN==NULL` (True) → return                      |
| 3    | 2-cell list, both non-null | `P==NULL \|\| PN==NULL` (False); `PV > PNV` (False) → return |
| 4    | 2-cell, `PV=1, PNV=0`      | `...` (False); `PV > PNV` (True) → **ERROR**                 |

Final PC to ERROR: `P != NULL /\ PN != NULL /\ PV > PNV`. (A variant has the same shape with inner `(PV-PNV)²>4`; the non-linear term is exactly where the **concrete** value is needed — pick `PV=3, PNV=0` so `9>4` ⇒ ERROR.)

**Worked example — black-box `thirdPartyFunction` (start x,y=1, 2 tables):**

```
computeResult(x,y){ result = thirdPartyFunction(x); if (result==y) ERROR; return result; }
// hidden: 100x³+200x²+300x+20346
```

- **Table 1** `x=1, y=1`: engine runs f for real → concrete `result = 20346`; PV token `THIRD_PARTY_FUNCTION`; PC `THIRD_PARTY_FUNCTION != Y`; returns 20346.
- Negate ⇒ need `THIRD_PARTY_FUNCTION == Y`; solver can't invert the opaque function, so **reuse the concrete output**: set `y = 20346, x = 1`.
- **Table 2** `x=1, y=20346`: `result=20346`, PC `THIRD_PARTY_FUNCTION == Y` → **ERROR**. Input `(1, 20346)`.

**Exam patterns & gotchas.**

- **Basic-condition denominator** = `2 × #atomic conditions`. `bar` has 3 atoms ⇒ **6**.
- **Full branch coverage without full basic-condition coverage:** possible — `p==NULL || p->next==NULL` can have both branches covered without ever making `p->next==NULL` true alone.
- **Iterations:** NULL-check list ⇒ 4; black-box equality ⇒ 2 tables. (4 is the suggested count; other counts can be acceptable.)
- **Black-box/non-linear:** keep a symbolic token, fill concrete column with the real value, and reuse that concrete value as the next input when inverting. Never algebraically solve the opaque function.
- **Choose the initial input by convention:** 0-and-increment for lists, 1 for black-box; pointers start NULL.
- Always **negate the last constraint** (not an earlier one); grow the structure by one node when the negated constraint needs a non-null `next`.

**Cheat sheet.**

- Columns `line | concrete | PV | PC`. `/\` conj, `||` disj, mark `(True)/(False)`.
- Pointer symbols `P, PV, PN, PNV, PNN, …`; black-box token `THIRD_PARTY_FUNCTION`.
- Per iteration write: concrete input, concrete output, symbolic PC, how next input is chosen.
- Random ints start **0** (lists) or **1** (black-box); pointers NULL; iterate negate→resolve until ERROR.
- Basic-condition denominator = `2 × #atomic conditions`.

---

## 8. FSM-based Testing (UIO, DS, W-set)

> **Plain words:** Some systems have *memory* — the same input does different things depending on what happened before (a vending machine, a login flow). We model these as a **Finite State Machine (FSM)**: a set of states with labelled transitions ("on input `a`, go from state s0 to s1 and output 0"). To test such a system you need to confirm it's really *in* the state you think it is. The three tools all answer "which state am I in?" by feeding inputs and watching outputs: a **UIO** is a fingerprint for *one* state, a **DS** is a single fingerprint that identifies *every* state at once, and a **W-set** is a *collection* of short inputs that together tell all states apart. UIO and DS don't always exist; a W-set always does (for a well-behaved FSM).

**Key definitions.**

- **Mealy FSM** = ⟨S, I, O, s₀, δ, λ⟩ — states S, inputs I, outputs O, start state s₀, a next-state function δ (state+input→state), an output function λ (state+input→output). "Mealy" means the output is produced **on the transition** (it depends on both the current state and the input), not just on the state.
- **Four assumed properties:** **completely specified** (every state has a defined transition & output for every input — δ,λ are "total"), **deterministic** (one input → exactly one next state), **reduced** (no two states behave identically — otherwise you couldn't tell them apart), **strongly connected** (you can get from any state to any other). The UIO/DS/W theory assumes *reduced*.
- **UIO (Unique Input-Output) for state sᵢ** — an input sequence whose *output* is **different from what every other state would produce** on that same sequence. So observing that output proves "I was in sᵢ" — a fingerprint for one state. An FSM "has a UIO" only if **every** state has one.
- **Distinguishing Sequence (DS)** — one *single* input sequence that yields a **different output for every state** — one fingerprint that identifies all states at once. A DS ⇒ every state trivially has a UIO. Not every reduced FSM has a DS.
- **Characterizing set W** — a *set* of sequences {w₁,…,wₖ} that **together** tell all states apart (no single one has to; the combination does). Always exists for a reduced FSM. A DS is just the special case where one sequence suffices (|W|=1).
- Key implication (exam favorite): **if even one state has no UIO ⇒ there is no DS** (because a DS would hand every state a UIO). The reverse isn't true.

**The recipes.**

_(a) Find/refute a UIO for sᵢ:_ build a UIO tree of path vectors; apply each input, split states by output, track next-states. Terminal when sᵢ becomes a **singleton** (success — path = UIO), or sᵢ shares (output, next-state) with another state (**dead**), or path **repeats** (loop). No branch yields a singleton ⇒ **sᵢ has no UIO**. Rigorous refutation: for each input, show sᵢ shares the same output AND next-state with another state ⇒ inseparable forever.

_(b) DS tree:_ node = **partition of S into blocks**. Develop on input x: within each block group states by output on x; child blocks = each group's next-states. Prune:

| Rule               | Condition                             | Meaning                              |
| ------------------ | ------------------------------------- | ------------------------------------ |
| **D1 homogeneous** | a block has a **repeated state**      | inseparable → prune (dead)           |
| **D2 singleton**   | **every** block is a singleton        | root→node path **is a DS** (success) |
| **D3 loop**        | child block already on root→node path | prune                                |

First D2 ⇒ DS = that input path. All branches die D1/D3 ⇒ **no DS**.

_(c) Characterizing set W:_ build the output table for short words (length 1, then 2, …); greedily pick words so **every pair of states differs on ≥1 word**; present W + per-state output table; the per-state output **column-vectors must all be distinct**.

_(d) Conformance tests:_ "conformance testing" = checking a real implementation matches the FSM spec. A **transfer sequence** `transfer(sᵢ)` is just a shortest input sequence that drives the machine from the start state s₀ to state sᵢ (so you can reach the state you want to test). Build them with a BFS **spanning tree** from s₀; the collection is the **state cover**. Then `V` is your chosen state-identifier (UIO, DS, or W).
- **State coverage** (verify every state exists): for each sᵢ, run `transfer(sᵢ)·V(sᵢ)` — go to sᵢ, then apply its fingerprint to confirm you're really there.
- **Transition coverage** (verify every transition, stronger): for each edge sᵢ—x→sⱼ, run `transfer(sᵢ)·x·V(sⱼ)` — go to sᵢ, take input `x`, then fingerprint to confirm you landed in the expected sⱼ. Transition coverage ⊋ state coverage (⊋ = strictly stronger). (Weaker alternative: a **transition tour** from s₀ that just walks every edge and checks outputs, without confirming the target state.)

**Worked example 1 — prove no UIO ⇒ no DS.** 3 states, I={a,b}, O={0,1}:

| state | a      | b      |
| ----- | ------ | ------ |
| s0    | s1 / 0 | s2 / 0 |
| s1    | s0 / 1 | s2 / 0 |
| s2    | s1 / 0 | s0 / 1 |

s0 on **a**: s0→(0)s1 and s2→(0)s1 — same output AND next-state ⇒ inseparable. s0 on **b**: s0→(0)s2 and s1→(0)s2 — same. Every UIO starts with a or b; both fail ⇒ **s0 has no UIO ⇒ no UIO ⇒ no DS.** DS tree confirms: both root children homogeneous (D1).
_Change (s2→s0) to b/0:_ the blocking collisions (a: s0,s2→s1/0; b: s0,s1→s2/0) don't involve that edge ⇒ **still no UIO, no DS.** (Always re-check the changed edge first.)

**Worked example 2 — DS exists; show the tree.** 5 states; following branch **aba**:

```
root      [ {0,1,2,3,4} ]
  └─a→    [ {0,2,3}, {1,2} ]
       └─b→ [ {0},{0},{3,4},{3} ]
            └─a→ [ {1},{2},{2},{3},{3} ]   ★ D2 all singletons ⇒ DS = a·b·a
```

Verification (all 5 outputs of `aba` distinct): s0=001, s1=100, s2=101, s3=110, s4=010.

**(b) Minimum DS size for n states.** A DS must give a distinct output string to each of n states; with |O|=m, length L gives ≤ mᴸ strings ⇒ `L ≥ ⌈log_m n⌉`. A safe bound (binary, m=2): **min DS length = ⌈log₂ n⌉ + 1**. → n=5 ⇒ **3**; n=23 ⇒ **5**.

**Worked example 3 — no DS, give W.** FSM: s0 a/0→s1, b/0→s2; s1 a/0→s1, b/1→s1; s2 a/1→s2, b/0→s2.
Root: on **a**, s0,s1 both →s1/0 (D1); on **b**, s0,s2 both →s2/0 (D1) ⇒ **no DS.**
**W = {a, b}** (minimal): _a_ separates {s0,s1} from s2; _b_ separates {s0,s2} from s1. Output vectors s0=(0,0), s1=(0,1), s2=(1,0) — distinct ✓. Dropping either word merges a pair.

**Exam patterns & gotchas.**

- **Prove non-existence rigorously:** give the structural reason — the (output, next-state) **collision** between two states means no input ever separates them; back it with the pruned tree (all branches D1/D3).
- **No UIO ⇒ no DS** (use freely); reverse is false.
- **"Change one label":** re-check whether the changed edge is one of the colliding ones; one label change can create or destroy a DS.
- **Min DS size:** ⌈log_m n⌉ (+1 binary). Memorize n=5→3, n=23→5.
- **No DS ⇒ use W** (always works for reduced FSM); substitute W wherever you'd use the DS in conformance tests.

**Cheat sheet — UIO vs DS vs W:**

|                | UIO                     | DS                     | W                        |
| -------------- | ----------------------- | ---------------------- | ------------------------ | --- | ---------------------- |
| What           | one seq per state       | one seq for all states | a _set_ of seqs          |
| Count          | n seqs (varied lengths) | 1                      | k≥1                      |
| Always exists? | No                      | No                     | **Yes** (reduced FSM)    |
| Built via      | UIO tree                | DS tree                | output table, pair-cover |
| Relation       | DS ⇒ all UIOs           | DS ⇒ each UIO          |                          | W   | =1 ⇒ that word is a DS |

DS-tree pruning: **D1** repeated state in a block = dead; **D2** all singletons = DS found; **D3** repeated block = loop. Conformance: spanning tree → state cover → `transfer·V` per state; transition cover = `transfer(sᵢ)·x·V(sⱼ)` per edge.

---

## 9. Black-box Techniques (ECP, BVA, Decision Tables, Domain)

> **Plain words:** "Black-box" means you pick test inputs from the *specification* alone, without looking at the code inside. The problem is still "too many inputs" — so these techniques are smart ways to choose a few representatives. **ECP:** group inputs that *should be treated the same* and test one from each group. **BVA:** bugs love edges, so test right at and just past the boundaries between groups. **Decision tables:** when the output depends on several yes/no conditions, tabulate the combinations. **Domain testing:** picture the input space as regions separated by boundary lines, and test points *on and just off* each boundary to catch a mis-drawn boundary.

**Key definitions.**

- **Equivalence class / partition (EC):** a group of inputs the program *should* handle identically (e.g. "all ages 18–65"). Split into **valid** and **invalid** groups. Testing one representative per group stands in for the whole group — that's the saving.
- **Boundary value:** a value right at, or just next to, the edge of an equivalence class. Off-by-one and `<` vs `≤` bugs cluster exactly here, so these are high-value tests.
- **Decision table:** a table of conditions (each Y / N / `–` where `–` = "doesn't matter") across the top × **rules** (columns) → resulting actions. `n` conditions give up to `2ⁿ` combinations; combine columns that share the same action using don't-cares (`–`); each surviving column becomes one test case.
- **Category-partition:** a systematic method — break the spec into **categories** (input characteristics) → each into **choices** (the partitions) → add **constraints** to prune nonsense combinations (`[property]`, `[if…]`, `[error]`, `[single]`) → generate **test frames** (concrete combinations).
- **Domain vs computation error:** think of the program as sorting each input into a region ("subdomain") and computing a result for it. A **domain error** = the input took the *wrong region/path* because a **condition** (`if`) is wrong. A **computation error** = right region/path but the *value* computed is wrong because an **assignment** is wrong. A program is thus a **classifier** that partitions the input space into subdomains.
- **Boundary geometry:** a **closed** boundary *includes* its edge points (`≤` / `≥`); an **open** boundary *excludes* them (`<` / `>`). **Adjacent domains** share a boundary; an **extreme point** is where two boundaries cross.
- **Three boundary errors** (ways a boundary line can be coded wrong): **closure** (`≤` written as `<` — right line, wrong include/exclude), **shifted** (right slope, wrong position — wrong constant, e.g. `x+y>5` coded `x+y>4`), **tilted** (wrong slope — wrong coefficient, e.g. `x+y>5` coded `x+0.5y>5`).
- **ON point:** a point lying *exactly on* the boundary (the equality holds). **OFF point:** a point *just off* the boundary — for a **closed** boundary it sits just *outside* (in the adjacent domain); for an **open** boundary it sits just *inside* the domain. (This flip is the #1 thing to get right — see gotchas.)

**The recipe.**

- _ECP:_ range → 1 valid + 2 invalid; set → 1 valid per member + 1 invalid; "must be" → 1 valid + 1 invalid. One test per valid class (combine valids); **one separate test per invalid class** (never combine invalids).
- _BVA:_ for `[a,b]` test `a−ε, a, a+ε, b−ε, b, b+ε` + nominal. Classic `[−10,10]` → `−10.1, −10, 9.9, 10, 10.1`.
- _Decision table:_ `2ⁿ` rules → fill effects → merge don't-care columns → each column = test.
- _Domain (ON–OFF–ON):_ per boundary, two **ON** points (A,B) spread along it + one **OFF** point (C) → sequence A,C,B. Two ONs catch tilt; ON/OFF pair catches shift + closure.

**Worked example.** `discount(qty)`: 0% if `qty<10`, 10% if `10≤qty≤99`, 20% if `qty≥100`; positive int.

- ECP: invalid `qty≤0`; valid `[1,9]`,`[10,99]`,`[100,∞)`.
- BVA: `0,1,9,10,99,100,large`. Boundaries `9|10`, `99|100` hide closure/shift faults.
- Domain: boundary `qty=10` closed on 10%-side; ON=`10` (10%), OFF=`9` (0%). If code wrote `qty>10` (closure error), ON point `10` wrongly gets 0% → caught.

**Exam patterns & gotchas.**

- _Never merge two invalid ECs_ — can't tell which triggered the failure.
- Domain error = conditional fault; computation error = assignment fault. Boundary-interior / ON-OFF target **domain (boundary) errors**.
- **Closed boundary → OFF outside; open boundary → OFF inside** (#1 deduction).
- BVA _extends_ ECP, doesn't replace it.

**Cheat sheet.**

| Concept                        | One-liner                                    |
| ------------------------------ | -------------------------------------------- |
| ECP valid / invalid            | 1 per class, combine / 1 EACH, never combine |
| BVA range [a,b]                | a−ε, a, a+ε, b−ε, b, b+ε, nominal            |
| Decision table                 | rules=2ⁿ, merge don't-cares, 1 col = 1 test  |
| Computation error              | correct path, wrong value (assignment)       |
| Domain error                   | wrong path, faulty predicate                 |
| Closure / shifted / tilted     | `≤↔<` / wrong constant / wrong coefficient   |
| ON / OFF (closed) / OFF (open) | on boundary / just outside / just inside     |
| Criterion                      | ON–OFF–ON (A, C, B) per boundary             |

---

## 10. JUnit & Tooling Reference (Pitest, JaCoCo)

> **Plain words:** This section is the *practical* toolkit — the actual Java tools that implement the ideas above. **JUnit** = the framework you write tests in (an `assert…` that throws if the program misbehaves). **Pitest** = the tool that automates mutation testing from §1 (it plants the mutants and runs your tests against each). **JaCoCo** = the tool that measures coverage from §2 (which lines/branches your tests actually ran). Exam questions here are usually "given this code and these tests, what does the tool report?" — so know how each tool *counts*.

**Key definitions.**

- **JUnit:** the Java unit-test framework. A test does: create the object → set up inputs → state the expected result → run the code → **assert** the result matches. A failed assertion throws `AssertionFailedError`; related tests group into *suites*.
- **Mutant / killed / survived / equivalent** and the **score `100·D/(N−E)`** — all defined in §1.
- **Pitest (PIT):** a JVM mutation-testing tool. It applies its default **mutators** (the tiny changes) to your compiled bytecode and re-runs your test suite once per mutant, reporting which survived.
- **JaCoCo:** a coverage tool. It has several counters (instruction / line / branch / complexity / method / class); the exam cares about **statement (line)** and **branch** coverage. Run with `mvn test jacoco:report`.

**JUnit assertions (write precisely).**

| Assertion                                | Use                                                      |
| ---------------------------------------- | -------------------------------------------------------- |
| `assertEquals(expected, actual)`         | object/primitive equality (`.equals`)                    |
| `assertEquals(expected, actual, delta)`  | **doubles/floats — MUST give a tolerance** (e.g. `1e-9`) |
| `assertTrue(cond)` / `assertFalse(cond)` | booleans                                                 |
| `assertNull` / `assertNotNull`           | null checks                                              |
| `assertSame` / `assertNotSame`           | **reference identity (`==`)**, not value                 |
| `assertArrayEquals(exp, act)`            | array contents                                           |
| `fail(msg)`                              | force failure (unreached-branch guards)                  |

**JaCoCo counters (denominators).**

- **Statement/line:** denominator = executable lines/instructions; a line covered if any instruction ran.
- **Branch:** denominator = branch outcomes = **2 per decision**. JaCoCo counts at **bytecode** → each atomic boolean in `&&`/`||` contributes its own pair. `if(A)` → 2; `if(A && B)` → 4.

**Worked example.** `f(y){ if(y>0) return 2*y; if(y<0) return -3*y; return 0; }` with tests `f(5)=10, f(-2)=6, f(0)=0`:

- `y>0→y>=0`: at `y=0` both return 0 ⇒ **equivalent**. `y<0→y<=0`: at `y=0` both return 0 ⇒ **equivalent**.
- `2*y→2/y`: `f(5)` → `2/5=0≠10` ⇒ **killed**. `-3*y→-3/y`: `f(-2)` → `-3/-2=1≠6` ⇒ **killed**.
- N=4, E=2, D=2 → **score 100×2/(4−2) = 100%**. State the survivors are equivalent; don't "fix" them.

**Exam patterns & gotchas.**

- **CONDITIONALS_BOUNDARY at an untested boundary value → often equivalent.** Always test the equality case to decide.
- `a*b→b*a`, `x+0→x`, mutating unreachable code ⇒ equivalent.
- **100% branch coverage ⇏ all mutants killed** (weak-oracle gap) — the whole point of the "non-trivial assertion that still lets the mutant survive" sub-question.
- Always put the **delta on double `assertEquals`**. Score denominator is **N − E**, never N.

---

## 11. Exam Playbook & Master Cheat Sheets

> **Plain words:** This is the exam-day section — no new theory, just *how to attack a question*. The first table maps a question's shape ("archetype") to the section that answers it, so you can jump straight there. The second table is the single most important thing to get right under pressure: **denominators** — when a question asks for "coverage %" you must state *exactly what is being counted* (lines? edges? conditions?). The last list is the recurring reasons students lose marks.

### Question archetype → topic

| Archetype                                   | What it asks                                                                                                                       | §       |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------- |
| **A Mutation / score**                      | survive vs kill, flag equivalents, `D/(N−E)`, add tests for 100%; or write a weak-assertion test where a mutant survives, then fix | §1, §10 |
| **B AETG pair-count**                       | first param fixed; for each candidate order count new pairs; which wins; resulting π                                               | §5      |
| **C IPO/OA growth**                         | horizontal growth for new param, then which tuples vertical growth adds & why                                                      | §5      |
| **D CFG + boundary-interior**               | draw CFG (number nodes), minimal boundary-interior path set, subsumption vs branch                                                 | §2      |
| **E Dataflow / subsumption counterexample** | "show X does NOT subsume Y — program + suite"                                                                                      | §3, §4  |
| **F Symbolic → ERROR**                      | PC reaching ERROR, feasibility + sample input, false-branch-first, branch denominator                                              | §6      |
| **G Concolic table**                        | concrete+symbolic+PC table over a struct, start int at 0, until ERROR                                                              | §7      |
| **H FSM UIO/DS/W**                          | prove no UIO; DS tree; characterizing set W; min DS size                                                                           | §8      |
| **(I) MC/DC** (sub-part)                    | minimal MC/DC suite (~N+1 tests); pseudocode                                                                                       | §2, §6  |

### Denominators cheat sheet (state EXACTLY what is counted)

| Metric                       | Denominator = number of …                                                           |
| ---------------------------- | ----------------------------------------------------------------------------------- |
| **Statement (line)**         | executable statements/lines (JaCoCo: instructions)                                  |
| **Branch (decision)**        | **2 per decision** (true & false); JaCoCo bytecode → 2 per atomic boolean in `&&`/` |
| **Basic (atomic) condition** | **2 × #atomic conditions**                                                          |
| **Branch-and-condition**     | branch + basic-condition obligations                                                |
| **Compound condition**       | **2ᴺ** combinations of the N atoms in a decision                                    |
| **MC/DC**                    | one independence obligation per atom → suite ≈ **N+1**                              |

Sanity: `if (A && B)` → branch **4**, basic-condition **4**, compound **2²=4**, MC/DC **3** tests.

### Things examiners always deduct for

- **No justification**
- **Counting equivalent mutants in the denominator** / not arguing why a mutant is equivalent / trying to "kill" an equivalent mutant.
- **Including infeasible paths**, or claiming a symbolic path reachable without a satisfying input (or unreachable without proving UNSAT).
- **Wrong branch order in symbolic execution** — convention is **false branch first**.
- **Miscounting pairs in AETG/IPO** (not listing each pair, double-counting covered pairs, wrong candidate).
- **CFG mistakes:** unnumbered nodes, ignoring `&&`/`||` short-circuit as separate branches, non-minimal/loop-not-exercised boundary-interior set.
- **Double `assertEquals` with no delta.** **OFF-point on the wrong side** of an open/closed boundary.
