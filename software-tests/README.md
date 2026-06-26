# Software Tests Summary

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

**Key definitions:**

- **Mutant** — program `Pᵢ` obtained from `P` by _one_ small syntactically-valid change (operator swap, boundary swap, etc.).
- **Killed (dead) mutant** — some test in `T` produces a _different output_ on `Pᵢ` than on `P`. **Survived** — no test distinguishes it.
- **Equivalent mutant** — `Pᵢ` and `P` have identical behavior on _every possible input_; impossible to kill. (General equivalence-detection is **undecidable**.)
- **Mutation score** = `100 × D / (N − E)` — D = killed, N = total mutants, E = equivalent. Equivalents are removed from the **denominator**, never counted as killed.
- **Competent-programmer hypothesis** — real faults are small deviations. **Coupling effect** — tests that catch simple faults also catch complex ones. These justify single-change mutants.
- A mutant survives iff either: no test reaches the mutated line, OR a test reaches it but the _output_ is unchanged (includes equivalents).

**The recipe (per mutant):**

0. **Precondition:** run the suite `T` against the original `P` first — every test must pass. A failing test means **fix `P` and retest**, not a killed mutant. The whole process iterates: after adding tests, re-run until the score clears the chosen threshold.
1. **Locate** the mutated line and the exact change (e.g. `>` → `>=`).
2. **Find a reaching input** that exercises the mutated code AND makes the mutated expression differ from the original (the "infection" step).
3. **Propagate:** check the _return value / output_ actually changes for that input. If for _all_ inputs the output is identical → **equivalent** (add to E). Otherwise it is **killable**.
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

**Key definitions:**

- **CFG nodes:** computation (rectangle, straight-line code), decision (diamond, T/F edges), merge (circle). Single entry, single exit; number every node.
- **Statement (node) coverage** — every node executed once. _Weakest._
- **Branch (edge/decision) coverage** — every decision goes both T and F. **Subsumes statement.**
- **Basic-condition coverage** — every _elementary_ boolean (each `a`, `b` in `a&&b`) takes both T and F. _Incomparable with branch._
- **Branch-and-condition** — both branch AND basic-condition adequacy.
- **Compound-condition** — every _combination_ of basic conditions in a decision (≤ 2ᴺ rows; short-circuit trims).
- **MC/DC** — for _each_ basic condition, two test cases that flip _only that condition_ and flip the _whole decision's_ outcome. ~**N+1** tests for N conditions. (DO-178B / ED-12B.)
- **Boundary-interior** — **unfold the CFG as a tree up to the first repeated node, and provide one feasible path for every subpath of that tree.** Exiting after the first iteration = **boundary** test; ≥2 differing iterations = **interior** test.
- **Loop-boundary adequacy** — run each loop **0, 1, and >1** times.
- **Subsumption:** A subsumes B if every suite satisfying A (on every program) satisfies B.

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

**Key definitions:**

- **Definition** `d_n(x)`: x is _assigned_ at node n (LHS of `=`, parameter binding at entry, input read). Params are defined at the entry line.
- **Use** `u_n(x)`: x is _referenced_ (RHS, predicate, or call argument).
  - **c-use (computation use)** — value feeds a computation/assignment/output; associated with a **NODE**. E.g. `return x+10`.
  - **p-use (predicate use)** — value controls a branch; associated with an **EDGE** (both T and F out-edges of the decision). E.g. `if(flag)`.
- **def-clear path wrt x**: a subpath whose _intermediate_ nodes contain no redefinition/undefinition of x.
- **`d_m(x)` reaches `u_n(x)`**: there is a subpath (m)·p·(n) with p def-clear wrt x.
- **du-path** (n1…nk): n1 has a _global_ def of x, and EITHER nk has a global c-use and the whole path is def-clear & **simple**; OR edge (n*{k-1},nk) has a p-use of x and (n1…n*{k-1}) is def-clear & **loop-free**.
- A node such as `x = x+1` has a c-use of x **and** a def of x.

**The recipe (mechanical):**

1. **Draw the CFG**, number nodes, force a single entry/single exit (add an exit edge if a `return` dangles).
2. **Annotate each node**: list `d_i(var)` for every assigned variable, and the uses. Predicate node → p-use on **both** out-edges; assignment/return/print node → c-use in the node.
3. **Build the def-use table**: for every (def, use) pair of the same variable, find a def-clear path. This is the obligation set.
4. **Satisfy a criterion:**

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

**Key definitions:**

- **A subsumes B** ("A includes B"): for **every** program P, **every** test suite that satisfies A on P also satisfies B on P. A is then _strictly stronger_.
- **Equivalent**: A subsumes B and B subsumes A. **Incomparable**: neither subsumes the other.
- Caution: subsumption is a _logical_ relation; it does **not** guarantee better real-world fault detection.

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

**Key definitions.**

- **t-way / pairwise (t=2):** for every group of t parameters, every value combination appears in ≥1 test ("at least once" — _not_ balanced).
- **Covering array CA(N; t, k, v):** N tests, k params, v values, covering all t-way combos; size grows **logarithmically in #params**.
- **Orthogonal array `L_Runs(Levels^Factors)`** e.g. `L4(2³)` = 4 runs, 3 factors, 2 levels; extra property: **every pair appears the same number of times**.
- **π = set of currently _uncovered_ pairs.** The bookkeeping object. Remove a pair the moment a test covers it. Stop when π empty.
- **Conventions to state:** seed all-0s / all-1s first if valid; ties → first value in listed order.

**AETG — the recipe** _(one complete test at a time, greedy)_:

1. **Build π** = all t-way pairs (`Σ_{i<j}|Pi|·|Pj|`). Seed `0000`,`1111`, remove their pairs.
2. **Repeat until π empty.** Each iteration = ONE test:
3. **Fix first (param, value)** = the one in the **most remaining pairs**. Ties → first.
4. **Generate m candidates**, each with a (given/random) **order** of remaining params.
5. **Greedy per-parameter pick:** for the next param, pick the value forming the **most pairs in π with the values already chosen** (only look back at _assigned_ params, never ahead). Ties → first.
6. **Score each finished candidate** = total pairs in π it covers (re-count over whole test).
7. **Choose max-score candidate** (ties → first); add it, remove its pairs from π.

**IPO/IPOG — the recipe** _(one parameter at a time; deterministic)_:

1. **Initialization:** full t-way set for the first t params (e.g. P1×P2).
2. **For each next parameter Pi:**
   a. **π** = all pairs `(value of earlier Pj, value of Pi)`.
   b. **Horizontal growth:** append a Pi-value to **each existing test**, choosing the value covering the **most pairs still in π** (ties → first). Remove covered pairs after each.
   c. **Vertical growth:** for each leftover pair `(Pj=a, Pi=b)`, reuse an existing vertical-growth row whose slots are `a`/`*` and `b`/`*` (fill its blanks); else **add a new row** with `Pj=a, Pi=b` and **`*` (don't-care)** elsewhere.
   d. Replace remaining `*` with any valid value; next parameter.

**Worked example.** 4 binary params; after 3 tests, remaining:

```
π = { p0p1:(1,0) ; p0p2:(1,1) ; p0p3:(1,1) ; p1p2:(0,0),(1,1) ; p1p3:(0,1) ; p2p3:(1,1) }   (7 pairs)
```

First fixed: **p2=1**.

- **Candidate 1, order p2,p1,p0,p3:** p1=1 (covers p1p2), p0=1 (covers p0p2), p3=1 (covers p0p3,p2p3) → test `(1,1,1,1)`, **new pairs = 4**.
- **Candidate 2, order p2,p0,p3,p1:** p0=1 (p0p2), p3=1 (p0p3,p2p3), p1=0 (p0p1,p1p3) → test `(1,0,1,1)`, **new pairs = 5**.
- **Chosen: Candidate 2 (5 > 4).** Resulting `π = { p1p2:(0,0), p1p2:(1,1) }` (2 left).

**Exam patterns & gotchas.**

- **m=1 vs m=3:** larger m → more candidates → **fewer total tests** but **more computation** per step. m=1 fast but bigger suite. AETG is **non-deterministic**; IPOG **deterministic**.
- **"Extend a 2-way set to a new P3 — list all pairs":** answer is **only pairs involving P3** (every P1–P3 and P2–P3 pair). For |P1|=|P2|=3, |P3|=2 → `3·2+3·2 = 12` pairs. Don't re-list P1–P2.
- **Variant (a value must appear ≥ twice):** modify IPO at **π construction** — add each P3-bearing pair **twice** to π; leave P1–P2 pairs at multiplicity one; run growth normally (the doubled pairs force double coverage).
- **Counting traps (#1 point-loser):** count only with _already-assigned_ params; a pair scores only if still in π; re-count the candidate's full-test score; reuse `*`-rows before adding new rows; **remove covered pairs from π after every assignment**.

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

**Key definitions.**

- **Symbolic value** — each input gets an uppercase symbol (`x→X`, `arr→A`, length `SIZE_OF_A`). Constants stay literal.
- **Symbolic state / PV** — current binding of every variable to a symbolic expression. Assignments update PV; never touch PC.
- **Path condition (PC)** — conjunction (`/\`) of branch constraints. True branch adds the condition; False branch adds its **negation**.
- **Feasibility / SAT** — path feasible iff PC satisfiable (solver → SAT+model / UNSAT / UNKNOWN / TIMEOUT). UNSAT ⇒ infeasible ⇒ unreachable.
- **Reaching ERROR** — conjoin the constraints of exactly the branches on the path to ERROR.

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

**Key definitions.**

- **Concolic = concrete + symbolic side by side.** Concrete values drive the run; where the solver can't help (unknown/non-linear function, pointer), the **concrete value is the fallback**.
- **DART** — start random, record branch conditions, negate path conditions one at a time to steer to new paths. Handles a black-box function by substituting its concrete output.
- **CUTE** — pointers/dynamic structures via **logical addresses** (same value ⇒ same logical location). NULL checks → symbolic constraints (`P==NULL`, `PN==NULL`).
- **Pointer symbol notation:** `p→P`, `p->v→PV`, `p->next→PN`, `p->next->v→PNV`, `p->next->next→PNN`, …

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

**Key definitions.**

- **Mealy FSM** = ⟨S, I, O, s₀, δ, λ⟩; output produced _on the transition_ (depends on state and input).
- **Four properties:** **completely specified** (δ,λ total), **deterministic**, **reduced** (no two equivalent states), **strongly connected**. UIO/DS/W theory assumes reduced.
- **UIO for sᵢ** — an input sequence whose output is **different from that of every other state**. An FSM "has a UIO" iff **every** state has one.
- **Distinguishing Sequence (DS)** — a **single** input sequence whose output is distinct for **every** state. DS ⇒ every state has a UIO. Not every reduced FSM has a DS.
- **Characterizing set W** — a set {w₁,…,wₖ} that **collectively** distinguishes all states. Always exists for a reduced FSM. DS = special case |W|=1.
- Key implication (exam favorite): **no UIO for even one state ⇒ no DS.**

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

_(d) Conformance tests:_ BFS spanning tree from s₀ → **state cover** (transfer sequences). **State coverage:** for each sᵢ run `transfer(sᵢ)·V(sᵢ)`, V = UIO/DS/W. **Transition coverage:** for each edge sᵢ—x→sⱼ run `transfer(sᵢ)·x·V(sⱼ)`. Transition coverage ⊋ state coverage. (Alternative: transition tour from s₀ — weaker, checks outputs not target states.)

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

**Key definitions.**

- **Equivalence class (EC):** subset of inputs handled the same; split valid / invalid; one representative tests the class.
- **Boundary value:** at or adjacent to an EC edge; defects cluster here.
- **Decision table:** conditions (Y/N/`–`) × **rules** → actions; `2ⁿ` combos, collapsible with don't-cares; each surviving column = one test.
- **Category-partition:** category (characteristic) → choices (partitions) → constraints (`[property]`,`[if…]`,`[error]`,`[single]`) → test frames.
- **Domain vs computation error:** domain error = wrong _path_ (faulty **predicate**); computation error = correct path, wrong _value_ (faulty **assignment**). A program is a **classifier** partitioning input into subdomains.
- **Boundary geometry:** **closed** = boundary points included (`≤/≥`); **open** = excluded (`</>`); adjacent domains share a boundary; extreme point = boundaries intersect.
- **Three boundary errors:** **closure** (`≤` coded `<`), **shifted** (wrong constant: `x+y>5`→`>4`), **tilted** (wrong coefficient: `x+y>5`→`x+0.5y>5`).
- **ON point:** on the boundary (equality holds). **OFF point:** just off it — for a **closed** boundary, just _outside_ (adjacent domain); for an **open** boundary, just _inside_ the domain.

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

**Key definitions.**

- **JUnit:** instantiate → inputs → expected → execute → **assert**; failed assertion throws `AssertionFailedError`; tests group into suites.
- **Mutant / killed / survived / equivalent** and **score `100·D/(N−E)`** — see §1.
- **Pitest (PIT):** JVM mutation tool; applies default mutators to bytecode, runs your tests per mutant.
- **JaCoCo:** coverage tool; counters instruction/line/branch/complexity/method/class. Exam cares about **statement (line)** and **branch**. Setup: `mvn test jacoco:report`.

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

6 questions, 3 hours, open-book; **recycles the same six archetypes** (one slot occasionally splits into cohort variants). Identify the archetype from the verb in the prompt, jump to the recipe, **show every step with justification** — unjustified answers are explicitly penalized.

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
