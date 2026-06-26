# Feature catalogue

31 features, ordered by exam year. All feature tests pass.

> Note: these solutions are not necessarily the most efficient or clean — this is just how I implemented the features.

## Index

- [2017b86 — implicit-refs : static](#2017b86--implicit-refs--static)
- [2017b86 — proc-ds : dynamic-binding](#2017b86--proc-ds--dynamic-binding)
- [2019b84 — implicit-refs : apply](#2019b84--implicit-refs--apply)
- [2019b84 — let : max](#2019b84--let--max)
- [2021b57 — implicit-refs : switch](#2021b57--implicit-refs--switch)
- [2021b57 — proc-ds : tuples](#2021b57--proc-ds--tuples)
- [2021b78 — explicit-refs : arr](#2021b78--explicit-refs--arr)
- [2021b87 — implicit-refs : generator](#2021b87--implicit-refs--generator)
- [2023b84 — implicit-refs : const](#2023b84--implicit-refs--const)
- [2023b84 — let : exception](#2023b84--let--exception)
- [2023b87 — implicit-refs : letlazy](#2023b87--implicit-refs--letlazy)
- [2023b87 — proc-ds : global](#2023b87--proc-ds--global)
- [2023b99 — implicit-refs : guard](#2023b99--implicit-refs--guard)
- [2023b99 — let : do](#2023b99--let--do)
- [2024b84 — implicit-refs : forproc](#2024b84--implicit-refs--forproc)
- [2024b84 — proc-ds : enum](#2024b84--proc-ds--enum)
- [2024b98 — implicit-refs : multiptr](#2024b98--implicit-refs--multiptr)
- [2024b98 — proc-ds : forsum](#2024b98--proc-ds--forsum)
- [2025b84 — implicit-refs : map](#2025b84--implicit-refs--map)
- [2025b84 — let : cast](#2025b84--let--cast)
- [2025b91 — implicit-refs : overload-proc](#2025b91--implicit-refs--overload-proc)
- [2025b91 — proc-ds : type](#2025b91--proc-ds--type)
- [2025b93 — implicit-refs : uninit-complicated](#2025b93--implicit-refs--uninit-complicated)
- [2025b93 — implicit-refs : uninit-simple](#2025b93--implicit-refs--uninit-simple)
- [2025c93 — implicit-refs : event](#2025c93--implicit-refs--event)
- [2025c93 — proc-ds : foreach](#2025c93--proc-ds--foreach)
- [let : dot](#let--dot)
- [let : poly](#let--poly)
- [proc-ds : cond](#proc-ds--cond)
- [proc-ds : fold](#proc-ds--fold)
- [proc-ds : overload-count](#proc-ds--overload-count)

## 2017b86 — implicit-refs : static

`2017b86-implicit-refs-static.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_proc-static-persists-across-calls_

```
let f = proc(d)
          static c = 0
          begin set c = -(c,-1); c end
in begin (f 0); (f 0); (f 0) end
```
⇒ `3`

Notes:

- static inits are evaluated ONCE at proc-creation (in the def env), not per call.
- each static gets one store ref baked into the closure, so mutations persist across calls.
- here c starts 0; each (f 0) does set c = c+1, so the three calls yield 1,2,3 -> result 3.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -71,8 +71,17 @@
             (value-of body
               (extend-env var (newref v1) env))))
 
-        (proc-exp (var body)
-          (proc-val (procedure var body env)))
+        (proc-exp (var statvars statvals body)
+          (letrec
+            ((inner
+               (lambda (svars svals senv)
+                 (cond
+                   ((and (null? svars) (null? svals)) senv)
+                   ((or (null? svars) (null? svals)) (eopl:error 'proc-exp "static mismatch"))
+                   (else
+                     (inner (cdr svars) (cdr svals)
+                       (extend-env (car svars) (newref (value-of (car svals) env)) senv)))))))
+            (proc-val (procedure var body (inner statvars statvals env)))))
 
         (call-exp (rator rand)
           (let ((proc (expval->proc (value-of rator env)))
--- a/lang.scm
+++ b/lang.scm
@@ -40,8 +40,9 @@
        ("let" identifier "=" expression "in" expression)
        let-exp)
 
+      ;; static variables: proc (id) {static id = exp}* body
       (expression
-       ("proc" "(" identifier ")" expression)
+       ("proc" "(" identifier ")" (arbno "static" identifier "=" expression) expression)
        proc-exp)
 
       (expression
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,20 @@
 in ((f 44) 33)"
 	12)
 
+      ;; static (lexical) variables on proc: evaluated once at proc-creation
+      (proc-static-1 "(proc(x) static y = 5 -(x,y) 12)" 7)
+      ;; note - static inits are evaluated ONCE at proc-creation (in the def env), not per call.
+      ;; note - each static gets one store ref baked into the closure, so mutations persist across calls.
+      ;; note - here c starts 0; each (f 0) does set c = c+1, so the three calls yield 1,2,3 -> result 3.
+      (proc-static-persists-across-calls-put-in-preview
+        "let f = proc(d)
+                   static c = 0
+                   begin set c = -(c,-1); c end
+         in begin (f 0); (f 0); (f 0) end"
+        3)
+      (proc-static-captures-def-env
+        "let a = 3 in let f = proc(x) static s = a -(x,s) in let a = 99 in (f 10)"
+        7)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2017b86 — proc-ds : dynamic-binding

`2017b86-proc-ds-dynamic-binding.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_dynamic-binding_

```
let a = 3
in let p = proc (x) -(x, a)
   in let a = 5
      in -(a, (p 2))
```
⇒ `8`

Notes:

- dynamic scope: a proc's free vars resolve in the CALLER's env, not its definition env.
- here p's free `a` sees the call-site a=5 (not a=3 at definition): (p 2)=-(2,5)=-3, so -(5,-3)=8.
- apply-procedure discards the closure's saved-env and extends the current env instead.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -71,16 +71,16 @@
         (call-exp (rator rand)
           (let ((proc (expval->proc (value-of rator env)))
                 (arg (value-of rand env)))
-            (apply-procedure proc arg)))
+            (apply-procedure proc arg env)))
 
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 79
   (define apply-procedure
-    (lambda (proc1 val)
+    (lambda (proc1 val env)
       (cases proc proc1
         (procedure (var body saved-env)
-          (value-of body (extend-env var val saved-env))))))
+          (value-of body (extend-env var val env))))))
 
   )
--- a/tests.scm
+++ b/tests.scm
@@ -61,17 +61,46 @@
       (let-to-proc-1 "(proc(f)(f 30)  proc(x)-(x,1))" 29)
 
 
-      (nested-procs "((proc (x) proc (y) -(x,y)  5) 6)" -1)
-      (nested-procs2 "let f = proc(x) proc (y) -(x,y) in ((f -(10,5)) 6)"
-        -1)
+      ;; These tests do no work as expected with dynamic binding.
+;;       (nested-procs "((proc (x) proc (y) -(x,y)  5) 6)" -1)
+;;       (nested-procs2 "let f = proc(x) proc (y) -(x,y) in ((f -(10,5)) 6)"
+;;         -1)
+;;       (y-combinator-1 "
+;; let fix =  proc (f)
+;;             let d = proc (x) proc (z) ((f (x x)) z)
+;;             in proc (n) ((f (d d)) n)
+;; in let
+;;     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
+;; in let times4 = (fix t4m)
+;;    in (times4 3)" 12)
 
-      (y-combinator-1 "
-let fix =  proc (f)
-            let d = proc (x) proc (z) ((f (x x)) z)
-            in proc (n) ((f (d d)) n)
-in let
-    t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
-in let times4 = (fix t4m)
-   in (times4 3)" 12)
-      ))
+  ;; note - dynamic scope: a proc's free vars resolve in the CALLER's env, not its definition env.
+  ;; note - here p's free `a` sees the call-site a=5 (not a=3 at definition): (p 2)=-(2,5)=-3, so -(5,-3)=8.
+  ;; note - apply-procedure discards the closure's saved-env and extends the current env instead.
+  (dynamic-binding-put-in-preview
+   "let a = 3
+    in let p = proc (x) -(x, a)
+       in let a = 5
+          in -(a, (p 2))"
+    8
   )
+
+  (fibonacci
+   "let fib = proc (n)
+      if zero?(n) then
+        0
+      else
+        if zero?(-(n,1)) then
+          1
+        else
+          -(
+            (fib -(n,1)),
+            -(0, (fib -(n,2)))
+          )
+    in
+      (fib 7)"
+    13
+  )
+  )
+)
+)
```

[↑ back to top](#feature-catalogue)

## 2019b84 — implicit-refs : apply

`2019b84-implicit-refs-apply.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_apply-force-set_

```
let y = 30
in let p = proc (x) -(x, y)
   in apply y in p during (p 100)
```
⇒ `0`

Notes:

- `apply id1 in id2 during E` rebinds id2 for E only to a proc whose body is `let id1 = <param> in <orig-body>`, so each call to id2 inside E shadows id1 with the call argument.
- The rebinding is scoped to E (the original id2 is restored after); the construct returns the value of E.
- Here calling p shadows y with 100, so -(x,y) = -(100,100) = 0.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -100,7 +100,32 @@
               (value-of exp1 env))
             (num-val 27)))
 
-        )))
+        (apply-exp (id1 id2 exp)
+          (let*
+            (
+              (proc1ref (apply-env env id2))
+              (proc1 (expval->proc (deref proc1ref)))
+            )
+            (cases proc proc1
+              (procedure (pvar pbody penv)
+                (let*
+                  (
+                    (new-proc1
+                      (procedure
+                        pvar
+                        (let-exp id1 (var-exp pvar) pbody)
+                        penv
+                      )
+                    )
+                  )
+                  (value-of exp (extend-env id2 (newref (proc-val new-proc1)) env))
+                )
+              )
+            )
+          )
+        )
+
+      )))
 
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,8 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      (expression ("apply" identifier "in" identifier "during" expression) apply-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,40 @@
 in ((f 44) 33)"
 	12)
 
+      ;; apply <var> in <proc> during <expr>:
+      ;; during evaluation of <expr>, every call to <proc> also force-assigns
+      ;; its argument into <var>; the assignment is scoped to <expr> (reverts
+      ;; afterwards). The construct returns the value of <expr>.
+
+      ;; note - `apply id1 in id2 during E` rebinds id2 for E only to a proc \
+      ;; note -   whose body is `let id1 = <param> in <orig-body>`, so each call \
+      ;; note -   to id2 inside E shadows id1 with the call argument.
+      ;; note - The rebinding is scoped to E (the original id2 is restored after); \
+      ;; note -   the construct returns the value of E.
+      ;; note - Here calling p shadows y with 100, so -(x,y) = -(100,100) = 0.
+      (apply-force-set-put-in-preview "
+let y = 30
+in let p = proc (x) -(x, y)
+   in apply y in p during (p 100)"
+        0)
+
+      ;; scoping: after the during-expr, y reverts to 30, so (p 5) = -(5,30) = -25
+      (apply-scoped-revert "
+let y = 30
+in let p = proc (x) -(x,y)
+   in let dummy = apply y in p during (p 100)
+      in (p 5)"
+        -25)
+
+      ;; worked example: q = 0 (y temp 100 during first apply, then reverts),
+      ;; final apply targets z so y is 30 -> (p 300) = 270 -> -(0,270) = -270
+      (apply-nested-example "
+let z = 10
+in let y = 30
+   in let p = proc (x) -(x,y)
+      in let q = apply y in p during (p 100)
+         in apply z in p during -(q, (p 300))"
+        -270)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2019b84 — let : max

`2019b84-let-max.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_max-over-shadowed-bindings_

```
let m = 4
in let m = zero?(m)
   in let m = 7
      in let m = 5
         in -(max(m), m)
```
⇒ `2`

Notes:

- max(m) returns the largest NUMERIC value among ALL bindings of m currently in scope, not just the innermost one.
- non-numeric bindings of m (e.g. booleans) are skipped.
- if m has no numeric binding in scope, max(m) raises an error.

```diff
--- a/environments.scm
+++ b/environments.scm
@@ -5,7 +5,7 @@
 
   (require "data-structures.scm")
 
-  (provide init-env empty-env extend-env apply-env)
+  (provide init-env empty-env extend-env apply-env empty-env?)
 
 ;;;;;;;;;;;;;;;; initial environment ;;;;;;;;;;;;;;;;
 
--- a/interp.scm
+++ b/interp.scm
@@ -63,9 +63,55 @@
           (let ((val1 (value-of exp1 env)))
             (value-of body
               (extend-env var val1 env))))
+        (max-exp (identifier)
+          (letrec
+            (
+              (num-val?
+                (lambda (v)
+                  (cases expval v
+                    (num-val (num) #t)
+                    (else #f)
+                  )
+                )
+              )
+              (max-loop
+                (lambda (env search-sym)
+                  (if (empty-env? env)
+                    'empty
+                    (let*
+                      (
+                        (sym (extended-env-record->sym env))
+                        (val (extended-env-record->val env))
+                        (old-env (extended-env-record->old-env env))
+                        (next-max (max-loop old-env search-sym))
+                      )
+                      (cond
+                        ((or (not (eqv? search-sym sym)) (not (num-val? val)))
+                          next-max
+                        )
+                        ((equal? next-max 'empty)
+                          val
+                        )
+                        ((> (expval->num val) (expval->num next-max))
+                          val
+                        )
+                        (else
+                          next-max
+                        )
+                      )
+                    )
+                  )
+                )
+              )
+              (result (max-loop env identifier))
+            )
+            (if (equal? result 'empty)
+              (eopl:error "no binding for max")
+              result
+            )
+          )
+        )
 
-        )))
+  )))
+)
 
-
-  )
-
--- a/lang.scm
+++ b/lang.scm
@@ -42,6 +42,8 @@
        ("let" identifier "=" expression "in" expression)
        let-exp)
 
+      (expression ("max" "(" identifier ")") max-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -55,5 +55,21 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
+      ;; note - max(m) returns the largest NUMERIC value among ALL bindings of m
+      ;;        currently in scope, not just the innermost one.
+      ;; note - non-numeric bindings of m (e.g. booleans) are skipped.
+      ;; note - if m has no numeric binding in scope, max(m) raises an error.
+
+      ;; bindings: 4, zero?(4)=#f, 7, 5 -> max numeric = 7; -(7,5) = 2
+      (max-over-shadowed-bindings-put-in-preview "
+let m = 4
+in let m = zero?(m)
+   in let m = 7
+      in let m = 5
+         in -(max(m), m)"
+        2)
+
+      (max-no-numeric-binding "let m = zero?(0) in max(m)" error)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2021b57 — implicit-refs : switch

`2021b57-implicit-refs-switch.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_switch-matches-clause_

```
let k = 5
in switch 5 { number n when (zero?(-(n,k))) => -(n,k)
              boolean b when (b) => 0
              default => 100 }
```
⇒ `0`

Notes:

- picks the FIRST clause whose runtime type matches AND whose guard is true; the clause id is bound to the scrutinee for guard+body.
- a type match with a false guard does NOT stop the scan; it continues to later clauses, then the default.
- an empty clause list (default only) is a "no conditions" error; here 5 is a number and -(5,5)=0 is zero? => clause 1 fires, body -(5,5)=0.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -100,8 +100,39 @@
               (value-of exp1 env))
             (num-val 27)))
 
+        ;; switch
+        (switch-exp (e1 typs ids bools exps defexp)
+          (if (null? typs)
+            (eopl:error 'switch-exp "no conditions")
+            (let ((v1 (value-of e1 env)))
+              (letrec
+                ((loop
+                  (lambda (ts is bs es)
+                    (cond
+                      ((null? ts) (value-of defexp env))
+                      ((eqv? (type-name->symbol (car ts)) (expval->symbol v1))
+                       (let ((new-env (extend-env (car is) (newref v1) env)))
+                         (if (expval->bool (value-of (car bs) new-env))
+                           (value-of (car es) new-env)
+                           (loop (cdr ts) (cdr is) (cdr bs) (cdr es)))))
+                      (else (loop (cdr ts) (cdr is) (cdr bs) (cdr es)))))))
+                (loop typs ids bools exps)))))
+
         )))
 
+  (define expval->symbol
+    (lambda (v)
+      (cases expval v
+        (num-val  (n) 'number)
+        (bool-val (b) 'boolean)
+        (proc-val (p) 'function)
+        (ref-val  (r) 'reference))))
+  (define type-name->symbol
+    (lambda (typ)
+      (cases type-name typ
+        (type-name-number   () 'number)
+        (type-name-boolean  () 'boolean)
+        (type-name-function () 'function))))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 119
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,14 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      ;; switch — first clause whose type matches AND guard holds; else default
+      (expression
+        ("switch" expression "{" (arbno type-name identifier "when" "(" expression ")" "=>" expression) "default" "=>" expression "}")
+        switch-exp)
+      (type-name ("number") type-name-number)
+      (type-name ("boolean") type-name-boolean)
+      (type-name ("function") type-name-function)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,23 @@
 in ((f 44) 33)"
 	12)
 
+      ;; switch — match on runtime type + a guard, else default
+      ;; note - picks the FIRST clause whose runtime type matches AND whose guard is true; the clause id is bound to the scrutinee for guard+body.
+      ;; note - a type match with a false guard does NOT stop the scan; it continues to later clauses, then the default.
+      ;; note - an empty clause list (default only) is a "no conditions" error; here 5 is a number and -(5,5)=0 is zero? => clause 1 fires, body -(5,5)=0.
+      (switch-matches-clause-put-in-preview
+        "let k = 5
+         in switch 5 { number n when (zero?(-(n,k))) => -(n,k)
+                       boolean b when (b) => 0
+                       default => 100 }"
+        0)
+      (switch-falls-to-default
+        "let d = 42
+         in switch zero?(0) { number n when (zero?(n)) => 1
+                              default => d }"
+        42)
+      (switch-no-clauses-errors
+        "switch zero?(0) { default => 1 }" error)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2021b57 — proc-ds : tuples

`2021b57-proc-ds-tuples.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_tuple-swap_

```
let [x, y] = <10, 20> in -(y, x)
```
⇒ `10`

Notes:

- <...> builds a tuple value; let [slots] = tuple destructures positionally.
- a slot is a name to bind or `_` to discard; tuple size must equal slot count (else error).

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -16,7 +16,9 @@
     (bool-val
       (boolean boolean?))
     (proc-val
-      (proc proc?)))
+      (proc proc?))
+    (tuple-val
+      (vals (list-of expval?))))
 
 ;;; extractors:
 
@@ -40,6 +42,13 @@
       (cases expval v
 	(proc-val (proc) proc)
 	(else (expval-extractor-error 'proc v)))))
+
+  ;; expval->tuple : ExpVal -> Listof(ExpVal)
+  (define expval->tuple
+    (lambda (v)
+      (cases expval v
+        (tuple-val (vals) vals)
+        (else (expval-extractor-error 'tuple v)))))
 
   (define expval-extractor-error
     (lambda (variant value)
--- a/interp.scm
+++ b/interp.scm
@@ -59,11 +59,31 @@
               (value-of exp2 env)
               (value-of exp3 env))))
 
-        ;\commentbox{\ma{\theletspecsplit}}
-        (let-exp (var exp1 body)
-          (let ((val1 (value-of exp1 env)))
-            (value-of body
-              (extend-env var val1 env))))
+        ;; tuples — build a tuple value, and let-destructure it ([_] skips a slot)
+        (tuple-exp (exps)
+          (tuple-val (map (lambda (e) (value-of e env)) exps)))
+        (let-exp (target rhs body)
+          (let ((v (value-of rhs env)))
+            (cases let-target target
+              (single-target (id)
+                (value-of body (extend-env id v env)))
+              (multi-target (slots)
+                (letrec
+                  ((bind-all
+                     (lambda (ss vs e)
+                       (cond
+                         ((and (null? ss) (null? vs)) e)
+                         ((or  (null? ss) (null? vs))
+                          (eopl:error 'let-exp
+                            "tuple size doesn't match number of variables"))
+                         (else
+                          (cases slot (car ss)
+                            (wild-slot ()
+                              (bind-all (cdr ss) (cdr vs) e))
+                            (named-slot (id)
+                              (bind-all (cdr ss) (cdr vs)
+                                (extend-env id (car vs) e)))))))))
+                  (value-of body (bind-all slots (expval->tuple v) env)))))))
 
         (proc-exp (var body)
           (proc-val (procedure var body env)))
--- a/lang.scm
+++ b/lang.scm
@@ -36,9 +36,19 @@
 
       (expression (identifier) var-exp)
 
+      ;; tuples — < v1, v2, ... > together with destructuring let
       (expression
-       ("let" identifier "=" expression "in" expression)
+       ("<" (separated-list expression ",") ">")
+       tuple-exp)
+      (expression
+       ("let" let-target "=" expression "in" expression)
        let-exp)
+      (let-target (identifier) single-target)
+      (let-target ("[" (separated-list slot ",") "]") multi-target)
+      ;; a destructuring slot is either a name to bind, or `_` to discard.
+      ;; `_` is a literal terminal here, so it is NOT a general identifier.
+      (slot (identifier) named-slot)
+      (slot ("_") wild-slot)
 
       (expression
        ("proc" "(" identifier ")" expression)
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,16 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;; tuples — < ... >; target is a name OR a bracketed list [ ... ]
+      (let-single   "let x = 3 in -(x, 1)" 2)
+      ;; note - <...> builds a tuple value; let [slots] = tuple destructures positionally.
+      ;; note - a slot is a name to bind or `_` to discard; tuple size must equal slot count (else error).
+      (tuple-swap-put-in-preview   "let [x, y] = <10, 20> in -(y, x)" 10)
+      (tuple-wild   "let [x, _] = <10, 20> in x" 10)
+      (tuple-three  "let [a, b, c] = <1, 2, 3> in -(c, -(b, a))" 2)
+      (tuple-one    "let [x] = <-(8,3)> in x" 5)
+      (tuple-proc   "let [f, n] = <proc (x) -(x,1), 5> in (f n)" 4)
+      (tuple-nested "let [p, q] = <-(9,4), 6> in let [r] = <-(q,p)> in r" 1)
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2021b78 — explicit-refs : arr

`2021b78-explicit-refs-arr.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_arr-mutate_

```
let a = #[3]{1, 2, 3}
in begin
     setref([a, 1], 99);
     deref([a, 1])
   end
```
⇒ `99`

Notes:

- #/?/@ pick the element type (num/bool/proc); every initializer must match or it errors, and the count must equal the declared size.
- [a,i] yields the slot's ref-val itself (not its contents), so you deref it to read and setref it to write; i must be < size.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,7 +19,38 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (arr-val
+      (arr arr?)
+    ))
+
+  (define-datatype arr arr?
+    (array (typename symbol?) (size integer?) (elems (list-of expval?)))
+  )
+
+  (define expval->arr
+    (lambda (v)
+      (cases expval v
+        (arr-val (a) a)
+        (else (expval-extractor-error 'arr v))
+      )
     )
+  )
+
+  (define arr->size
+    (lambda (v)
+      (cases arr v
+        (array (t s e) s)
+      )
+    )
+  )
+
+  (define arr->elems
+    (lambda (v)
+      (cases arr v
+        (array (t s e) e)
+      )
+    )
+  )
 
 ;;; extractors:
 
--- a/interp.scm
+++ b/interp.scm
@@ -108,6 +108,59 @@
               (begin
                 (setref! ref v2)
                 (num-val 23)))))
+
+        (arr-exp (typ size initexps)
+          (let*
+            (
+              (typename (typeexp->typename typ))
+              (sizeval (expval->num (value-of size env)))
+              (elems
+                (map
+                  (lambda (initexp)
+                    (let*
+                      (
+                        (initval (value-of initexp env))
+                      )
+                      (cond
+                        (
+                          (not (equal? typename (expval->typename initval)))
+                          (eopl:error 'value-of "Array initialization mismatch")
+                        )
+                        (else (ref-val (newref initval)))
+                      )
+                    )
+                  )
+                  initexps
+                )
+              )
+              (assert-size
+                (if (not (equal? sizeval (length elems)))
+                  (eopl:error 'value-of "Array initialization mismatch array size")
+                  #t
+                )
+              )
+            )
+            (arr-val (array typename sizeval elems))
+          )
+        )
+
+        (index-exp (arrexp index)
+          (let*
+            (
+              (arr1 (expval->arr (value-of arrexp env)))
+              (index1 (expval->num (value-of index env)))
+              (assert-size
+                (if (>= index1 (arr->size arr1))
+                  (eopl:error 'value-of "Index access out of bounds")
+                )
+              )
+              (refval (list-ref (arr->elems arr1) index1))
+            )
+            refval
+          )
+        )
+
+
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
@@ -120,6 +173,26 @@
   ;;          (value-of body (extend-env bvar arg saved-env))))))
 
   ;; instrumented version
+  (define typeexp->typename
+    (lambda (typeexp)
+      (cases arr-type typeexp
+        (arr-type-num () 'num)
+        (arr-type-bool () 'bool)
+        (arr-type-proc () 'proc)
+      )
+    )
+  )
+  (define expval->typename
+    (lambda (val1)
+      (cases expval val1
+        (num-val (v) 'num)
+        (bool-val (v) 'bool)
+        (proc-val (v) 'proc)
+        (else (eopl:error 'value-of "Wrong array type"))
+      )
+    )
+  )
+
   (define apply-procedure
     (lambda (proc1 arg)
       (cases proc proc1
--- a/lang.scm
+++ b/lang.scm
@@ -72,6 +72,14 @@
         ("setref" "(" expression "," expression ")")
         setref-exp)
 
+      (expression
+        (arr-type "[" expression "]" "{" (separated-list expression ",") "}")
+        arr-exp
+      )
+      (arr-type ("#") arr-type-num)
+      (arr-type ("?") arr-type-bool)
+      (arr-type ("@") arr-type-proc)
+      (expression ("[" expression "," expression "]") index-exp)
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -159,5 +159,31 @@
    end"
    11)
 
+ ;; arrays:  #[size]{...} num,  ?[size]{...} bool,  @[size]{...} proc
+ ;;          [arr, i] indexes a slot, yielding a ref-val (deref/setref it)
+ (arr-read-first  "let a = #[3]{10,20,30} in deref([a, 0])" 10)
+ (arr-read-last   "let a = #[3]{10,20,30} in deref([a, 2])" 30)
+ (arr-read-computed-index "let a = #[3]{10,20,30} in deref([a, -(2,1)])" 20)
+ ;; note - #/?/@ pick the element type (num/bool/proc); every initializer \
+ ;; note -   must match or it errors, and the count must equal the declared size.
+ ;; note - [a,i] yields the slot's ref-val itself (not its contents), so you \
+ ;; note -   deref it to read and setref it to write; i must be < size.
+ (arr-mutate-put-in-preview
+   "let a = #[3]{1, 2, 3}
+    in begin
+         setref([a, 1], 99);
+         deref([a, 1])
+       end"
+   99)
+ (arr-bool        "let a = ?[2]{zero?(0), zero?(1)} in deref([a,0])" #t)
+ (arr-proc        "let a = @[1]{proc(x) -(x,1)} in (deref([a,0]) 5)" 4)
+
+ ;; array error cases (expected result `error`)
+ (arr-err-type-mismatch  "#[2]{1, zero?(0)}" error)        ; bool in a num array
+ (arr-err-size-too-small "#[3]{1, 2}" error)               ; fewer elems than declared
+ (arr-err-size-too-big   "#[1]{1, 2}" error)               ; more elems than declared
+ (arr-err-index-oob      "let a = #[2]{1,2} in deref([a, 2])" error)  ; index == size
+ (arr-err-index-nonarray "[5, 0]" error)                   ; indexing a non-array
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2021b87 — implicit-refs : generator

`2021b87-implicit-refs-generator.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_gen-advances-between-calls_

```
let g = generator(x): [1 2 3] yield -(x,-1)
in -(::g, ::g)
```
⇒ `-1`

Notes:

- ::g pulls the next element (bound to x) and evals the yield body; the cursor is a store ref so it advances/persists across calls. ??g is empty?.
- here ::g => x=1 => -(1,-1)=2, next ::g => x=2 => 3, so -(2,3) = -1.
- pulling past the last element errors ("Generator is empty").

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,6 +19,7 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (gen-val (gen generator?))
     )
 
 ;;; extractors:
@@ -52,6 +53,12 @@
       (eopl:error 'expval-extractors "Looking for a ~s, found ~s"
 	variant value)))
 
+  (define expval->gen
+    (lambda (v)
+      (cases expval v
+        (gen-val (gen) gen)
+        (else (expval-extractor-error 'gen v)))))
+
 ;;;;;;;;;;;;;;;; procedures ;;;;;;;;;;;;;;;;
 
   (define-datatype proc proc?
@@ -59,6 +66,14 @@
       (bvar symbol?)
       (body expression?)
       (env environment?)))
+
+  (define-datatype generator generator?
+    (generator1
+      (var symbol?)
+      (exps (list-of expression?))
+      (retexp expression?)
+      (env environment?)
+      (pos reference?)))           ; store cell holding the current index
 
   (define-datatype environment environment?
     (empty-env)
--- a/interp.scm
+++ b/interp.scm
@@ -100,6 +100,24 @@
               (value-of exp1 env))
             (num-val 27)))
 
+        ;; generator
+        (gen-exp (var exps retexp)
+          (gen-val (generator1 var exps retexp env (newref (num-val 0)))))
+        (return-exp (gen)
+          (cases generator (expval->gen (deref (apply-env env gen)))
+            (generator1 (var exps retexp genv pos)
+              (let ((i (expval->num (deref pos))))
+                (if (>= i (length exps))
+                  (eopl:error 'return-exp "Generator is empty")
+                  (begin
+                    (setref! pos (num-val (+ i 1)))
+                    (value-of retexp
+                      (extend-env var (newref (value-of (list-ref exps i) genv)) genv))))))))
+        (empty-exp (gen)
+          (cases generator (expval->gen (deref (apply-env env gen)))
+            (generator1 (var exps retexp genv pos)
+              (bool-val (>= (expval->num (deref pos)) (length exps))))))
+
         )))
 
 
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,13 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      ;; generator(x): [e ...] yield body ; ::g pulls next ; ??g is empty?
+      (expression
+        ("generator" "(" identifier ")" ":" "[" (arbno expression) "]" "yield" expression)
+        gen-exp)
+      (expression ("::" identifier) return-exp)
+      (expression ("??" identifier) empty-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,17 @@
 in ((f 44) 33)"
 	12)
 
+      ;; note - ::g pulls the next element (bound to x) and evals the yield body; the \
+      ;; note - cursor is a store ref so it advances/persists across calls. ??g is empty?.
+      ;; note - here ::g => x=1 => -(1,-1)=2, next ::g => x=2 => 3, so -(2,3) = -1.
+      ;; note - pulling past the last element errors ("Generator is empty").
+      (gen-advances-between-calls-put-in-preview
+        "let g = generator(x): [1 2 3] yield -(x,-1)
+         in -(::g, ::g)" -1)
+      (gen-empty-after-consuming-all
+        "let g = generator(x): [7 8] yield x in begin ::g; ::g; ??g end" #t)
+      (gen-exhausted-errors
+        "let g = generator(x): [4] yield x in begin ::g; ::g end" error)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2023b84 — implicit-refs : const

`2023b84-implicit-refs-const.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_const-and-mutable-mix_

```
let x = 5
in let const y = 6
   in begin
        set x = 10;
        -(x, y)
      end
```
⇒ `4`

Notes:

- `let const x = ...` (and `(f const v)`) wrap the cell's value in a const-val; reading is transparent but `set` on it errors.
- Plain (non-const) bindings stay mutable, so the two kinds coexist.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,6 +19,7 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (const-val (inner expval?))         ; an immutable binding wraps its value
     )
 
 ;;; extractors:
@@ -51,6 +52,20 @@
     (lambda (variant value)
       (eopl:error 'expval-extractors "Looking for a ~s, found ~s"
 	variant value)))
+
+  ;; const-val? : ExpVal -> Bool
+  (define const-val?
+    (lambda (v)
+      (cases expval v
+        (const-val (inner) #t)
+        (else #f))))
+
+  ;; strip-const : ExpVal -> ExpVal
+  (define strip-const
+    (lambda (v)
+      (cases expval v
+        (const-val (inner) inner)
+        (else v))))
 
 ;;;;;;;;;;;;;;;; procedures ;;;;;;;;;;;;;;;;
 
--- a/interp.scm
+++ b/interp.scm
@@ -39,7 +39,7 @@
 
         ;\commentbox{ (value-of (var-exp \x{}) \r)
         ;              = (deref (apply-env \r \x{}))}
-        (var-exp (var) (deref (apply-env env var)))
+        (var-exp (var) (strip-const (deref (apply-env env var))))
 
         ;\commentbox{\diffspec}
         (diff-exp (exp1 exp2)
@@ -65,18 +65,18 @@
               (value-of exp2 env)
               (value-of exp3 env))))
 
-        ;\commentbox{\ma{\theletspecsplit}}
-        (let-exp (var exp1 body)
+        (let-exp (opt var exp1 body)
           (let ((v1 (value-of exp1 env)))
             (value-of body
-              (extend-env var (newref v1) env))))
+              (extend-env var (newref (if (is-const opt) (const-val v1) v1)) env))))
 
         (proc-exp (var body)
           (proc-val (procedure var body env)))
 
-        (call-exp (rator rand)
+        (call-exp (rator opt rand)
           (let ((proc (expval->proc (value-of rator env)))
-                (arg (value-of rand env)))
+                (arg (let ((randval (value-of rand env)))
+                       (if (is-const opt) (const-val randval) randval))))
             (apply-procedure proc arg)))
 
         (letrec-exp (p-names b-vars p-bodies letrec-body)
@@ -94,14 +94,21 @@
             (value-of-begins exp1 exps)))
 
         (assign-exp (var exp1)
-          (begin
-            (setref!
-              (apply-env env var)
-              (value-of exp1 env))
-            (num-val 27)))
+          (let ((ref (apply-env env var)))
+            (if (const-val? (deref ref))
+              (eopl:error 'assign-exp "cannot set const variable ~s" var)
+              (begin
+                (setref! ref (value-of exp1 env))
+                (num-val 27)))))
 
         )))
 
+  ;; is-const : Option -> Bool
+  (define is-const
+    (lambda (opt)
+      (cases option opt
+        (option-const () #t)
+        (else #f))))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 119
--- a/lang.scm
+++ b/lang.scm
@@ -36,8 +36,9 @@
 
       (expression (identifier) var-exp)
 
+      ;; const: `let const x = ...` and `(f const v)` bind an immutable cell
       (expression
-       ("let" identifier "=" expression "in" expression)
+       ("let" option identifier "=" expression "in" expression)
        let-exp)
 
       (expression
@@ -45,8 +46,10 @@
        proc-exp)
 
       (expression
-       ("(" expression expression ")")
+       ("(" expression option expression ")")
        call-exp)
+      (option () option-empty)
+      (option ("const") option-const)
 
       (expression
         ("letrec"
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,23 @@
 in ((f 44) 33)"
 	12)
 
+      ;; const: `let const`/`(f const v)` bind an immutable cell
+      (const-let-reads-value  "let const x = 5 in -(x,1)" 4)
+      (const-let-set-rejected "let const x = 5 in set x = 10" error)
+      ;; note - `let const x = ...` (and `(f const v)`) wrap the cell's value in \
+      ;; note -   a const-val; reading is transparent but `set` on it errors.
+      ;; note - Plain (non-const) bindings stay mutable, so the two kinds coexist.
+      (const-and-mutable-mix-put-in-preview
+        "let x = 5
+         in let const y = 6
+            in begin
+                 set x = 10;
+                 -(x, y)
+               end"
+        4)
+      (const-call-reads-value  "(proc (x) -(x,1) const 5)" 4)
+      (const-call-set-rejected "(proc (x) set x = 10 const 5)" error)
+      (mutable-call-set-ok     "(proc (x) begin set x = 10; x end 5)" 10)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2023b84 — let : exception

`2023b84-let-exception.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_try-catch-matches_

```
try
{
  -(if -(4,6) then 70 else 20, 45)
}
catch [general]        : 11 ;
catch [not a number]   : 12 ;
catch [not a boolean]  : 13 ;
catch [environment]    : 14 ;
finally : 200 ;
```
⇒ `13`

Notes:

- catches are matched top-to-bottom by message; the four messages are "general", "not a number", "not a boolean", "environment"
- -(4,6) is -2 (nonzero), so if treats it as a number test -> raises "not a boolean"
- finally ALWAYS runs (normal exit, caught, or propagated) but its value is discarded
- an uncaught exception escapes to value-of-program and becomes the result (excp-val ...), which the harness compares against the expected message string

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -8,11 +8,16 @@
 
 ;;; an expressed value is either a number, a boolean or a procval.
 
+  (define-datatype exception exception?
+    (Exception (msg string?)))
+
   (define-datatype expval expval?
     (num-val
       (value number?))
     (bool-val
-      (boolean boolean?)))
+      (boolean boolean?))
+    (excp-val
+      (exn exception?)))
 
 ;;; extractors:
 
--- a/environments.scm
+++ b/environments.scm
@@ -43,7 +43,7 @@
   (define apply-env
     (lambda (env search-sym)
       (if (empty-env? env)
-	(eopl:error 'apply-env "No binding for ~s" search-sym)
+	(excp-val (Exception "environment"))
 	(let ((sym (extended-env-record->sym env))
 	      (val (extended-env-record->val env))
 	      (old-env (extended-env-record->old-env env)))
--- a/interp.scm
+++ b/interp.scm
@@ -14,6 +14,11 @@
 
 ;;;;;;;;;;;;;;;; the interpreter ;;;;;;;;;;;;;;;;
 
+  ;; Exceptions are ordinary expressed values (excp-val) that PROPAGATE: any
+  ;; sub-expression that yields an excp-val short-circuits its enclosing
+  ;; expression, which simply returns that excp-val. No Scheme-level
+  ;; raise/with-handlers is used; control flow is plain value passing.
+
   ;; value-of-program : Program -> ExpVal
   ;; Page: 71
   (define value-of-program
@@ -21,6 +26,65 @@
       (cases program pgm
         (a-program (exp1)
           (value-of exp1 (init-env))))))
+
+  ;; excp-val? : ExpVal -> Bool
+  (define excp-val?
+    (lambda (v)
+      (cases expval v
+        (excp-val (e) #t)
+        (else #f))))
+
+  ;; need-num : ExpVal * (Int -> ExpVal) -> ExpVal
+  ;; propagate an exception value; run k on a number; otherwise yield the
+  ;; "not a number" exception value.
+  (define need-num
+    (lambda (v k)
+      (cases expval v
+        (excp-val (e) v)
+        (num-val (n) (k n))
+        (else (excp-val (Exception "not a number"))))))
+
+  ;; need-bool : ExpVal * (Bool -> ExpVal) -> ExpVal
+  (define need-bool
+    (lambda (v k)
+      (cases expval v
+        (excp-val (e) v)
+        (bool-val (b) (k b))
+        (else (excp-val (Exception "not a boolean"))))))
+
+  ;; except->msg : Except -> String
+  (define except->msg
+    (lambda (e)
+      (cases except e
+        (except-general () "general")
+        (except-not-a-number () "not a number")
+        (except-not-a-boolean () "not a boolean")
+        (except-environment () "environment"))))
+
+  ;; handle-exn : ExpVal(excp) * Listof(Except) * Listof(Exp) * Env -> ExpVal
+  ;; run the first catch whose message matches; if none match, return the
+  ;; exception value unchanged so it keeps propagating.
+  (define handle-exn
+    (lambda (exv excpts excptexps env)
+      (let ((msg (cases expval exv
+                   (excp-val (e) (cases exception e (Exception (m) m)))
+                   (else ""))))
+        (letrec
+          ((loop (lambda (es xs)
+            (cond
+              ((null? es) exv)
+              ((equal? (except->msg (car es)) msg) (value-of (car xs) env))
+              (else (loop (cdr es) (cdr xs)))))))
+          (loop excpts excptexps)))))
+
+  ;; run-finally : Listof(Exp) * Env -> Unspecified  (0 or 1 expressions)
+  ;; evaluated only for side effects; its value is discarded.
+  (define run-finally
+    (lambda (finexps env)
+      (if (null? finexps)
+        #f
+        (begin (value-of (car finexps) env)
+               (run-finally (cdr finexps) env)))))
 
   ;; value-of : Exp * Env -> ExpVal
   ;; Page: 71
@@ -36,36 +100,51 @@
 
         ;\commentbox{\diffspec}
         (diff-exp (exp1 exp2)
-          (let ((val1 (value-of exp1 env))
-                (val2 (value-of exp2 env)))
-            (let ((num1 (expval->num val1))
-                  (num2 (expval->num val2)))
-              (num-val
-                (- num1 num2)))))
+          (need-num (value-of exp1 env)
+            (lambda (num1)
+              (need-num (value-of exp2 env)
+                (lambda (num2)
+                  (num-val (- num1 num2)))))))
 
         ;\commentbox{\zerotestspec}
         (zero?-exp (exp1)
-          (let ((val1 (value-of exp1 env)))
-            (let ((num1 (expval->num val1)))
+          (need-num (value-of exp1 env)
+            (lambda (num1)
               (if (zero? num1)
                 (bool-val #t)
                 (bool-val #f)))))
 
         ;\commentbox{\ma{\theifspec}}
         (if-exp (exp1 exp2 exp3)
-          (let ((val1 (value-of exp1 env)))
-            (if (expval->bool val1)
-              (value-of exp2 env)
-              (value-of exp3 env))))
+          (need-bool (value-of exp1 env)
+            (lambda (b)
+              (if b
+                (value-of exp2 env)
+                (value-of exp3 env)))))
 
         ;\commentbox{\ma{\theletspecsplit}}
         (let-exp (var exp1 body)
           (let ((val1 (value-of exp1 env)))
-            (value-of body
-              (extend-env var val1 env))))
+            (if (excp-val? val1)
+              val1
+              (value-of body (extend-env var val1 env)))))
+
+        (throw-exp (excpt)
+          (excp-val (Exception (except->msg excpt))))
+
+        ;; run exp1; if it yields an exception value, the first matching catch
+        ;; handles it (an unmatched one keeps propagating); finally always runs
+        ;; (its value discarded).
+        (try-exp (exp1 excpts excptexps finexps)
+          (let* ((result (value-of exp1 env))
+                 (handled (if (excp-val? result)
+                            (handle-exn result excpts excptexps env)
+                            result)))
+            (begin
+              (run-finally finexps env)
+              handled)))
 
         )))
 
 
   )
-
--- a/lang.scm
+++ b/lang.scm
@@ -42,6 +42,21 @@
        ("let" identifier "=" expression "in" expression)
        let-exp)
 
+      (expression
+       ("throw" except)
+       throw-exp)
+
+      (expression
+       ("try" "{" expression "}"
+        (arbno "catch" "[" except "]" ":" expression ";")
+        (arbno "finally" ":" expression ";"))
+       try-exp)
+
+      (except ("general") except-general)
+      (except ("not a number") except-not-a-number)
+      (except ("not a boolean") except-not-a-boolean)
+      (except ("environment") except-environment)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -21,18 +21,19 @@
       (test-var-2 "-(x,1)" 9)
       (test-var-3 "-(1,x)" -9)
 
-      ;; simple unbound variables
-      (test-unbound-var-1 "foo" error)
-      (test-unbound-var-2 "-(x,foo)" error)
+      ;; unbound variables now raise the "environment" exception
+      ;; (instead of aborting with eopl:error)
+      (test-unbound-var-1 "foo" "environment")
+      (test-unbound-var-2 "-(x,foo)" "environment")
 
       ;; simple conditionals
       (if-true "if zero?(0) then 3 else 4" 3)
       (if-false "if zero?(1) then 3 else 4" 4)
 
-      ;; test dynamic typechecking
-      (no-bool-to-diff-1 "-(zero?(0),1)" error)
-      (no-bool-to-diff-2 "-(1,zero?(0))" error)
-      (no-int-to-if "if 1 then 2 else 3" error)
+      ;; dynamic type errors now raise exceptions instead of aborting
+      (no-bool-to-diff-1 "-(zero?(0),1)" "not a number")
+      (no-bool-to-diff-2 "-(1,zero?(0))" "not a number")
+      (no-int-to-if "if 1 then 2 else 3" "not a boolean")
 
       ;; make sure that the test and both arms get evaluated
       ;; properly.
@@ -55,5 +56,60 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
+      ;;;;;;;;;;;;;;;; exceptions (exam 2023b moed-a Q1) ;;;;;;;;;;;;;;;;
+      ;; a string expected value means (excp-val (Exception <string>))
+
+      ;; example 1 — subtracting a boolean raises "not a number", which
+      ;; escapes the let and becomes the program result (not 78)
+      (exc-not-a-number
+        "let t= -(6,zero?(9))in 78" "not a number")
+      ;; example 2 — an unbound variable raises "environment"
+      (exc-environment
+        "-(t,8)" "environment")
+      ;; example 3 — throw raises the named exception
+      (exc-throw-general
+        "throw general" "general")
+      ;; note - catches are matched top-to-bottom by message; the four messages are
+      ;;        "general", "not a number", "not a boolean", "environment"
+      ;; note - -(4,6) is -2 (nonzero), so if treats it as a number test -> raises "not a boolean"
+      ;; note - finally ALWAYS runs (normal exit, caught, or propagated) but its value is discarded
+      ;; note - an uncaught exception escapes to value-of-program and becomes the result (excp-val ...),
+      ;;        which the harness compares against the expected message string
+      (try-catch-matches-put-in-preview
+        "try
+           {
+             -(if -(4,6) then 70 else 20, 45)
+           }
+           catch [general]        : 11 ;
+           catch [not a number]   : 12 ;
+           catch [not a boolean]  : 13 ;
+           catch [environment]    : 14 ;
+           finally : 200 ;
+          " 13)
+      ;; example 5 — the matching catch itself throws; that propagates
+      (try-handler-rethrows
+        "try
+           {
+             -(if  -(4,6) then 70 else 20 , 45)
+           }
+           catch  [general] : 11   ;
+           catch [not a number] : 12   ;
+           catch [not a boolean] : throw general ;
+           catch [environment] :  14 ;
+           finally : 200;
+          " "general")
+      ;; example 6 — no catch matches "not a boolean", so it propagates
+      ;; (finally still runs)
+      (try-unhandled-propagates
+        "try
+           {
+             -(if  -(4,6) then 70 else 20 , 45)
+           }
+           catch  [general] : 11   ;
+           catch [not a number] : 12   ;
+           catch [environment] :  14 ;
+           finally : 200;
+          " "not a boolean")
+
       ))
   )
--- a/top.scm
+++ b/top.scm
@@ -46,6 +46,7 @@
       (cond
         ((number? sloppy-val) (num-val sloppy-val))
         ((boolean? sloppy-val) (bool-val sloppy-val))
+        ((string? sloppy-val) (excp-val (Exception sloppy-val)))
         (else
          (eopl:error 'sloppy->expval
                      "Can't convert sloppy value to expval: ~s"
```

[↑ back to top](#feature-catalogue)

## 2023b87 — implicit-refs : letlazy

`2023b87-implicit-refs-letlazy.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_lazy-unused-not-forced_

```
let x = (1 2) in 10
```
⇒ `10`

_lazy-yields-value_

```
let f = proc(y) -(y,1) in let x = (f 5) in x
```
⇒ `4`

Notes:

- only a CALL rhs in a let is made lazy (deferred as a thunk); it is forced the first time the bound var is read. Other rhs forms bind eagerly as usual.
- (1 2) errors if forced (1 is not a proc), so returning 10 proves x was never forced. The deferred thunk captures the env at the let, not the use site.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,7 +19,13 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (lazy-val
+      (lazy lazy?))
     )
+
+  (define-datatype lazy lazy?
+    (lazy1 (rator expression?) (rand expression?) (env environment?))
+  )
 
 ;;; extractors:
 
--- a/interp.scm
+++ b/interp.scm
@@ -39,7 +39,26 @@
 
         ;\commentbox{ (value-of (var-exp \x{}) \r)
         ;              = (deref (apply-env \r \x{}))}
-        (var-exp (var) (deref (apply-env env var)))
+        (var-exp (var)
+          (let
+            (
+              (v1 (deref (apply-env env var)))
+            )
+            (cases expval v1
+              (lazy-val (lz)
+                (cases lazy lz
+                  (lazy1 (rator rand env2)
+                    (apply-procedure
+                      (expval->proc (value-of rator env2))
+                      (value-of rand env2)
+                    )
+                  )
+                )
+              )
+              (else v1)
+            )
+          )
+        )
 
         ;\commentbox{\diffspec}
         (diff-exp (exp1 exp2)
@@ -67,9 +86,18 @@
 
         ;\commentbox{\ma{\theletspecsplit}}
         (let-exp (var exp1 body)
-          (let ((v1 (value-of exp1 env)))
-            (value-of body
-              (extend-env var (newref v1) env))))
+          (let
+            (
+              (v1
+                (cases expression exp1
+                  (call-exp (rator rand) (lazy-val (lazy1 rator rand env)))
+                  (else (value-of exp1 env))
+                )
+              )
+            )
+            (value-of body (extend-env var (newref v1) env))
+          )
+        )
 
         (proc-exp (var body)
           (proc-val (procedure var body env)))
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,22 @@
 in ((f 44) 33)"
 	12)
 
+      ;; note - only a CALL rhs in a let is made lazy (deferred as a thunk); it is forced \
+      ;; note - the first time the bound var is read. Other rhs forms bind eagerly as usual.
+      ;; note - (1 2) errors if forced (1 is not a proc), so returning 10 proves x was never \
+      ;; note - forced. The deferred thunk captures the env at the let, not the use site.
+      (lazy-unused-not-forced-put-in-preview "let x = (1 2) in 10" 10)
+      (lazy-used-is-forced    "let x = (1 2) in x" error)
+      (lazy-yields-value-put-in-preview "let f = proc(y) -(y,1) in let x = (f 5) in x" 4)
+      (lazy-used-in-arith
+        "let inc = proc(y) -(y,-1) in let x = (inc 9) in -(x,1)" 9)
+      (lazy-used-twice
+        "let f = proc(y) -(y,1) in let x = (f 10) in -(x,x)" 0)
+      ;; the deferred call captures the env AT THE let, not where it's forced
+      (lazy-captures-let-env
+        "let a = 100 in let x = (proc(y) -(y,a) 10) in let a = 1 in x" -90)
+      ;; non-call RHS still binds eagerly, as before
+      (lazy-noncall-rhs-eager "let x = -(3,1) in x" 2)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2023b87 — proc-ds : global

`2023b87-proc-ds-global.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_global-skips-local-let_

```
let x = 99 in ::x
```
⇒ `10`

Notes:

- ::id walks the env, skips exactly ONE matching binding, returns the next.
- errors if id has no shadowed (second) binding, or is wholly unbound.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -73,6 +73,33 @@
                 (arg (value-of rand env)))
             (apply-procedure proc arg)))
 
+        (global-exp (id)
+          (letrec
+            (
+              (apply-env* (lambda (env2 search-sym num)
+                (if (empty-env-record? env2)
+                  (eopl:error 'value-of "no global variable")
+                  (let
+                    (
+                      (sym (extended-env-record->sym env2))
+                      (val (extended-env-record->val env2))
+                      (old-env (extended-env-record->old-env env2))
+                    )
+                    (if (eqv? search-sym sym)
+                      (if (zero? num)
+                        val
+                        (apply-env* old-env search-sym (- num 1))
+                      )
+                      (apply-env* old-env search-sym num)
+                    )
+                  )
+                )
+              ))
+            )
+            (apply-env* env id 1)
+          )
+        )
+
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -48,6 +48,11 @@
        ("(" expression expression ")")
        call-exp)
 
+       (expression
+        ("::" identifier)
+        global-exp
+       )
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,21 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;; global access: ::id skips the innermost binding of id and returns
+      ;; the next one out (init-env globals are i=1, v=5, x=10)
+      ;; note - ::id walks the env, skips exactly ONE matching binding, returns the next.
+      ;; note - errors if id has no shadowed (second) binding, or is wholly unbound.
+      (global-skips-local-let-put-in-preview    "let x = 99 in ::x" 10)
+      (global-local-still-visible "let x = 99 in x" 99)
+      (global-vs-local-diff       "let x = 99 in -(x, ::x)" 89)
+      (global-skips-proc-param    "(proc(x) ::x 99)" 10)
+      (global-other-var           "let v = 7 in ::v" 5)
+      ;; only goes up ONE level — returns the immediately-shadowed binding,
+      ;; not the outermost
+      (global-one-level-only      "let x = 1 in let x = 2 in ::x" 1)
+      ;; error: id bound only once (no shadowed binding to reach)
+      (global-no-shadow-error     "::x" error)
+      (global-unbound-error       "::foo" error)
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2023b99 — implicit-refs : guard

`2023b99-implicit-refs-guard.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_guard-set-ok_

```
let # x = 5 in begin set x = 10; x end
```
⇒ `10`

Notes:

- guards: # num, ? bool, @ proc, (none) = unguarded. The guard is stored on the cell itself, so it is re-checked on every set, not just at let-binding time.
- storing a mismatched type (e.g. set x = zero?(0) on a # cell) errors.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,6 +19,7 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (guard-val (inner expval?) (typ string?))
     )
 
 ;;; extractors:
@@ -47,6 +48,24 @@
 	(ref-val (ref) ref)
 	(else (expval-extractor-error 'reference v)))))
 
+  (define expval->guardval
+    (lambda (v)
+      (cases expval v
+	(guard-val (inner typ) inner)
+	(else (expval-extractor-error 'guard v)))))
+
+  (define strip-guard
+    (lambda (v)
+      (cases expval v
+	(guard-val (inner typ) inner)
+	(else v))))
+
+  (define expval->guardtyp
+    (lambda (v)
+      (cases expval v
+	(guard-val (inner typ) typ)
+	(else ""))))
+
   (define expval-extractor-error
     (lambda (variant value)
       (eopl:error 'expval-extractors "Looking for a ~s, found ~s"
@@ -56,6 +75,7 @@
 
   (define-datatype proc proc?
     (procedure
+      (grd guard?)                 ; the parameter's type guard (guard-empty = none)
       (bvar symbol?)
       (body expression?)
       (env environment?)))
@@ -96,7 +116,7 @@
       (cases expval val
 	(proc-val (p)
 	  (cases proc p
-	    (procedure (var body saved-env)
+	    (procedure (grd var body saved-env)
 	      (list 'procedure var '... (env->list saved-env)))))
 	(else val))))
 
--- a/environments.scm
+++ b/environments.scm
@@ -1,6 +1,7 @@
 (module environments (lib "eopl.ss" "eopl")
 
   (require "data-structures.scm")
+  (require "lang.scm")                  ; for the guard datatype (guard-empty)
   (require "store.scm")
   (provide init-env empty-env extend-env apply-env)
 
@@ -39,6 +40,7 @@
               (newref
                 (proc-val
                   (procedure
+                    (guard-empty)                 ; letrec procs are unguarded
                     (list-ref b-vars n)
                     (list-ref p-bodies n)
                     env)))
--- a/interp.scm
+++ b/interp.scm
@@ -39,7 +39,7 @@
 
         ;\commentbox{ (value-of (var-exp \x{}) \r)
         ;              = (deref (apply-env \r \x{}))}
-        (var-exp (var) (deref (apply-env env var)))
+        (var-exp (var) (strip-guard (deref (apply-env env var))))
 
         ;\commentbox{\diffspec}
         (diff-exp (exp1 exp2)
@@ -66,13 +66,19 @@
               (value-of exp3 env))))
 
         ;\commentbox{\ma{\theletspecsplit}}
-        (let-exp (var exp1 body)
-          (let ((v1 (value-of exp1 env)))
-            (value-of body
-              (extend-env var (newref v1) env))))
+        (let-exp (grd var exp1 body)
+          (let* ((v1  (value-of exp1 env))
+                 (typ (grd->typ grd)))
+            (if (or (equal? typ "") (equal? typ (expval->typ v1)))
+              (value-of body
+                (extend-env var (newref (guard-val v1 typ)) env))
+              (eopl:error 'let-exp "violate let guard"))))
 
-        (proc-exp (var body)
-          (proc-val (procedure var body env)))
+        ;; a parameter guard is just a guarded let on the bound variable:
+        ;; the parameter guard is stored in the procedure itself and enforced by
+        ;; apply-procedure when the argument is bound.
+        (proc-exp (grd var body)
+          (proc-val (procedure grd var body env)))
 
         (call-exp (rator rand)
           (let ((proc (expval->proc (value-of rator env)))
@@ -95,14 +101,46 @@
 
         (assign-exp (var exp1)
           (begin
-            (setref!
-              (apply-env env var)
-              (value-of exp1 env))
+            (let*
+              (
+                (refvar (apply-env env var))
+                (refval (deref refvar))
+                (reftyp (expval->guardtyp refval))
+                (val1 (value-of exp1 env))
+              )
+              (if
+                (or
+                  (equal? reftyp "")
+                  (equal? reftyp (expval->typ val1))
+                )
+                (setref! refvar (guard-val val1 reftyp))
+                (eopl:error 'assign-exp "violate let guard")
+              )
+            )
             (num-val 27)))
 
         )))
 
-
+  (define grd->typ
+    (lambda (v)
+      (cases guard v
+        (guard-num () "num")
+        (guard-bool () "bool")
+        (guard-proc () "proc")
+        (guard-empty () "")
+      )
+    )
+  )
+  (define expval->typ
+    (lambda (v)
+      (cases expval v
+        (num-val (n) "num")
+        (bool-val (b) "bool")
+        (proc-val (p) "proc")
+        (else "")
+      )
+    )
+  )
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 119
 
@@ -118,19 +156,23 @@
   (define apply-procedure
     (lambda (proc1 arg)
       (cases proc proc1
-        (procedure (var body saved-env)
-          (let ((r (newref arg)))
-            (let ((new-env (extend-env var r saved-env)))
-              (if (instrument-let)
-                (begin
-                  (eopl:printf
-                    "entering body of proc ~s with env =~%"
-                    var)
-                  (pretty-print (env->list new-env))
-                  (eopl:printf "store =~%")
-                  (pretty-print (store->readable (get-store-as-list)))
-                  (eopl:printf "~%")))
-              (value-of body new-env)))))))
+        (procedure (grd var body saved-env)
+          (let ((typ (grd->typ grd)))
+            (if (or (equal? typ "") (equal? typ (expval->typ arg)))
+              ;; bind the parameter as a guarded cell, so a later `set` is type-checked too
+              (let ((r (newref (guard-val arg typ))))
+                (let ((new-env (extend-env var r saved-env)))
+                  (if (instrument-let)
+                    (begin
+                      (eopl:printf
+                        "entering body of proc ~s with env =~%"
+                        var)
+                      (pretty-print (env->list new-env))
+                      (eopl:printf "store =~%")
+                      (pretty-print (store->readable (get-store-as-list)))
+                      (eopl:printf "~%")))
+                  (value-of body new-env)))
+              (eopl:error 'apply-procedure "violate proc guard")))))))
 
   ;; store->readable : Listof(List(Ref,Expval))
   ;;                    -> Listof(List(Ref,Something-Readable))
--- a/lang.scm
+++ b/lang.scm
@@ -37,11 +37,11 @@
       (expression (identifier) var-exp)
 
       (expression
-       ("let" identifier "=" expression "in" expression)
+       ("let" guard identifier "=" expression "in" expression)
        let-exp)
 
       (expression
-       ("proc" "(" identifier ")" expression)
+       ("proc" "(" guard identifier ")" expression)
        proc-exp)
 
       (expression
@@ -64,6 +64,11 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      (guard ("#") guard-num)
+      (guard ("?") guard-bool)
+      (guard ("@") guard-proc)
+      (guard () guard-empty)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,28 @@
 in ((f 44) 33)"
 	12)
 
+      ;; guards: # = num, ? = bool, @ = proc, (empty) = unguarded.
+      ;; checked on let-binding, proc application, and set.
+
+      ;; let guard — value matches / violates the declared type
+      (guard-let-num-ok        "let # x = 5 in -(x,1)" 4)
+      (guard-let-num-violation "let # x = zero?(0) in x" error)         ; declares num, binds bool
+      (guard-let-bool-ok       "let ? b = zero?(0) in if b then 1 else 2" 1)
+      (guard-let-empty-ok      "let x = zero?(0) in if x then 1 else 2" 1)   ; no guard = anything
+
+      ;; proc guard — argument matches / violates the parameter's type
+      (guard-proc-num-ok        "(proc (# x) -(x,1) 5)" 4)
+      (guard-proc-num-violation "(proc (# x) x zero?(0))" error)        ; num param, given bool
+      (guard-proc-bool-ok       "(proc (? b) if b then 1 else 2 zero?(0))" 1)
+      (guard-proc-proc-ok       "(proc (@ f) (f 5) proc (x) -(x,1))" 4) ; proc param, given a proc
+
+      ;; set guard — the cell keeps its let-guard across assignment
+      ;; note - guards: # num, ? bool, @ proc, (none) = unguarded. The guard is stored on the \
+      ;; note - cell itself, so it is re-checked on every set, not just at let-binding time.
+      ;; note - storing a mismatched type (e.g. set x = zero?(0) on a # cell) errors.
+      (guard-set-ok-put-in-preview
+        "let # x = 5 in begin set x = 10; x end" 10)
+      (guard-set-violation "let # x = 5 in set x = zero?(0)" error)     ; can't store a bool in a num cell
+
       ))
   )
--- a/top.scm
+++ b/top.scm
@@ -53,7 +53,7 @@
                 (run (cadr test))))
           (else (eopl:error 'run-one "no such test: ~s" test-name))))))
 
-  ;; (run-all)
+  (run-all)
 
   )
 
```

[↑ back to top](#feature-catalogue)

## 2023b99 — let : do

`2023b99-let-do.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_do-loop_

```
do (
  <a 0 4>
  <b 7 -(a,2)>
  <c -(b,1) -(a,b)>
  [zero? (b) -(a,c)]
  [zero? (-(c,-2)) -(a,5)]
)
```
⇒ `3`

Notes:

- <id init step>: id starts at init, each iteration id := id + step
- all step exprs evaluate against the PREVIOUS iteration's env (simultaneous update), not left-to-right
- [cond result] clauses checked top-to-bottom each iteration; first true cond returns its result and stops

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -64,8 +64,83 @@
             (value-of body
               (extend-env var val1 env))))
 
+        (do-exp (variables results)
+          ;; Initialzes loop variables.
+          (define do-build
+            (lambda (do-variables-remaning do-env)
+              (if (null? do-variables-remaning)
+                do-env
+                (cases do-variable-grammar (car do-variables-remaning)
+                  (do-variables (id init-exp step-exp)
+                    (do-build
+                      (cdr do-variables-remaning)
+                      (extend-env id (value-of init-exp do-env) do-env)
+                    )
+                  )
+                )
+              )
+            )
+          )
+
+          ;; Increments loop variables.
+          (define do-step
+            (lambda (do-variables-remaning do-env do-env-result)
+              (if (null? do-variables-remaning)
+                do-env-result
+                (cases do-variable-grammar (car do-variables-remaning)
+                  (do-variables (id init-exp step-exp)
+                    (do-step
+                      (cdr do-variables-remaning)
+                      do-env
+                      (extend-env
+                        id
+                        (num-val
+                          (+
+                            (expval->num (apply-env do-env id))
+                            (expval->num (value-of step-exp do-env))
+                          )
+                        )
+                        do-env-result
+                      )
+                    )
+                  )
+                )
+              )
+            )
+          )
+
+          ;; Checks if loop results and returns result value if done.
+          (define do-check
+            (lambda (do-results-remaining do-env)
+              (if (null? do-results-remaining)
+                (do-loop (do-step variables do-env do-env))
+                (cases do-results-grammar (car do-results-remaining)
+                  (do-results (cond-exp result-exp)
+                    (if (expval->bool (value-of cond-exp do-env))
+                      (value-of result-exp do-env)
+                      (do-check (cdr do-results-remaining) do-env))
+                  )
+                )
+              )
+            )
+          )
+
+          ;; Run loop
+          (define do-loop
+            (lambda (do-env)
+              (do-check results do-env)
+            )
+          )
+
+          ; Verify parameters and run the loop
+          (if (null? variables)
+            (eopl:error 'do-exp "do requires at least one variable expression")
+            (if (null? results)
+              (eopl:error 'do-exp "do requires at least one result expression")
+              (do-loop (do-build variables env))
+            )
+          )
+        )
         )))
-
-
   )
 
--- a/lang.scm
+++ b/lang.scm
@@ -42,6 +42,15 @@
        ("let" identifier "=" expression "in" expression)
        let-exp)
 
+      (expression
+        ("do" "(" (arbno do-variable-grammar) (arbno do-results-grammar) ")")
+        do-exp)
+      (do-variable-grammar
+        ("<" identifier expression expression ">")
+        do-variables)
+      (do-results-grammar
+        ("[" expression expression "]")
+        do-results)
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -55,5 +55,26 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
+      ;; do loop
+      ;; note - <id init step>: id starts at init, each iteration id := id + step
+      ;; note - all step exprs evaluate against the PREVIOUS iteration's env (simultaneous update), not left-to-right
+      ;; note - [cond result] clauses checked top-to-bottom each iteration; first true cond returns its result and stops
+      (do-loop-put-in-preview "do (
+        <a 0 4>
+        <b 7 -(a,2)>
+        <c -(b,1) -(a,b)>
+        [zero? (b) -(a,c)]
+        [zero? (-(c,-2)) -(a,5)]
+      )" 3)
+       (do-loop-no-variables "do (
+        [zero? (b) -(a,c)]
+        [zero? (-(c,-2)) -(a,5)]
+      )" error)
+       (do-loop-no-results "do (
+         <a 0 4>
+         <b 7 -(a,2)>
+         <c -(b,1) -(a,b)>
+      )" error)
       ))
+
   )
```

[↑ back to top](#feature-catalogue)

## 2024b84 — implicit-refs : forproc

`2024b84-implicit-refs-forproc.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_forproc-runs-body-each-iter_

```
let acc = 0
in begin
     for/proc f ; ( [x, x, x] ; [x, x, x] ; ) { set acc = -(acc,-1) };
     acc
   end
```
⇒ `3`

_forproc-body-calls-proc_

```
let acc = 10
in begin
     for/proc f ; ( [x, x] ; [ -(x,1), -(x,2) ] ; ) { set acc = (f acc) };
     acc
   end
```
⇒ `7`

Notes:

- `for/proc f ; ( [p1,..,pn] ; [b1,..,bn] ; ) <guard>* { stmt }` runs the stmt ONCE per (param, body) pair; the two bracketed lists are parallel and must be equal length.
- on iteration k it (re)binds `f` to `proc(pk) bk` (recursive, so bk may call f), and that f is visible to both the guards and the stmt of that iteration.
- a guard `< skip : c >` or `< break : c >` is tested BEFORE the stmt, first-true-wins: skip => don't run the stmt this iteration; break => stop the loop early.
- the form is a STATEMENT (always returns 27); watch its effect through mutation (set acc).

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -100,8 +100,49 @@
               (value-of exp1 env))
             (num-val 27)))
 
+        (forprox-exp (id ids bodies guards body)
+          (letrec (
+            (guard->action (lambda (grd)
+              (cases guard grd
+                (skip-guard (v) 'skip)
+                (break-guard (v) 'break)
+            )))
+            (guard->exp (lambda (grd)
+              (cases guard grd
+                (skip-guard (v) v)
+                (break-guard (v) v)
+            )))
+            (guardcheck (lambda (id2 idx bodyx guards2)
+              (if (null? guards2)
+                  'do
+                  (let* (
+                    (guardval (value-of (guard->exp (car guards2))
+                        (extend-env-rec* (list id2) (list idx) (list bodyx) env)
+                    ))
+                  ) (if (expval->bool guardval)
+                    (guard->action (car guards2))
+                    (guardcheck id2 idx bodyx (cdr guards2))
+                  ))
+            )))
+            (loop (lambda (ids2 bodies2)
+              (if (null? ids2) #t
+                (let* (
+                  (guardtype (guardcheck id (car ids2) (car bodies2) guards))
+                ) (cond
+                    ((equal? guardtype 'break) #t)
+                    ((equal? guardtype 'skip) (loop (cdr ids2) (cdr bodies2)))
+                    (else (let* (
+                      (r (value-of
+                          body
+                          (extend-env-rec* (list id) (list (car ids2)) (list (car bodies2)) env)
+                      ))
+                    ) (loop (cdr ids2) (cdr bodies2))))
+            )))))
+            (r (loop ids bodies))
+          ) (num-val 27)
+        ))
+
         )))
-
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 119
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,21 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      (expression
+        (
+          "for/proc" identifier ";"
+          "("
+          "[" (separated-list identifier ",") "]" ";"
+          "[" (separated-list expression ",") "]" ";"
+          ")"
+          (arbno "<" guard ">")
+          "{" expression "}"
+        )
+        forprox-exp
+      )
+
+      (guard ("skip" ":" expression) skip-guard)
+      (guard ("break" ":" expression) break-guard)
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,64 @@
 in ((f 44) 33)"
 	12)
 
+      ;;;;;;;;;;;;;;;; for/proc feature ;;;;;;;;;;;;;;;;
+      ;; note - `for/proc f ; ( [p1,..,pn] ; [b1,..,bn] ; ) <guard>* { stmt }` runs the stmt ONCE per \
+      ;; note -   (param, body) pair; the two bracketed lists are parallel and must be equal length.
+      ;; note - on iteration k it (re)binds `f` to `proc(pk) bk` (recursive, so bk may call f), \
+      ;; note -   and that f is visible to both the guards and the stmt of that iteration.
+      ;; note - a guard `< skip : c >` or `< break : c >` is tested BEFORE the stmt, first-true-wins: \
+      ;; note -   skip => don't run the stmt this iteration; break => stop the loop early.
+      ;; note - the form is a STATEMENT (always returns 27); watch its effect through mutation (set acc).
+
+      ;; simplest: 3 (param,body) pairs => the stmt runs 3 times, so acc counts 0->1->2->3
+      (forproc-runs-body-each-iter-put-in-preview "
+let acc = 0
+in begin
+     for/proc f ; ( [x, x, x] ; [x, x, x] ; ) { set acc = -(acc,-1) };
+     acc
+   end"
+        3)
+
+      ;; the stmt calls f, which is REDEFINED from the body list each iteration:
+      ;; iter1 f = proc(x) -(x,1); iter2 f = proc(x) -(x,2). acc: 10 -> (f 10)=9 -> (f 9)=7.
+      (forproc-body-calls-proc-put-in-preview "
+let acc = 10
+in begin
+     for/proc f ; ( [x, x] ; [ -(x,1), -(x,2) ] ; ) { set acc = (f acc) };
+     acc
+   end"
+        7)
+
+      ;; the bound proc may be recursive (extend-env-rec*): f(n) = n
+      (forproc-recursive-proc "
+let acc = 0
+in begin
+     for/proc f ; ( [n] ; [ if zero?(n) then 0 else -((f -(n,1)),-1) ] ; ) { set acc = (f 5) };
+     acc
+   end"
+        5)
+
+      ;; break: stop the loop once acc reaches 2 (guard checked before body)
+      (forproc-break "
+let acc = 0
+in begin
+     for/proc f ; ( [x, x, x, x] ; [x, x, x, x] ; )
+       < break : zero?(-(acc,2)) >
+       { set acc = -(acc,-1) };
+     acc
+   end"
+        2)
+
+      ;; skip: body is skipped on iterations where acc is already 1
+      (forproc-skip "
+let acc = 0
+in begin
+     for/proc f ; ( [x, x, x] ; [x, x, x] ; )
+       < skip : zero?(-(acc,1)) >
+       { set acc = -(acc,-1) };
+     acc
+   end"
+        1)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2024b84 — proc-ds : enum

`2024b84-proc-ds-enum.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_enum-match-middle-branch_

```
let c = enum {red, green, blue}
in let e = < c . green >
   in match [ c :: e ]
        { ?red   => 1; }
        { ?green => 2; }
        { ?blue  => 3; }
```
⇒ `2`

Notes:

- `enum {..}` makes an enum-type value; `< E . id >` makes an element (id must be in E, else error).
- `match [ T :: V ] {?id => body;}...` binds T to the enum type, V to an element, dispatches on V's id.
- branches must cover every variant exactly once; missing or duplicate variants -> error. match dispatches to the branch matching the element's id

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -16,7 +16,14 @@
     (bool-val
       (boolean boolean?))
     (proc-val
-      (proc proc?)))
+      (proc proc?))
+    (enumtype-val
+      (enmtype enumtype?)
+    )
+    (enumelem-val
+      (enmelem symbol?)
+    )
+      )
 
 ;;; extractors:
 
@@ -41,6 +48,24 @@
 	(proc-val (proc) proc)
 	(else (expval-extractor-error 'proc v)))))
 
+  (define expval->enumtype
+    (lambda (v)
+      (cases expval v
+        (enumtype-val (enm) enm)
+        (else (expval-extractor-error 'enumtype v))
+      )
+    )
+  )
+
+   (define expval->enumelem
+    (lambda (v)
+      (cases expval v
+        (enumelem-val (enmelem) enmelem)
+        (else (expval-extractor-error 'enumelem v))
+      )
+    )
+  )
+
   (define expval-extractor-error
     (lambda (variant value)
       (eopl:error 'expval-extractors "Looking for a ~s, found ~s"
@@ -55,6 +80,18 @@
       (var symbol?)
       (body expression?)
       (env environment?)))
+
+  (define-datatype enumtype enumtype?
+    (enmtyp (ids (list-of symbol?)))
+  )
+
+  (define enumtype->ids
+    (lambda (v)
+      (cases enumtype v
+        (enmtyp (ids) ids)
+      )
+    )
+  )
 
 ;;;;;;;;;;;;;;;; environment structures ;;;;;;;;;;;;;;;;
 
--- a/interp.scm
+++ b/interp.scm
@@ -73,7 +73,84 @@
                 (arg (value-of rand env)))
             (apply-procedure proc arg)))
 
+        (enum-exp (ids)
+          (enumtype-val (enmtyp ids))
+        )
+
+        (enum-elmt-exp (enm id)
+          (let*
+            (
+              (enmtype (expval->enumtype (value-of enm env)))
+              (a (enum-assert-ids enmtype (list id)))
+            )
+            (enumelem-val id)
+          )
+        )
+
+        (match-exp (enmid exp1 enmids exps)
+          (let*
+            (
+              (enmtype (expval->enumtype (apply-env env enmid)))
+              (elemid (expval->enumelem (value-of exp1 env)))
+              (a1 (if (null? enmids) (eopl:error "empty match") #t))
+              (a2 (enum-assert-ids-all enmtype enmids))
+              (a3 (enum-assert-ids enmtype (list elemid)))
+            )
+            (letrec
+              (
+                (match-exp-loop
+                  (lambda (enmids-loop exps-loop)
+                    (if (equal? elemid (car enmids-loop))
+                      (value-of (car exps-loop) env)
+                      (match-exp-loop (cdr enmids-loop) (cdr exps-loop))
+                    )
+                  )
+                )
+              )
+              (match-exp-loop enmids exps)
+            )
+          )
+        )
+
         )))
+
+  (define enum-assert-ids
+    (lambda (enmtype ids)
+      (cond
+        ((null? ids) #t)
+        (
+          (not (member (car ids) (enumtype->ids enmtype)))
+          (eopl:error 'enum-assert-ids "given id is not member of enum")
+        )
+        (else (enum-assert-ids enmtype (cdr ids)))
+      )
+    )
+  )
+
+  (define unique?
+    (lambda (lst)
+      (cond
+        ((null? lst) #t)
+        ((member (car lst) (cdr lst)) #f)
+        (else (unique? (cdr lst)))
+      )
+    )
+  )
+
+  (define enum-assert-ids-all
+    (lambda (enmtype ids)
+      (letrec
+        (
+          (a (enum-assert-ids enmtype ids))
+        )
+        (if (and (unique? ids)
+                 (= (length (enumtype->ids enmtype)) (length ids)))
+          #t
+          (eopl:error 'enum-assert "not all enum values present")
+        )
+      )
+    )
+  )
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 79
@@ -83,4 +160,5 @@
         (procedure (var body saved-env)
           (value-of body (extend-env var val saved-env))))))
 
+
   )
--- a/lang.scm
+++ b/lang.scm
@@ -48,6 +48,24 @@
        ("(" expression expression ")")
        call-exp)
 
+      (expression
+       ("enum" "{" (separated-list identifier ",") "}")
+       enum-exp
+      )
+
+      (expression
+        ("<" expression "." identifier ">")
+        enum-elmt-exp
+      )
+
+      (expression
+        (
+          "match" "[" identifier "::" expression "]"
+          (arbno "{" "?"identifier "=>" expression ";" "}")
+        )
+        match-exp
+      )
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,55 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;;;;;;;;;;;;;;;; enum feature ;;;;;;;;;;;;;;;;
+      ;; enum {a,b,...}            -> an enum *type* value
+      ;; < E . id >                -> the element `id` of enum type E (error if id not in E)
+      ;; match [ T :: V ] { ?id => body; } ...
+      ;;                           -> T is a variable bound to the enum type, V evaluates
+      ;;                              to an enum element; dispatch on the element's id,
+      ;;                              all variants must be covered by the branches.
+
+      ;; note - `enum {..}` makes an enum-type value; `< E . id >` makes an element (id must be in E, else error).
+      ;; note - `match [ T :: V ] {?id => body;}...` binds T to the enum type, V to an element, dispatches on V's id.
+      ;; note - branches must cover every variant exactly once; missing or duplicate variants -> error.
+      ;; match dispatches to the branch matching the element's id
+      (enum-match-middle-branch-put-in-preview
+       "let c = enum {red, green, blue}
+        in let e = < c . green >
+           in match [ c :: e ]
+                { ?red   => 1; }
+                { ?green => 2; }
+                { ?blue  => 3; }"
+        2)
+
+      ;; first branch selected
+      (enum-match-first-branch "
+let c = enum {red, green, blue}
+in let e = < c . red >
+   in match [ c :: e ] { ?red => 1; } { ?green => 2; } { ?blue => 3; }"
+        1)
+
+      ;; branch body is a real computation
+      (enum-match-body-computes "
+let c = enum {a, b}
+in match [ c :: < c . b > ] { ?a => 0; } { ?b => -(10,3); }"
+        7)
+
+      ;; <E . id> with id not a member of the enum -> error
+      (enum-elem-not-member "< enum {a, b, c} . zzz >" error)
+
+      ;; match must cover every variant of the enum -> error if one is missing
+      (enum-match-non-exhaustive "
+let c = enum {a, b}
+in match [ c :: < c . a > ] { ?a => 1; }"
+        error)
+
+      ;; duplicate pattern can't fake exhaustiveness (right count, but b uncovered) -> error
+      (enum-match-duplicate-pattern "
+let c = enum {a, b}
+in match [ c :: < c . a > ] { ?a => 1; } { ?a => 2; }"
+        error)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2024b98 — implicit-refs : multiptr

`2024b98-implicit-refs-multiptr.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_mptr-ex1_

```
let p = &&&(6)
in let q = **(p)
   in let num = *(q)
      in -(num, 2)
```
⇒ `4`

Notes:

- &..&(e) makes an n-level pointer to one shared leaf cell (n = count of &);
- *..*(p) peels n levels, deref'ing the leaf only when the last level is removed.
- peeling MORE levels than exist errors; here &&&=3 levels, **=2 then *=1 reach the leaf 6, so -(6,2) = 4. set @p mutates the shared leaf through any pointer.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,7 +19,32 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (multiptr-val
+      (multiptr multiptr?)
     )
+    )
+
+    (define-datatype multiptr multiptr?
+      (multiptr1 (ref reference?) (count integer?))
+    )
+
+    (define multiptr->ref (lambda (v)
+      (cases multiptr v
+        (multiptr1 (r c) r)
+      )
+    ))
+
+    (define multiptr->count (lambda (v)
+      (cases multiptr v
+        (multiptr1 (r c) c)
+      )
+    ))
+
+  (define expval->multiptr
+    (lambda (v)
+      (cases expval v
+	(multiptr-val (m) m)
+	(else (expval-extractor-error 'multiptr v)))))
 
 ;;; extractors:
 
--- a/interp.scm
+++ b/interp.scm
@@ -93,12 +93,47 @@
                      (value-of-begins (car es) (cdr es)))))))
             (value-of-begins exp1 exps)))
 
-        (assign-exp (var exp1)
-          (begin
-            (setref!
-              (apply-env env var)
-              (value-of exp1 env))
-            (num-val 27)))
+        (assign-exp (opt var exp1)
+          (cases opt-exp opt
+            (opt-exp-ptr ()
+              (begin
+                (setref!
+                  (multiptr->ref (expval->multiptr (deref (apply-env env var))))
+                  (value-of exp1 env)
+                )
+                (num-val 27)
+              )
+            )
+            (opt-exp-empty ()
+              (begin
+                (setref!
+                  (apply-env env var)
+                  (value-of exp1 env)
+                )
+                (num-val 27)
+              )
+            )
+          )
+        )
+
+        (multiptr-exp (ptrs data)
+          (multiptr-val (multiptr1 (newref (value-of data env)) (+ (length ptrs) 1)))
+        )
+
+        (multistar-exp (stars v)
+          (let*
+            (
+              (m1 (expval->multiptr (value-of v env)))
+              (count1 (- (multiptr->count m1) (+ (length stars) 1)))
+              (ref1 (multiptr->ref m1))
+            )
+            (cond
+              ((< count1 0) (eopl:error 'value-of "invalid star amount"))
+              ((= count1 0) (deref ref1))
+              (else         (multiptr-val (multiptr1 ref1 count1)))
+            )
+          )
+        )
 
         )))
 
--- a/lang.scm
+++ b/lang.scm
@@ -61,8 +61,22 @@
       ;; new for implicit-refs
 
       (expression
-        ("set" identifier "=" expression)
+        ("set" opt-exp identifier "=" expression)
         assign-exp)
+      (opt-exp ("@") opt-exp-ptr)
+      (opt-exp () opt-exp-empty)
+
+      (expression
+        ("&" (arbno amp) "(" expression ")")
+        multiptr-exp
+      )
+      (amp ("&") an-amp)
+
+      (expression
+        ("*" (arbno star) "(" expression ")")
+        multistar-exp
+      )
+      (star ("*") a-star)
 
       ))
 
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,55 @@
 in ((f 44) 33)"
 	12)
 
+      ;; multi-pointers (exam 2024b-98 Q2, worked examples 1-9 verbatim):
+      ;; &..&(e) builds an n-level pointer to e; *..*(p) dereferences n levels;
+      ;; set @p = e mutates the shared leaf.
+      ;; note - &..&(e) makes an n-level pointer to one shared leaf cell (n = count of &);
+      ;; note - *..*(p) peels n levels, deref'ing the leaf only when the last level is removed.
+      ;; note - peeling MORE levels than exist errors; here &&&=3 levels, **=2 then *=1 reach \
+      ;; note - the leaf 6, so -(6,2) = 4. set @p mutates the shared leaf through any pointer.
+      (mptr-ex1-put-in-preview
+        "let p = &&&(6)
+         in let q = **(p)
+            in let num = *(q)
+               in -(num, 2)" 4)
+      (mptr-ex2-error                       ; dereferencing more levels than exist
+        "let p = &&&(6)
+         in let q= **(p)
+            in let num = ****(q)
+               in -(num, 2)" error)
+      (mptr-ex3
+        "let p = **(&&&(6))
+         in -( *(p) ,5)" 1)
+      (mptr-ex4-error                       ; multistar on a non-pointer
+        "let p = *( zero?( 6))
+         in 9" error)
+      (mptr-ex5
+        "let p = &&&(proc (x) -(x,7))
+         in (***(p) 9)" 2)
+      ;; example 6 is omitted: `let p = &&&(proc..) in *(p)` returns a
+      ;; multi-pointer value, which the test harness can't represent/compare.
+      (mptr-ex7
+        "let p = &&&(proc (x) -(x,7))
+         in begin
+              set @p = 9;
+              -(***(p) , 2)
+            end" 7)
+      (mptr-ex8
+        "let p = &&&&(8)
+         in let q= **(p)
+            in begin
+                 set @q = 20;
+                 -(****(p) , 3)
+               end" 17)
+      (mptr-ex9
+        "let p = &&&&(8)
+         in let q= **(p)
+            in begin
+                 set @p = 20;
+                 set p = 5;
+                 -(** (q) , p)
+               end" 15)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2024b98 — proc-ds : forsum

`2024b98-proc-ds-forsum.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_forsum-guards-exam_

```
for/sum [i] (1,2,3,20,5,90)
  <skip: zero?(-(i,1))>
  <break: zero?(-(i,5))>
  <skip: zero?(-(i,3))>
  -(i,-5)
for/end
```
⇒ `32`

Notes:

- guards are tested in source order, first match wins; verb is `skip` (drop element) or `break` (stop loop, contribute 0 for it and the rest).
- body is only evaluated when no guard fires; empty/fully-broken loop sums to 0.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -73,6 +73,58 @@
                 (arg (value-of rand env)))
             (apply-procedure proc arg)))
 
+        (forsum-exp (id exps guards body)
+          (letrec
+            (
+              (guard->verb (lambda (grd)
+                (cases guard-exp grd
+                  (skip-guard (e) 'skip)
+                  (break-guard (e) 'break)
+                )
+              ))
+              (guard->exp (lambda (grd)
+                (cases guard-exp grd
+                  (skip-guard (e) e)
+                  (break-guard (e) e)
+                )
+              ))
+              (guards->action (lambda (grds expenv)
+                (if (null? grds)
+                  'run
+                  (let
+                    (
+                      (grd (car grds))
+                    )
+                    (if (expval->bool (value-of (guard->exp grd) expenv))
+                      (guard->verb grd)
+                      (guards->action (cdr grds) expenv)
+                    )
+                  )
+                )
+              ))
+              (loop (lambda (exps2)
+                (if (null? exps2)
+                  0
+                  (let*
+                    (
+                      (exp2 (car exps2))
+                      (next (cdr exps2))
+                      (expenv (extend-env id (value-of exp2 env) env))
+                      (action (guards->action guards expenv))
+                    )
+                    (cond
+                      ((equal? action 'break) 0)
+                      ((equal? action 'skip) (loop next))
+                      (else (+ (expval->num (value-of body expenv)) (loop next)))
+                    )
+                  )
+                )
+              ))
+            )
+            (num-val (loop exps))
+          )
+        )
+
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -48,6 +48,18 @@
        ("(" expression expression ")")
        call-exp)
 
+      (expression
+        (
+          "for/sum" "[" identifier "]" "(" (separated-list expression ",") ")"
+          (arbno "<" guard-exp ">")
+          expression
+          "for/end"
+        )
+        forsum-exp
+      )
+      (guard-exp ("skip" ":" expression) skip-guard)
+      (guard-exp ("break" ":" expression) break-guard)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,30 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;; for/sum: loop id over the value list, sum the body; guards (checked
+      ;; in order) can `skip` an element or `break` out of the loop.
+      (forsum-sum-all   "for/sum [i] (1,2,3,4) i for/end" 10)
+      (forsum-single    "for/sum [i] (10) i for/end" 10)
+      (forsum-body-expr "for/sum [i] (1,2,3,20,5,90) -(i,-5) for/end" 151)
+      (forsum-list-of-exprs "for/sum [i] (-(2,1),5) i for/end" 6)
+      ;; exam example 1: skip i=1, break at i=5, skip i=3; body is -(i,-5) (= i+5)
+      ;; → (2+5) + (20+5) = 32
+      ;; note - guards are tested in source order, first match wins; verb is `skip` \
+      ;; note -   (drop element) or `break` (stop loop, contribute 0 for it and the rest).
+      ;; note - body is only evaluated when no guard fires; empty/fully-broken loop sums to 0.
+      (forsum-guards-exam-put-in-preview
+        "for/sum [i] (1,2,3,20,5,90)
+           <skip: zero?(-(i,1))>
+           <break: zero?(-(i,5))>
+           <skip: zero?(-(i,3))>
+           -(i,-5)
+         for/end" 32)
+      ;; break on the very first element → empty sum
+      (forsum-break-first
+        "for/sum [i] (5,6,7) <break: zero?(-(i,5))> i for/end" 0)
+      ;; a guard that is always true (i-i=0) skips every element → 0
+      (forsum-skip-all
+        "for/sum [i] (1,2,3) <skip: zero?(-(i,i))> i for/end" 0)
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2025b84 — implicit-refs : map

`2025b84-implicit-refs-map.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_map-memoized_

```
let xs = map proc(x) -(x,1) [10, 20, 30]
in -(listref(xs, 2), listref(xs, 0))
```
⇒ `20`

Notes:

- map builds an UNEVALUATED value; the proc is applied to every element only when listref first forces it, then the result list is memoized back into the store ref, so repeated listref on the same binding re-uses it (no re-map).
- here listref(xs,2)=29, listref(xs,0)=9, so -(29,9) = 20.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,6 +19,12 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (unevaluated-val
+      (uproc expression?)
+      (uexps (list-of expression?))
+      (uenv environment?))
+    (list-val
+      (elems (list-of expval?)))
     )
 
 ;;; extractors:
@@ -46,6 +52,12 @@
       (cases expval v
 	(ref-val (ref) ref)
 	(else (expval-extractor-error 'reference v)))))
+
+  (define expval->listelem
+    (lambda (v i)
+      (cases expval v
+	(list-val (e) (list-ref e i))
+	(else (eopl:error 'listelem "expected a list, found ~s" v)))))
 
   (define expval-extractor-error
     (lambda (variant value)
--- a/interp.scm
+++ b/interp.scm
@@ -100,8 +100,56 @@
               (value-of exp1 env))
             (num-val 27)))
 
+        (map-exp (exp1 exps)
+          (unevaluated-val exp1 exps env)
+        )
+
+        (listref-exp (e1 e2)
+          (let*
+            (
+              (evaluate (lambda (val)
+                (cases expval val
+                  (unevaluated-val (uproc uexps uenv)
+                    (let*
+                      (
+                        (proc2 (expval->proc (value-of uproc uenv)))
+                        (elems (map
+                          (lambda (v)
+                            (apply-procedure proc2 (value-of v uenv))
+                          )
+                          uexps
+                        ))
+                      )
+                      (list-val elems)
+                    )
+                  )
+                  (else val)
+                )
+              ))
+              (evaluate-ref (lambda (ref)
+                (let*
+                  (
+                    (evaluated (evaluate (deref ref)))
+                  )
+                  (begin
+                    (setref! ref evaluated)
+                    evaluated
+                  )
+                )
+              ))
+              (index (expval->num (value-of e2 env)))
+              (listval
+                (cases expression e1
+                  (var-exp (var) (evaluate-ref (apply-env env var)))
+                  (else (evaluate (value-of e1 env)))
+                )
+              )
+            )
+            (expval->listelem listval index)
+          )
+        )
+
         )))
-
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 119
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,16 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      (expression
+       ("map" expression "[" (separated-list expression ",") "]")
+        map-exp
+      )
+
+      (expression
+       ("listref" "(" expression "," expression ")" )
+       listref-exp
+      )
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,39 @@
 in ((f 44) 33)"
 	12)
 
+      ;; lazy map + listref
+      (map-listref-first
+        "let xs = map proc(x) -(x,1) [10, 20, 30] in listref(xs, 0)" 9)
+      (map-listref-last
+        "let xs = map proc(x) -(x,1) [10, 20, 30] in listref(xs, 2)" 29)
+      (map-listref-identity
+        "let xs = map proc(x) x [5, 6, 7] in listref(xs, 1)" 6)
+      ;; the mapping proc closes over its definition environment
+      (map-closure
+        "let n = 100
+         in let xs = map proc(x) -(x,n) [105, 110] in listref(xs, 1)" 10)
+      ;; forcing is memoized: deref it twice, still indexes correctly
+      ;; note - map builds an UNEVALUATED value; the proc is applied to every element only \
+      ;; note - when listref first forces it, then the result list is memoized back into the \
+      ;; note - store ref, so repeated listref on the same binding re-uses it (no re-map).
+      ;; note - here listref(xs,2)=29, listref(xs,0)=9, so -(29,9) = 20.
+      (map-memoized-put-in-preview
+        "let xs = map proc(x) -(x,1) [10, 20, 30]
+         in -(listref(xs, 2), listref(xs, 0))" 20)
+
+      ;; inline map: listref forces a map literal directly, no let binding
+      (inline-map-first
+        "listref(map proc(x) -(x,1) [10, 20, 30], 0)" 9)
+      (inline-map-last
+        "listref(map proc(x) -(x,1) [10, 20, 30], 2)" 29)
+      (inline-map-identity
+        "listref(map proc(x) x [5, 6, 7], 1)" 6)
+      ;; inline map whose proc closes over an outer variable
+      (inline-map-closure
+        "let n = 100 in listref(map proc(x) -(x,n) [105, 110], 1)" 10)
+      ;; the index expression is itself evaluated
+      (inline-map-computed-index
+        "listref(map proc(x) -(x,1) [10, 20, 30], -(2,1))" 19)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2025b84 — let : cast

`2025b84-let-cast.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_cast-explicit-boolean-to-number_

```
 -(100, <int>(zero?(0)))
```
⇒ `99`

Notes:

- <int>(bool) maps #t->1 and #f->0; <bool>(int) is (> n 0) so 0 and negatives are false
- if's test is implicitly cast to bool, so "if 9 ..." takes the then-branch
- cast is total (never errors): every num/bool converts both ways

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -21,6 +21,16 @@
       (cases program pgm
         (a-program (exp1)
           (value-of exp1 (init-env))))))
+
+  ;; coerce an expval to a Scheme boolean (a number is true iff > 0)
+  (define to-bool
+    (lambda (val)
+      (cases expval val
+        (num-val  (number)  (> number 0))
+        (bool-val (boolean) boolean)
+      )
+    )
+  )
 
   ;; value-of : Exp * Env -> ExpVal
   ;; Page: 71
@@ -53,10 +63,9 @@
 
         ;\commentbox{\ma{\theifspec}}
         (if-exp (exp1 exp2 exp3)
-          (let ((val1 (value-of exp1 env)))
-            (if (expval->bool val1)
-              (value-of exp2 env)
-              (value-of exp3 env))))
+          (if (to-bool (value-of exp1 env))
+            (value-of exp2 env)
+            (value-of exp3 env)))
 
         ;\commentbox{\ma{\theletspecsplit}}
         (let-exp (var exp1 body)
@@ -64,8 +73,24 @@
             (value-of body
               (extend-env var val1 env))))
 
+        (cast-exp (typ exp1)
+          (let
+            (
+              (val (value-of exp1 env))
+            )
+            (cases cast-type typ
+              (cast-int-type ()
+                (cases expval val
+                  (num-val  (number)  (num-val number))
+                  (bool-val (boolean) (num-val (if boolean 1 0)))
+                )
+              )
+              (cast-bool-type ()
+                (bool-val (to-bool val))
+              )
+            )
+          )
+        )
         )))
-
-
   )
 
--- a/lang.scm
+++ b/lang.scm
@@ -42,6 +42,9 @@
        ("let" identifier "=" expression "in" expression)
        let-exp)
 
+      (expression (cast-type "(" expression ")") cast-exp)
+      (cast-type ("<int>")  cast-int-type)
+      (cast-type ("<bool>") cast-bool-type)
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -32,7 +32,7 @@
       ;; test dynamic typechecking
       (no-bool-to-diff-1 "-(zero?(0),1)" error)
       (no-bool-to-diff-2 "-(1,zero?(0))" error)
-      (no-int-to-if "if 1 then 2 else 3" error)
+      ;;(no-int-to-if "if 1 then 2 else 3" error)
 
       ;; make sure that the test and both arms get evaluated
       ;; properly.
@@ -55,5 +55,21 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
+      ;; casting
+      (cast-implicit-number-to-true " if 9 then 100 else 200" 100)
+      (cast-implicit-number-to-false " if 0 then 100 else 200" 200)
+      ;; note - <int>(bool) maps #t->1 and #f->0; <bool>(int) is (> n 0) so 0 and negatives are false
+      ;; note - if's test is implicitly cast to bool, so "if 9 ..." takes the then-branch
+      ;; note - cast is total (never errors): every num/bool converts both ways
+      (cast-explicit-boolean-to-number-put-in-preview " -(100, <int>(zero?(0)))" 99)
+      (cast-explicit-number-to-true " if <bool> (9) then 100 else 200" 100)
+      (cast-explicit-var-to-true "
+      let w = 40
+      in
+      if <bool>(w) then 500 else 700
+      " 500)
+      (cast-explicit-boolean-to-boolean "if <bool>(zero?(0)) then 3 else 4" 3)
+      (cast-explicit-number-to-number "-(<int>(3), 2)" 1)
       ))
+
   )
```

[↑ back to top](#feature-catalogue)

## 2025b91 — implicit-refs : overload-proc

`2025b91-implicit-refs-overload-proc.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_overload-three-way_

```
let id = proc(int x) x
in let f = proc(int x) -(x,3)
   in begin
        overload f with (bool b) if b then 100 else 200;
        overload f with (func g) (g 42);
        -(-((f 10), (f zero?(5))), (f id))
      end
```
⇒ `-235`

Notes:

- a proc-val holds 3 slots (int/bool/func); a typed proc fills only its slot, others are empty-proc.
- a call dispatches on the RUNTIME type of the argument; hitting an empty slot is an error.
- (f 10)->-(10,3)=7, (f zero?(5)=#f)->200, (f id)->(id 42)=42; -(-(7,200),42) = -235. all three slots on one procedure, dispatched three ways

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -16,7 +16,7 @@
     (bool-val
       (boolean boolean?))
     (proc-val
-      (proc proc?))
+      (int-proc proc?) (bool-proc proc?) (func-proc proc?))
     (ref-val
       (ref reference?))
     )
@@ -35,12 +35,6 @@
 	(bool-val (bool) bool)
 	(else (expval-extractor-error 'bool v)))))
 
-  (define expval->proc
-    (lambda (v)
-      (cases expval v
-	(proc-val (proc) proc)
-	(else (expval-extractor-error 'proc v)))))
-
 (define expval->ref
     (lambda (v)
       (cases expval v
@@ -58,7 +52,8 @@
     (procedure
       (bvar symbol?)
       (body expression?)
-      (env environment?)))
+      (env environment?))
+    (empty-proc))
 
   (define-datatype environment environment?
     (empty-env)
@@ -87,17 +82,4 @@
 	  (cons
 	    (list 'letrec p-names '...)
 	    (env->list saved-env))))))
-
-  ;; expval->printable : ExpVal -> List
-  ;; returns a value like its argument, except procedures get cleaned
-  ;; up with env->list
-  (define expval->printable
-    (lambda (val)
-      (cases expval val
-	(proc-val (p)
-	  (cases proc p
-	    (procedure (var body saved-env)
-	      (list 'procedure var '... (env->list saved-env)))))
-	(else val))))
-
 )
--- a/environments.scm
+++ b/environments.scm
@@ -37,11 +37,11 @@
             ;; n : (maybe int)
             (if n
               (newref
-                (proc-val
-                  (procedure
-                    (list-ref b-vars n)
-                    (list-ref p-bodies n)
-                    env)))
+                (let ((p (procedure
+                           (list-ref b-vars n)
+                           (list-ref p-bodies n)
+                           env)))
+                  (proc-val p p p)))
               (apply-env saved-env search-var)))))))
 
   ;; location : Sym * Listof(Sym) -> Maybe(Int)
--- a/interp.scm
+++ b/interp.scm
@@ -71,13 +71,12 @@
             (value-of body
               (extend-env var (newref v1) env))))
 
-        (proc-exp (var body)
-          (proc-val (procedure var body env)))
-
-        (call-exp (rator rand)
-          (let ((proc (expval->proc (value-of rator env)))
-                (arg (value-of rand env)))
-            (apply-procedure proc arg)))
+        (proc-exp (typ var body)
+          (let ((p (procedure var body env)))
+            (cases type typ
+              (int-type ()  (proc-val p (empty-proc) (empty-proc)))
+              (bool-type () (proc-val (empty-proc) p (empty-proc)))
+              (func-type () (proc-val (empty-proc) (empty-proc) p)))))
 
         (letrec-exp (p-names b-vars p-bodies letrec-body)
           (value-of letrec-body
@@ -100,8 +99,42 @@
               (value-of exp1 env))
             (num-val 27)))
 
+        (overload-proc (p-name typ var body)
+          (let* ((ref1 (apply-env env p-name))
+                 (v1 (deref ref1)))
+            (cases expval v1
+              (proc-val (iproc bproc fproc)
+                (let* ((newproc (procedure var body env))
+                       (newprocval
+                         (cases type typ
+                           (int-type ()  (proc-val newproc bproc   fproc))
+                           (bool-type () (proc-val iproc   newproc fproc))
+                           (func-type () (proc-val iproc   bproc   newproc)))))
+                  (begin
+                    (setref! ref1 newprocval)
+                    newprocval)))
+              (else (eopl:error 'overload-proc "~s is not a procedure" p-name)))))
+
+        (call-exp (rator rand)
+          (let ((ratorv (value-of rator env))
+                (randv  (value-of rand env)))
+            (cases expval ratorv
+              (proc-val (iproc bproc fproc)
+                (let ((chosen
+                        (cases expval randv
+                          (num-val  (n)     iproc)
+                          (bool-val (b)     bproc)
+                          (proc-val (i b f) fproc)
+                          (else (eopl:error 'call-exp
+                                  "no overload accepts argument ~s" randv)))))
+                  (cases proc chosen
+                    (empty-proc ()
+                      (eopl:error 'call-exp
+                        "operator has no overload for argument ~s" randv))
+                    (procedure (v b e) (apply-procedure chosen randv)))))
+              (else (eopl:error 'call-exp "not a procedure: ~s" ratorv)))))
+
         )))
-
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
   ;; Page: 119
@@ -128,20 +161,10 @@
                     var)
                   (pretty-print (env->list new-env))
                   (eopl:printf "store =~%")
-                  (pretty-print (store->readable (get-store-as-list)))
                   (eopl:printf "~%")))
-              (value-of body new-env)))))))
-
-  ;; store->readable : Listof(List(Ref,Expval))
-  ;;                    -> Listof(List(Ref,Something-Readable))
-  (define store->readable
-    (lambda (l)
-      (map
-        (lambda (p)
-          (list
-            (car p)
-            (expval->printable (cadr p))))
-        l)))
+              (value-of body new-env))))
+        (empty-proc ()
+          (eopl:error 'apply-procedure "applying an empty (missing) overload")))))
 
   )
 
--- a/lang.scm
+++ b/lang.scm
@@ -41,8 +41,16 @@
        let-exp)
 
       (expression
-       ("proc" "(" identifier ")" expression)
+       ("proc" "(" type identifier ")" expression)
        proc-exp)
+
+       (type ("int") int-type)
+       (type ("bool") bool-type)
+       (type ("func") func-type)
+
+       (expression
+        ("overload" identifier "with" "(" type identifier ")" expression)
+        overload-proc)
 
       (expression
        ("(" expression expression ")")
--- a/tests.scm
+++ b/tests.scm
@@ -54,22 +54,22 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
-      ;; simple applications
-      (apply-proc-in-rator-pos "(proc(x) -(x,1)  30)" 29)
-      (apply-simple-proc "let f = proc (x) -(x,1) in (f 30)" 29)
-      (let-to-proc-1 "(proc(f)(f 30)  proc(x)-(x,1))" 29)
+      ;; simple applications  (proc now requires an argument-type annotation)
+      (apply-proc-in-rator-pos "(proc(int x) -(x,1)  30)" 29)
+      (apply-simple-proc "let f = proc (int x) -(x,1) in (f 30)" 29)
+      (let-to-proc-1 "(proc(func f)(f 30)  proc(int x)-(x,1))" 29)
 
 
-      (nested-procs "((proc (x) proc (y) -(x,y)  5) 6)" -1)
-      (nested-procs2 "let f = proc(x) proc (y) -(x,y) in ((f -(10,5)) 6)"
+      (nested-procs "((proc (int x) proc (int y) -(x,y)  5) 6)" -1)
+      (nested-procs2 "let f = proc(int x) proc (int y) -(x,y) in ((f -(10,5)) 6)"
         -1)
 
        (y-combinator-1 "
-let fix =  proc (f)
-            let d = proc (x) proc (z) ((f (x x)) z)
-            in proc (n) ((f (d d)) n)
+let fix =  proc (func f)
+            let d = proc (func x) proc (int z) ((f (x x)) z)
+            in proc (int n) ((f (d d)) n)
 in let
-    t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
+    t4m = proc (func f) proc(int x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
 
@@ -90,7 +90,7 @@
 ;                  720)
 
       (HO-nested-letrecs
-"letrec even(odd)  = proc(x) if zero?(x) then 1 else (odd -(x,1))
+"letrec even(odd)  = proc(int x) if zero?(x) then 1 else (odd -(x,1))
    in letrec  odd(x)  = if zero?(x) then 0 else ((even odd) -(x,1))
    in (odd 13)" 1)
 
@@ -107,7 +107,7 @@
 
 
       (gensym-test
-"let g = let count = 0 in proc(d)
+"let g = let count = 0 in proc(int d)
                         let d = set count = -(count,-1)
                         in count
 in -((g 11), (g 22))"
@@ -124,7 +124,7 @@
    in let d = set x = 13 in (odd -99)" 1)
 
       (example-for-book-1 "
-let f = proc (x) proc (y)
+let f = proc (int x) proc (int y)
                   begin
                    set x = -(x,-1);
                    -(x,y)
@@ -132,5 +132,59 @@
 in ((f 44) 33)"
 	12)
 
+      ;;;;;;;;;;;;;;;; overloaded procedures ;;;;;;;;;;;;;;;;
+      ;; a typed proc fills only the slot for its declared argument type;
+      ;; a call dispatches on the runtime type of the actual argument.
+
+      ;; a bool-typed proc is selected when called with a boolean
+      (overload-bool-call
+       "let f = proc(bool b) if b then 10 else 20 in (f zero?(0))" 10)
+
+      ;; calling a slot the proc doesn't define is an error
+      (overload-missing-slot
+       "let f = proc(int x) x in (f zero?(0))" error)
+
+      ;; `overload` adds a second slot; dispatch then picks by argument type
+      (overload-adds-bool-slot
+       "let f = proc(int x) x
+        in begin
+             overload f with (bool b) if b then 1 else 2;
+             -((f 7), (f zero?(1)))
+           end" 5)
+
+      ;; `overload` can replace an existing slot
+      (overload-replaces-slot
+       "let f = proc(int x) x
+        in begin
+             overload f with (int x) -(x,1);
+             (f 9)
+           end" 8)
+
+      ;; the func slot is selected when the argument is itself a procedure
+      (overload-func-slot
+       "let id = proc(int x) x
+        in let f = proc(int x) -(x,100)
+           in begin
+                overload f with (func g) (g 5);
+                -((f 50), (f id))
+              end" -55)
+
+      ;; note - a proc-val holds 3 slots (int/bool/func); a typed proc fills only its slot, others are empty-proc.
+      ;; note - a call dispatches on the RUNTIME type of the argument; hitting an empty slot is an error.
+      ;; note - (f 10)->-(10,3)=7, (f zero?(5)=#f)->200, (f id)->(id 42)=42; -(-(7,200),42) = -235.
+      ;; all three slots on one procedure, dispatched three ways
+      (overload-three-way-put-in-preview
+       "let id = proc(int x) x
+        in let f = proc(int x) -(x,3)
+           in begin
+                overload f with (bool b) if b then 100 else 200;
+                overload f with (func g) (g 42);
+                -(-((f 10), (f zero?(5))), (f id))
+              end" -235)
+
+      ;; overloading something that isn't a procedure is an error
+      (overload-non-proc
+       "let f = 5 in overload f with (int x) x" error)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2025b91 — proc-ds : type

`2025b91-proc-ds-type.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_gettype-proc_

```
get-type(proc (x) x)
```
⇒ `proc`

Notes:

- get-type reflects a value's runtime type as a type-val: num | bool | proc.
- companion predicates isNum?/isBool?/isProc? return a bool for the same kinds.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -16,7 +16,9 @@
     (bool-val
       (boolean boolean?))
     (proc-val
-      (proc proc?)))
+      (proc proc?))
+    (type-val
+      (type symbol?)))
 
 ;;; extractors:
 
@@ -40,6 +42,22 @@
       (cases expval v
 	(proc-val (proc) proc)
 	(else (expval-extractor-error 'proc v)))))
+
+  ;; expval->type : ExpVal -> Symbol   (unwrap a type-val)
+  (define expval->type
+    (lambda (v)
+      (cases expval v
+        (type-val (type) type)
+        (else (expval-extractor-error 'type v)))))
+
+  ;; expval-type-of : ExpVal -> Symbol  (the runtime type name of ANY value)
+  (define expval-type-of
+    (lambda (v)
+      (cases expval v
+        (num-val  (n) 'num)
+        (bool-val (b) 'bool)
+        (proc-val (p) 'proc)
+        (type-val (t) 'type))))
 
   (define expval-extractor-error
     (lambda (variant value)
--- a/interp.scm
+++ b/interp.scm
@@ -73,6 +73,16 @@
                 (arg (value-of rand env)))
             (apply-procedure proc arg)))
 
+        ;; type — reflect the runtime type of a value
+        (get-type-exp (exp1)
+          (type-val (expval-type-of (value-of exp1 env))))
+        (isNum?-exp (exp1)
+          (bool-val (eqv? (expval-type-of (value-of exp1 env)) 'num)))
+        (isBool?-exp (exp1)
+          (bool-val (eqv? (expval-type-of (value-of exp1 env)) 'bool)))
+        (isProc?-exp (exp1)
+          (bool-val (eqv? (expval-type-of (value-of exp1 env)) 'proc)))
+
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -48,6 +48,13 @@
        ("(" expression expression ")")
        call-exp)
 
+      ;; type — reflect a value's runtime type; get-type yields a type value,
+      ;; the is*? predicates yield booleans
+      (expression ("get-type" "(" expression ")") get-type-exp)
+      (expression ("isNum?"   "(" expression ")") isNum?-exp)
+      (expression ("isBool?"  "(" expression ")") isBool?-exp)
+      (expression ("isProc?"  "(" expression ")") isProc?-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,19 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;; type — get-type yields a type name; isNum?/isBool?/isProc? yield booleans
+      (gettype-num   "get-type(5)" num)
+      (gettype-bool  "get-type(zero?(0))" bool)
+      ;; note - get-type reflects a value's runtime type as a type-val: num | bool | proc.
+      ;; note - companion predicates isNum?/isBool?/isProc? return a bool for the same kinds.
+      (gettype-proc-put-in-preview  "get-type(proc (x) x)" proc)
+      (isnum-yes     "isNum?(5)" #t)
+      (isnum-no      "isNum?(zero?(0))" #f)
+      (isbool-yes    "isBool?(zero?(0))" #t)
+      (isproc-yes    "isProc?(proc (x) x)" #t)
+      (isproc-no     "isProc?(5)" #f)
+      (type-in-if    "if isNum?(5) then 1 else 0" 1)
+      (gettype-of-let "let x = proc (y) y in get-type(x)" proc)
       ))
   )
--- a/top.scm
+++ b/top.scm
@@ -34,6 +34,7 @@
       (cond
         ((number? sloppy-val) (num-val sloppy-val))
         ((boolean? sloppy-val) (bool-val sloppy-val))
+        ((symbol? sloppy-val) (type-val sloppy-val))
         (else
          (eopl:error 'sloppy->expval
                      "Can't convert sloppy value to expval: ~s"
```

[↑ back to top](#feature-catalogue)

## 2025b93 — implicit-refs : uninit-complicated

`2025b93-implicit-refs-uninit-complicated.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_exam-example-1_

```
let z = ???
in
  let w = 50
  in
    let y = proc (a) -(a,5)
    in
      begin
        -(z,w);
        (y w);
        (y z);
        set z = 270;
        -(z,w);
        (y z)
      end
```
⇒ `265`

Notes:

- COMPLICATED variant: reproduces the exam transcript EXACTLY -- "uninitialized variable <x>" when read via a var-exp, generic "uninitialized value" when an uninit value is produced by any OTHER expression, and SILENT for the bare `???` literal.
- it does this by WRAPPING value-of and dispatching on the expression node that produced an uninit result -- a non-standard interp shape. The uninit-simple feature trades this exactness for a clearer one-line var-exp warning; both compute identical values.
- `???` is uninit-val, coerced to the sentinel 900 in any integer context.
- path-sensitivity in action: example 1 prints exactly z, z, a (each NAMED); example 2 prints one generic "value" warning (the uninit comes from (p 7), not a variable).
- the begin's earlier results are discarded; after `set z = 270`, the final (y z) = -(270,5) = 265.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,6 +19,7 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (uninit-val)
     )
 
 ;;; extractors:
@@ -27,6 +28,7 @@
     (lambda (v)
       (cases expval v
 	(num-val (num) num)
+	(uninit-val () 900)
 	(else (expval-extractor-error 'num v)))))
 
   (define expval->bool
--- a/interp.scm
+++ b/interp.scm
@@ -30,7 +30,35 @@
 
   ;; value-of : Exp * Env -> ExpVal
   ;; Page: 118, 119
-  (define value-of
+  ;; Note - this implementation is very weird
+  ;;        but it does print exactly what is needed
+  (define value-of (lambda (exp env)
+    (let
+      (
+        (val (value-of-exp exp env))
+      )
+      (begin
+        (cases expval val
+          (uninit-val ()
+            (cases expression exp
+              (var-exp (var)
+                (eopl:printf "Warning: you are using uninitialized variable ~a~%" var))
+              (uninit-exp ()
+                #t
+              )
+              (else
+                (eopl:printf "Warning: you are using uninitialized value~%")
+              )
+            )
+          )
+          (else val)
+        )
+        val
+      )
+    )
+  ))
+
+  (define value-of-exp
     (lambda (exp env)
       (cases expression exp
 
@@ -100,6 +128,8 @@
               (value-of exp1 env))
             (num-val 27)))
 
+        (uninit-exp () (uninit-val))
+
         )))
 
 
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,10 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      (expression
+        ("???")
+        uninit-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,53 @@
 in ((f 44) 33)"
 	12)
 
+      (uninit-reads-as-default
+        "-(???, 0)" 900)
+      (uninit-via-var
+        "let x = ??? in -(x, 1)" 899)
+      (uninit-in-arith
+        "let x = ??? in -(x, x)" 0)
+      (uninit-then-assigned
+        "let x = ??? in begin set x = 5; -(x, 1) end" 4)
+      (uninit-untouched-binding-is-fine
+        "let x = ??? in let y = 10 in y" 10)
+      ;; an uninit value flows into a procedure and is used there
+      (uninit-passed-to-proc
+        "let f = proc (a) -(a,5) in let x = ??? in (f x)" 895)
+      ;; reassigned twice, then read -> fully initialized, no warning
+      (uninit-reassigned-twice
+        "let x = ??? in begin set x = 10; set x = 20; -(x,5) end" 15)
+      ;; two independent uninit bindings, both coerced to 900
+      (uninit-two-bindings
+        "let x = ??? in let y = ??? in -(x, y)" 0)
+      ;; nested arithmetic: -(-(900,1),2)
+      (uninit-nested-arith
+        "-(-(???, 1), 2)" 897)
+
+      ;; note - COMPLICATED variant: reproduces the exam transcript EXACTLY -- "uninitialized variable <x>" when read via a var-exp, generic "uninitialized value" when an uninit value is produced by any OTHER expression, and SILENT for the bare `???` literal.
+      ;; note - it does this by WRAPPING value-of and dispatching on the expression node that produced an uninit result -- a non-standard interp shape. The uninit-simple feature trades this exactness for a clearer one-line var-exp warning; both compute identical values.
+      ;; note - `???` is uninit-val, coerced to the sentinel 900 in any integer context.
+      ;; note - path-sensitivity in action: example 1 prints exactly z, z, a (each NAMED); example 2 prints one generic "value" warning (the uninit comes from (p 7), not a variable).
+      ;; note - the begin's earlier results are discarded; after `set z = 270`, the final (y z) = -(270,5) = 265.
+      (exam-example-1-put-in-preview "
+let z = ???
+in
+  let w = 50
+  in
+    let y = proc (a) -(a,5)
+    in
+      begin
+        -(z,w);
+        (y w);
+        (y z);
+        set z = 270;
+        -(z,w);
+        (y z)
+      end" 265)
+      (exam-example-2 "
+let p = proc (a) ???
+in
+  -((p 7) , 20)" 880)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2025b93 — implicit-refs : uninit-simple

`2025b93-implicit-refs-uninit-simple.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_uninit-reads-as-default_

```
-(???, 0)
```
⇒ `900`

Notes:

- SIMPLE variant: the warning lives in var-exp and is GENERIC ("use of uninitialized value", no variable name). It does NOT reproduce the exam's exact transcript -- the uninit-complicated feature is the byte-exact version.
- the two variants compute IDENTICAL values; they differ ONLY in the warnings printed.
- `???` is uninit-val; in an integer context expval->num coerces it to the sentinel 900.
- it warns ONLY when reading uninit THROUGH a variable (var-exp); reading `???` directly, or using an uninit value produced by another expression, is silent.
- assigning the binding first makes later reads normal; an untouched uninit binding is harmless.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,6 +19,7 @@
       (proc proc?))
     (ref-val
       (ref reference?))
+    (uninit-val)
     )
 
 ;;; extractors:
@@ -27,6 +28,7 @@
     (lambda (v)
       (cases expval v
 	(num-val (num) num)
+	(uninit-val () 900)
 	(else (expval-extractor-error 'num v)))))
 
   (define expval->bool
--- a/interp.scm
+++ b/interp.scm
@@ -39,7 +39,14 @@
 
         ;\commentbox{ (value-of (var-exp \x{}) \r)
         ;              = (deref (apply-env \r \x{}))}
-        (var-exp (var) (deref (apply-env env var)))
+        (var-exp (var)
+          (let ((v1 (deref (apply-env env var))))
+            (cases expval v1
+              (uninit-val ()
+                (begin
+                  (eopl:printf "warning: use of uninitialized value~%")
+                  v1))
+              (else v1))))
 
         ;\commentbox{\diffspec}
         (diff-exp (exp1 exp2)
@@ -100,6 +107,8 @@
               (value-of exp1 env))
             (num-val 27)))
 
+        (uninit-exp () (uninit-val))
+
         )))
 
 
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,10 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      (expression
+        ("???")
+        uninit-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,39 @@
 in ((f 44) 33)"
 	12)
 
+      ;; note - SIMPLE variant: the warning lives in var-exp and is GENERIC ("use of uninitialized value", no variable name). It does NOT reproduce the exam's exact transcript -- the uninit-complicated feature is the byte-exact version.
+      ;; note - the two variants compute IDENTICAL values; they differ ONLY in the warnings printed.
+      ;; note - `???` is uninit-val; in an integer context expval->num coerces it to the sentinel 900.
+      ;; note - it warns ONLY when reading uninit THROUGH a variable (var-exp); reading `???` directly, or using an uninit value produced by another expression, is silent.
+      ;; note - assigning the binding first makes later reads normal; an untouched uninit binding is harmless.
+      (uninit-reads-as-default-put-in-preview
+        "-(???, 0)" 900)
+      (uninit-via-var
+        "let x = ??? in -(x, 1)" 899)
+      (uninit-in-arith
+        "let x = ??? in -(x, x)" 0)
+      (uninit-then-assigned
+        "let x = ??? in begin set x = 5; -(x, 1) end" 4)
+      (uninit-untouched-binding-is-fine
+        "let x = ??? in let y = 10 in y" 10)
+      ;; an uninit value flows into a procedure and is used there
+      (uninit-passed-to-proc
+        "let f = proc (a) -(a,5) in let x = ??? in (f x)" 895)
+      ;; reassigned twice, then read -> fully initialized, no warning
+      (uninit-reassigned-twice
+        "let x = ??? in begin set x = 10; set x = 20; -(x,5) end" 15)
+      ;; two independent uninit bindings, both coerced to 900
+      (uninit-two-bindings
+        "let x = ??? in let y = ??? in -(x, y)" 0)
+      ;; nested arithmetic: -(-(900,1),2)
+      (uninit-nested-arith
+        "-(-(???, 1), 2)" 897)
+      ;; same programs as the exam examples (values match; warnings differ from the exam)
+      (exam-example-1
+        "let z = ??? in let w = 50 in let y = proc (a) -(a,5)
+         in begin -(z,w); (y w); (y z); set z = 270; -(z,w); (y z) end" 265)
+      (exam-example-2
+        "let p = proc (a) ??? in -((p 7) , 20)" 880)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2025c93 — implicit-refs : event

`2025c93-implicit-refs-event.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_event-fires-handler_

```
let c = 0
in let e = event.create()
   in begin
        < e > += { proc(x) set c = x };
        (e 7);
        c
      end
```
⇒ `7`

Notes:

- an event is a list of procs; `event.create()` starts empty,
- `< e > += { ... }` appends handlers (returns 901), and calling the event `(e v)` fires every handler with v (returns 902).
- handlers run only for side effects; the call's own result is 902, so a handler's effect must be observed via mutable state (c).

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -19,10 +19,17 @@
       (proc proc?))
     (ref-val
       (ref reference?))
-    )
+    (event-val (procs (list-of proc?)))
+  )
 
 ;;; extractors:
 
+  (define expval->event (lambda (v)
+    (cases expval v
+      (event-val (procs) procs)
+      (else (eopl:error 'expval-event "expected event"))
+    )
+  ))
   (define expval->num
     (lambda (v)
       (cases expval v
--- a/interp.scm
+++ b/interp.scm
@@ -74,11 +74,6 @@
         (proc-exp (var body)
           (proc-val (procedure var body env)))
 
-        (call-exp (rator rand)
-          (let ((proc (expval->proc (value-of rator env)))
-                (arg (value-of rand env)))
-            (apply-procedure proc arg)))
-
         (letrec-exp (p-names b-vars p-bodies letrec-body)
           (value-of letrec-body
             (extend-env-rec* p-names b-vars p-bodies env)))
@@ -99,6 +94,60 @@
               (apply-env env var)
               (value-of exp1 env))
             (num-val 27)))
+
+        (event-create-exp ()
+          (event-val (list))
+        )
+
+        (event-add-exp (evnt procs)
+          (let*
+            (
+              (a (if (= (length procs) 0)
+                (eopl:error 'value-of "0 procs")
+                #t
+              ))
+              (evntref (apply-env env evnt))
+              (cprocs (expval->event (deref evntref)))
+              (nprocs (map
+                (lambda (p)
+                  (expval->proc (value-of p env))
+                )
+                procs
+              ))
+              (nevent (event-val (append cprocs nprocs)))
+            )
+            (begin
+              (setref! evntref nevent)
+              (num-val 901)
+            )
+          )
+        )
+
+        (call-exp (rator rand)
+          (let*
+            (
+              (ratorv (value-of rator env))
+              (randv (value-of rand env))
+            )
+            (cases expval ratorv
+              (proc-val (p)
+                (apply-procedure p randv)
+              )
+              (event-val (ps)
+                (begin
+                  (map
+                    (lambda (p)
+                      (apply-procedure p randv)
+                    )
+                    ps
+                  )
+                  (num-val 902)
+                )
+              )
+              (else (eopl:error 'value-of "call-exp invalid value"))
+            )
+          )
+        )
 
         )))
 
--- a/lang.scm
+++ b/lang.scm
@@ -64,6 +64,18 @@
         ("set" identifier "=" expression)
         assign-exp)
 
+      (expression
+        ("event.create()")
+        event-create-exp
+      )
+
+      (expression
+        (
+          "<" identifier ">" "+="
+          "{" (separated-list expression ";") "}"
+        )
+        event-add-exp
+      )
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -132,5 +132,53 @@
 in ((f 44) 33)"
 	12)
 
+      ;; event.create() makes an empty event; += returns 901
+      (event-add-returns-901
+        "let e = event.create() in < e > += { proc(x) x }" 901)
+      ;; calling an event returns 902
+      (event-call-returns-902
+        "let c = 0
+         in let e = event.create()
+            in begin < e > += { proc(x) set c = x }; (e 3) end" 902)
+      ;; note - an event is a list of procs; `event.create()` starts empty,
+      ;; note -   `< e > += { ... }` appends handlers (returns 901), and calling \
+      ;; note -   the event `(e v)` fires every handler with v (returns 902).
+      ;; note - handlers run only for side effects; the call's own result is 902, \
+      ;; note -   so a handler's effect must be observed via mutable state (c).
+      (event-fires-handler-put-in-preview
+        "let c = 0
+         in let e = event.create()
+            in begin
+                 < e > += { proc(x) set c = x };
+                 (e 7);
+                 c
+               end"
+        7)
+      ;; several handlers added in one += all fire
+      (event-multiple-handlers-one-add
+        "let c = 0
+         in let e = event.create()
+            in begin
+                 < e > += { proc(x) set c = -(c,-(0,x)) ;
+                            proc(x) set c = -(c,-(0,x)) };
+                 (e 10);
+                 c
+               end" 20)
+      ;; handlers added across separate += calls accumulate (append)
+      (event-handlers-accumulate
+        "let c = 0
+         in let e = event.create()
+            in begin
+                 < e > += { proc(x) set c = -(c,-(0,x)) };
+                 < e > += { proc(x) set c = -(c,-(0,x)) };
+                 (e 10);
+                 c
+               end" 20)
+      ;; an empty event fires nothing
+      (event-empty-fires-nothing
+        "let c = 5
+         in let e = event.create()
+            in begin (e 99); c end" 5)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## 2025c93 — proc-ds : foreach

`2025c93-proc-ds-foreach.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_foreach-filters-by-type_

```
foreach (int x) in [10, zero?(0), 30] do x
```
⇒ `(10 30)`

Notes:

- syntax: `foreach (<type> id) in [..] do body`; result is a LIST of body values, order preserved.
- elements are filtered by RUNTIME type vs declared type (int/bool/func); non-matching ones are skipped.
- here zero?(0) is a bool, so it is dropped from the int loop; body still sees the surrounding env. only elements whose runtime type matches the declared type are kept

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -16,7 +16,8 @@
     (bool-val
       (boolean boolean?))
     (proc-val
-      (proc proc?)))
+      (proc proc?))
+    (list-val (exps (list-of expval?))))
 
 ;;; extractors:
 
--- a/interp.scm
+++ b/interp.scm
@@ -73,6 +73,50 @@
                 (arg (value-of rand env)))
             (apply-procedure proc arg)))
 
+        (foreach-exp (typ id exps body)
+          (letrec
+            (
+              (typeexp->typename (lambda (t)
+                (cases type-exp t
+                  (type-exp-int () 'num)
+                  (type-exp-bool () 'bool)
+                  (type-exp-func () 'proc)
+                )
+              ))
+              (expval->typename (lambda (exp)
+                (cases expval exp
+                  (num-val (v) 'num)
+                  (bool-val (v) 'bool)
+                  (proc-val (v) 'proc)
+                  (else 'other)
+                )
+              ))
+              (typname (typeexp->typename typ))
+              (loop (lambda (lexps)
+                (if (null? lexps)
+                  (list)
+                  (let*
+                    (
+                      (exp (car lexps))
+                      (next (loop (cdr lexps)))
+                      (v1 (value-of exp env))
+                      (v1t (expval->typename v1))
+                    )
+                    (if (equal? typname v1t)
+                      (cons
+                        (value-of body (extend-env id v1 env))
+                        next
+                      )
+                      next
+                    )
+                  )
+                )
+              ))
+            )
+            (list-val (loop exps))
+          )
+        )
+
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -48,6 +48,18 @@
        ("(" expression expression ")")
        call-exp)
 
+      (expression
+        (
+          "foreach" "(" type-exp identifier ")" "in"
+          "[" (separated-list expression ",") "]"
+          "do" expression
+        )
+        foreach-exp
+      )
+      (type-exp ("int") type-exp-int)
+      (type-exp ("bool") type-exp-bool)
+      (type-exp ("func") type-exp-func)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,26 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;; foreach maps the body over the list, binding the id each iteration
+      (foreach-int-identity
+        "foreach (int x) in [10, 20, 30] do x" (10 20 30))
+      (foreach-int-body
+        "foreach (int x) in [10, 20, 30] do -(x,1)" (9 19 29))
+      ;; note - syntax: `foreach (<type> id) in [..] do body`; result is a LIST of body values, order preserved.
+      ;; note - elements are filtered by RUNTIME type vs declared type (int/bool/func); non-matching ones are skipped.
+      ;; note - here zero?(0) is a bool, so it is dropped from the int loop; body still sees the surrounding env.
+      ;; only elements whose runtime type matches the declared type are kept
+      (foreach-filters-by-type-put-in-preview
+        "foreach (int x) in [10, zero?(0), 30] do x" (10 30))
+      (foreach-bool-filter
+        "foreach (bool b) in [zero?(0), 5, zero?(1)] do b" (#t #f))
+      ;; no matching element yields the empty list
+      (foreach-none-match
+        "foreach (bool b) in [1, 2, 3] do b" ())
+      ;; the body sees the surrounding environment, not just the bound id
+      (foreach-closes-over-env
+        "let n = 100 in foreach (int x) in [1, 2] do -(x,n)" (-99 -98))
+
       ))
   )
--- a/top.scm
+++ b/top.scm
@@ -34,6 +34,7 @@
       (cond
         ((number? sloppy-val) (num-val sloppy-val))
         ((boolean? sloppy-val) (bool-val sloppy-val))
+        ((list? sloppy-val) (list-val (map sloppy->expval sloppy-val)))
         (else
          (eopl:error 'sloppy->expval
                      "Can't convert sloppy value to expval: ~s"
```

[↑ back to top](#feature-catalogue)

## let : dot

`let-dot.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_dot-many_

```
dot [2*3, 4*5]
```
⇒ `26`

Notes:

- DEMO of sllgen `separated-list` with a multi-symbol item.
- grammar: `dot [ <expr> * <expr> {, <expr> * <expr>}* ]`; the item is `expression "*" expression` (starts with a NONTERMINAL, several symbols) and `,` separates items.
- sllgen yields TWO parallel lists (lefts, rights); dot sums the pairwise products.
- each slot is a full expression: dot [ -(10,1) * 2 ] = (9*2) = 18.
- 1 item needs no comma ([7*1]); 0 items ([]) is allowed and sums to 0.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -64,6 +64,16 @@
             (value-of body
               (extend-env var val1 env))))
 
+        ;; lefts and rights are the two parallel lists sllgen built from the
+        ;; separated-list item `expression "*" expression`. Sum the products.
+        (dot-exp (lefts rights)
+          (num-val
+            (apply +
+              (map (lambda (l r)
+                     (* (expval->num (value-of l env))
+                        (expval->num (value-of r env))))
+                   lefts rights))))
+
         )))
 
 
--- a/lang.scm
+++ b/lang.scm
@@ -42,6 +42,12 @@
        ("let" identifier "=" expression "in" expression)
        let-exp)
 
+      ;; the separated-list ITEM is `expression "*" expression` -- it starts with
+      ;; a nonterminal and is several symbols, so sllgen yields TWO parallel lists.
+      (expression
+       ("dot" "[" (separated-list expression "*" expression ",") "]")
+       dot-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -55,5 +55,17 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
+      ;; note - DEMO of sllgen `separated-list` with a multi-symbol item.
+      ;; note - grammar: `dot [ <expr> * <expr> {, <expr> * <expr>}* ]`; the item is `expression "*" expression` (starts with a NONTERMINAL, several symbols) and `,` separates items.
+      ;; note - sllgen yields TWO parallel lists (lefts, rights); dot sums the pairwise products.
+      ;; note - each slot is a full expression: dot [ -(10,1) * 2 ] = (9*2) = 18.
+      ;; note - 1 item needs no comma ([7*1]); 0 items ([]) is allowed and sums to 0.
+      (dot-many-put-in-preview
+        "dot [2*3, 4*5]" 26)
+      (dot-single        "dot [7*1]" 7)
+      (dot-empty         "dot []" 0)
+      (dot-expr-slots    "dot [ -(10,1) * 2 ]" 18)
+      (dot-uses-env      "let a = 5 in dot [a*2, a*a]" 35)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## let : poly

`let-poly.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_poly-add-sames_

```
coeff(add-poly(make-poly(3,4), make-poly(5,4)), 4)
```
⇒ `8`

Notes:

- make-poly(a,n) is one monomial a*x^n; add-poly builds an unsimplified sum tree
- coeff(p, m) sums coefficients of ALL terms with exponent m (missing exponent -> 0)
- zero-poly? is true only if every monomial coeff is 0; it does NOT cancel like terms, so add-poly(make-poly(3,4), make-poly(-3,4)) is NOT zero-poly even though it sums to 0

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -12,7 +12,9 @@
     (num-val
       (value number?))
     (bool-val
-      (boolean boolean?)))
+      (boolean boolean?))
+    (poly-val
+      (p poly?)))
 
 ;;; extractors:
 
@@ -36,6 +38,40 @@
     (lambda (variant value)
       (eopl:error 'expval-extractors "Looking for a ~s, found ~s"
 	variant value)))
+
+  ;; poly — polynomial ADT (q2):  zero | a*x^n | p + q
+  (define-datatype poly poly?
+    (pzero)
+    (pmono (a integer?) (n integer?))
+    (padd (p poly?) (q poly?)))
+
+  (define poly-degree
+    (lambda (p)
+      (cases poly p
+        (pzero () 0)
+        (pmono (a n) n)
+        (padd (q t) (max (poly-degree q) (poly-degree t))))))
+
+  (define poly-coeff
+    (lambda (p m)
+      (cases poly p
+        (pzero () 0)
+        (pmono (a n) (if (eqv? n m) a 0))
+        (padd (q t) (+ (poly-coeff q m) (poly-coeff t m))))))
+
+  (define poly-zero?
+    (lambda (p)
+      (cases poly p
+        (pzero () #t)
+        (pmono (a n) (eqv? a 0))
+        (padd (q t) (and (poly-zero? q) (poly-zero? t))))))
+
+  ;; expval->poly : ExpVal -> Poly
+  (define expval->poly
+    (lambda (v)
+      (cases expval v
+        (poly-val (p) p)
+        (else (expval-extractor-error 'poly v)))))
 
 ;;;;;;;;;;;;;;;; environment structures ;;;;;;;;;;;;;;;;
 
--- a/interp.scm
+++ b/interp.scm
@@ -64,6 +64,22 @@
             (value-of body
               (extend-env var val1 env))))
 
+        ;; poly — build/query polynomial values
+        (zero-poly-exp () (poly-val (pzero)))
+        (make-poly-exp (ae ne)
+          (poly-val (pmono (expval->num (value-of ae env))
+                           (expval->num (value-of ne env)))))
+        (add-poly-exp (pe qe)
+          (poly-val (padd (expval->poly (value-of pe env))
+                          (expval->poly (value-of qe env)))))
+        (degree-exp (pe)
+          (num-val (poly-degree (expval->poly (value-of pe env)))))
+        (coeff-exp (pe me)
+          (num-val (poly-coeff (expval->poly (value-of pe env))
+                               (expval->num (value-of me env)))))
+        (zero-poly?-exp (pe)
+          (bool-val (poly-zero? (expval->poly (value-of pe env)))))
+
         )))
 
 
--- a/lang.scm
+++ b/lang.scm
@@ -42,6 +42,14 @@
        ("let" identifier "=" expression "in" expression)
        let-exp)
 
+      ;; poly — a small polynomial ADT exposed as language values
+      (expression ("poly-zero") zero-poly-exp)
+      (expression ("make-poly" "(" expression "," expression ")") make-poly-exp)
+      (expression ("add-poly" "(" expression "," expression ")") add-poly-exp)
+      (expression ("degree" "(" expression ")") degree-exp)
+      (expression ("coeff" "(" expression "," expression ")") coeff-exp)
+      (expression ("zero-poly?" "(" expression ")") zero-poly?-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -55,5 +55,20 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
+      ;; poly — a*x^n polynomials with add/degree/coeff/zero?  (p = 3x^4 + 2x^1)
+      (poly-degree-1   "degree(add-poly(make-poly(3,4), make-poly(2,1)))" 4)
+      (poly-coeff-hi   "coeff(add-poly(make-poly(3,4), make-poly(2,1)), 4)" 3)
+      (poly-coeff-lo   "coeff(add-poly(make-poly(3,4), make-poly(2,1)), 1)" 2)
+      (poly-coeff-none "coeff(add-poly(make-poly(3,4), make-poly(2,1)), 9)" 0)
+      ;; note - make-poly(a,n) is one monomial a*x^n; add-poly builds an unsimplified sum tree
+      ;; note - coeff(p, m) sums coefficients of ALL terms with exponent m (missing exponent -> 0)
+      ;; note - zero-poly? is true only if every monomial coeff is 0; it does NOT cancel like terms,
+      ;;        so add-poly(make-poly(3,4), make-poly(-3,4)) is NOT zero-poly even though it sums to 0
+      (poly-add-sames-put-in-preview "coeff(add-poly(make-poly(3,4), make-poly(5,4)), 4)" 8)
+      (poly-not-zero   "zero-poly?(add-poly(make-poly(3,4), make-poly(2,1)))" #f)
+      (poly-zero-lit   "zero-poly?(poly-zero)" #t)
+      (poly-zero-mono  "zero-poly?(make-poly(0,2))" #t)
+      (poly-in-let     "let p = make-poly(7,3) in degree(p)" 3)
+
       ))
   )
```

[↑ back to top](#feature-catalogue)

## proc-ds : cond

`proc-ds-cond.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_cond-second_

```
cond
  zero?(1) ==> 1
  zero?(0) ==> 2
end
```
⇒ `2`

Notes:

- clauses scanned top-to-bottom; first true test wins (here clause 2).
- tests must be bool (dynamic typecheck); no true clause -> error.
- only the chosen clause's result is evaluated; later results may be unbound.

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -73,6 +73,18 @@
                 (arg (value-of rand env)))
             (apply-procedure proc arg)))
 
+        ;; cond — evaluate each test in order, run the first true clause's result
+        (cond-exp (tests results)
+          (letrec
+            ((eval-clauses
+               (lambda (ts rs)
+                 (cond
+                   ((null? ts) (eopl:error 'cond-exp "no true clause"))
+                   ((expval->bool (value-of (car ts) env))
+                    (value-of (car rs) env))
+                   (else (eval-clauses (cdr ts) (cdr rs)))))))
+            (eval-clauses tests results)))
+
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -48,6 +48,11 @@
        ("(" expression expression ")")
        call-exp)
 
+      ;; cond — clauses of  test ==> result, first true test wins
+      (expression
+       ("cond" (arbno expression "==>" expression) "end")
+       cond-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,20 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;; cond — first clause whose test is true wins; no true clause -> error
+      (cond-first  "cond zero?(0) ==> 1 zero?(1) ==> 2 end" 1)
+      ;; note - clauses scanned top-to-bottom; first true test wins (here clause 2).
+      ;; note - tests must be bool (dynamic typecheck); no true clause -> error.
+      ;; note - only the chosen clause's result is evaluated; later results may be unbound.
+      (cond-second-put-in-preview
+       "cond
+          zero?(1) ==> 1
+          zero?(0) ==> 2
+        end"
+       2)
+      (cond-order  "cond zero?(0) ==> 1 zero?(0) ==> 2 end" 1)
+      (cond-none   "cond zero?(1) ==> 1 zero?(2) ==> 2 end" error)
+      (cond-lazy   "cond zero?(0) ==> 7 zero?(0) ==> foo end" 7)
       ))
   )
```

[↑ back to top](#feature-catalogue)

## proc-ds : fold

`proc-ds-fold.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_fold-decrement_

```
fold proc (x) -(x,1) 0 [5, 6, 7]
```
⇒ `15`

Notes:

- syntax: `fold <proc> <acc> [v1, v2, ...]`; result = sum over the list of (proc v_i), an int.
- the acc operand (here 0) is evaluated/bound but IGNORED — it does not seed the sum.
- empty list -> 0; here (4)+(5)+(6)=15 from proc(x)=-(x,1).

```diff
--- a/interp.scm
+++ b/interp.scm
@@ -73,6 +73,31 @@
                 (arg (value-of rand env)))
             (apply-procedure proc arg)))
 
+        ;; fold — sum of (proc value) over the list; acc is bound but ignored
+        (fold-exp (fold-raw-proc fold-raw-acc fold-raw-vals)
+          (let
+            (
+              (proc (expval->proc (value-of fold-raw-proc env)))
+            )
+            (letrec
+              (
+                (loop
+                  (lambda (vals)
+                    (if (null? vals)
+                      0
+                      (+
+                        (expval->num (apply-procedure proc (value-of (car vals) env)))
+                        (loop (cdr vals))
+                      )
+                    )
+                  )
+                )
+              )
+              (num-val (loop fold-raw-vals))
+            )
+          )
+        )
+
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -48,6 +48,11 @@
        ("(" expression expression ")")
        call-exp)
 
+      ;; fold — sum of proc1 applied to each value; acc is bound but ignored
+      (expression
+       ("fold" expression expression "[" (separated-list expression ",") "]")
+       fold-exp)
+
       ))
 
   ;;;;;;;;;;;;;;;; sllgen boilerplate ;;;;;;;;;;;;;;;;
--- a/tests.scm
+++ b/tests.scm
@@ -73,5 +73,14 @@
     t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
 in let times4 = (fix t4m)
    in (times4 3)" 12)
+
+      ;; note - syntax: `fold <proc> <acc> [v1, v2, ...]`; result = sum over the list of (proc v_i), an int.
+      ;; note - the acc operand (here 0) is evaluated/bound but IGNORED — it does not seed the sum.
+      ;; note - empty list -> 0; here (4)+(5)+(6)=15 from proc(x)=-(x,1).
+      (fold-decrement-put-in-preview
+       "fold proc (x) -(x,1) 0 [5, 6, 7]" 15)
+      (fold-identity  "fold proc (x) x 100 [1, 2, 3, 4]" 10)
+      (fold-empty     "fold proc (x) x 0 []" 0)
+      (fold-single    "fold proc (x) -(x,1) 0 [5]" 4)
       ))
   )
```

[↑ back to top](#feature-catalogue)

## proc-ds : overload-count

`proc-ds-overload-count.diff`

**Preview** — what the feature must do (from `*-put-in-preview` tests):

_overload-both_

```
let f = overload proc [x] -> -(x,1) ;
                 [x y] -> -(x,y) ;
in -((f 30), (f 10 3))
```
⇒ `22`

Notes:

- one value bundles many proc clauses; the call's ARG COUNT selects the clause.
- clauses may have any arity (incl. 0); no clause matching the arity → error.

```diff
--- a/data-structures.scm
+++ b/data-structures.scm
@@ -16,7 +16,7 @@
     (bool-val
       (boolean boolean?))
     (proc-val
-      (proc proc?)))
+      (proc (list-of proc?))))
 
 ;;; extractors:
 
@@ -52,7 +52,7 @@
   ;; procedure : Var * Exp * Env -> Proc
   (define-datatype proc proc?
     (procedure
-      (var symbol?)
+      (vars (list-of symbol?))
       (body expression?)
       (env environment?)))
 
--- a/interp.scm
+++ b/interp.scm
@@ -65,14 +65,55 @@
             (value-of body
               (extend-env var val1 env))))
 
-        (proc-exp (var body)
-          (proc-val (procedure var body env)))
+        (overload-proc-exp (ids bodies)
+          (letrec
+            (
+              (loop (lambda (ids2 bodies2)
+                (if (null? ids2)
+                  (list)
+                  (cons
+                    (procedure (car ids2) (car bodies2) env)
+                    (loop (cdr ids2) (cdr bodies2))
+                  )
+                )
+              ))
+            )
+            (proc-val (loop ids bodies))
+          )
+        )
 
-        (call-exp (rator rand)
-          (let ((proc (expval->proc (value-of rator env)))
-                (arg (value-of rand env)))
-            (apply-procedure proc arg)))
-
+        (call-exp (rator rands)
+          (letrec
+            (
+              (procs (expval->proc (value-of rator env)))
+              (randsvals (map
+                  (lambda (v) (value-of v env))
+                  rands
+              ))
+              (randslen (length rands))
+              (extend-env* (lambda (vars vals env2)
+                (if (null? vars)
+                  env2
+                  (extend-env (car vars) (car vals) (extend-env* (cdr vars) (cdr vals) env2))
+                )
+              ))
+              (loop (lambda (procs2)
+                (if (null? procs2)
+                  (eopl:error 'value-of "no overload fits")
+                  (cases proc (car procs2)
+                      (procedure (vars body env)
+                        (if (= (length vars) randslen)
+                          (value-of body (extend-env* vars randsvals env))
+                          (loop (cdr procs2))
+                        )
+                      )
+                    )
+                )
+              ))
+            )
+            (loop procs)
+          )
+        )
         )))
 
   ;; apply-procedure : Proc * ExpVal -> ExpVal
--- a/lang.scm
+++ b/lang.scm
@@ -41,11 +41,11 @@
        let-exp)
 
       (expression
-       ("proc" "(" identifier ")" expression)
-       proc-exp)
+       ("overload" "proc" (arbno "[" (arbno identifier) "]" "->" expression ";"))
+       overload-proc-exp)
 
       (expression
-       ("(" expression expression ")")
+       ("(" expression (arbno expression) ")")
        call-exp)
 
       ))
--- a/tests.scm
+++ b/tests.scm
@@ -55,23 +55,49 @@
       (check-shadowing-in-body "let x = 3 in let x = 4 in x" 4)
       (check-shadowing-in-rhs "let x = 3 in let x = -(x,1) in x" 2)
 
-      ;; simple applications
-      (apply-proc-in-rator-pos "(proc(x) -(x,1)  30)" 29)
-      (apply-simple-proc "let f = proc (x) -(x,1) in (f 30)" 29)
-      (let-to-proc-1 "(proc(f)(f 30)  proc(x)-(x,1))" 29)
+      ;; simple applications (procs are now `overload proc [args] -> body ;`)
+      (apply-proc-in-rator-pos "(overload proc [x] -> -(x,1) ; 30)" 29)
+      (apply-simple-proc "let f = overload proc [x] -> -(x,1) ; in (f 30)" 29)
+      (let-to-proc-1
+        "(overload proc [f] -> (f 30) ; overload proc [x] -> -(x,1) ;)" 29)
 
-
-      (nested-procs "((proc (x) proc (y) -(x,y)  5) 6)" -1)
-      (nested-procs2 "let f = proc(x) proc (y) -(x,y) in ((f -(10,5)) 6)"
-        -1)
+      (nested-procs
+        "((overload proc [x] -> overload proc [y] -> -(x,y) ; ; 5) 6)" -1)
+      (nested-procs2
+        "let f = overload proc [x] -> overload proc [y] -> -(x,y) ; ;
+         in ((f -(10,5)) 6)" -1)
 
       (y-combinator-1 "
-let fix =  proc (f)
-            let d = proc (x) proc (z) ((f (x x)) z)
-            in proc (n) ((f (d d)) n)
-in let
-    t4m = proc (f) proc(x) if zero?(x) then 0 else -((f -(x,1)),-4)
-in let times4 = (fix t4m)
-   in (times4 3)" 12)
+let fix = overload proc [f] ->
+            let d = overload proc [x] -> overload proc [z] -> ((f (x x)) z) ; ;
+            in overload proc [n] -> ((f (d d)) n) ; ;
+in let t4m = overload proc [f] ->
+               overload proc [x] -> if zero?(x) then 0 else -((f -(x,1)),-4) ; ;
+   in let times4 = (fix t4m)
+      in (times4 3)" 12)
+
+      ;; overloading: pick the clause whose arity matches the call
+      (overload-arity-1
+        "let f = overload proc [x] -> -(x,1) ;
+                          [x y] -> -(x,y) ;
+         in (f 30)" 29)
+      (overload-arity-2
+        "let f = overload proc [x] -> -(x,1) ;
+                          [x y] -> -(x,y) ;
+         in (f 10 3)" 7)
+      ;; note - one value bundles many proc clauses; the call's ARG COUNT selects the clause.
+      ;; note - clauses may have any arity (incl. 0); no clause matching the arity → error.
+      (overload-both-put-in-preview
+        "let f = overload proc [x] -> -(x,1) ;
+                          [x y] -> -(x,y) ;
+         in -((f 30), (f 10 3))" 22)
+      ;; a zero-argument clause, selected by a zero-argument call
+      (overload-zero-arg
+        "let f = overload proc [] -> 5 ; [x] -> x ; in (f)" 5)
+      (overload-three-args
+        "let f = overload proc [a b c] -> -(-(a,b),c) ; in (f 10 3 2)" 5)
+      ;; no clause matches the call's arity → error
+      (overload-no-fit-error
+        "let f = overload proc [x] -> x ; in (f 1 2)" error)
       ))
   )
```

[↑ back to top](#feature-catalogue)
