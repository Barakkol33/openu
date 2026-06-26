#!/usr/bin/env python3
"""main.py - a tiny study harness for the EOPL interpreters in this tree.

Workflow: copy a canonical language into a working *env*, hand-edit it to add a
*feature*, then capture/replay that feature as a portable unified diff.

  init   <lang> <env>       copy chapter*/<lang> -> envs/<lang>-<env>
  import <feature> <env>    apply features/[<testid>-]<lang>-<feature>.diff onto the env
  export <env> <feature>    diff the env vs its pristine lang -> matching feature file
                            (<feature> is a substring; unique hit wins, else lists)
  diff   <env>              print the env's current diff to stdout
  test   <env>              run one env's Racket test suite (racket -e ... run-all)
  test-all                  apply every feature to a fresh env, run tests, clean up
  export-all                concatenate all feature diffs into one Markdown file
  smoke                     run test-all, export-all, infer on an example
  infer  [args...]          Hindley-Milner type inference (inlined)
  list                      show known langs / envs / features

Pure standard library, no external `diff`/`patch` binaries and no subprocess, so
it runs the same on Linux/macOS/Windows.
"""

import argparse
import difflib
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

SUMMARY_ROOT = Path(__file__).resolve().parent          # .../summary
FEATURES_DIR = SUMMARY_ROOT / "features"

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

# A feature file may carry a leading exam test-id, e.g. '2021b78-explicit-refs-arr':
# four digits, a semester letter, then the paper/moed token, followed by '-'.
TESTID_RE = re.compile(r"^\d{4}[a-z][a-z0-9]*-")


# ---------------------------------------------------------------- utilities

def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def slug(lang):
    """Lang name -> a filesystem-safe token (replace any '/')."""
    return lang.replace("/", "-")


def fslug(lang):
    """Short lang token used in feature/env names: drop a trailing '-lang'
    (let-lang -> let, letrec-lang -> letrec, proc-ds -> proc-ds)."""
    s = slug(lang)
    return s[:-5] if s.endswith("-lang") else s


def read_lines(path):
    """File -> list of newline-free lines; missing file -> []. read_text uses
    universal newlines, so CRLF/LF both become clean lines."""
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------- lang discovery

def discover_langs():
    """{name: dir} for every leaf language (a dir with both lang.scm + top.scm)
    under summary/chapter*/. Name is the path relative to its chapter dir."""
    langs = {}
    for chap in sorted(SUMMARY_ROOT.glob("chapter*")):
        if not chap.is_dir():
            continue
        for langfile in chap.rglob("lang.scm"):
            d = langfile.parent
            if (d / "top.scm").exists():
                name = d.relative_to(chap).as_posix()
                langs[name] = d
    return langs


def resolve_lang(name, langs):
    """Exact match, else a unique suffix match (e.g. 'ds-rep')."""
    if name in langs:
        return name
    hits = [k for k in langs if k.endswith(name)]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        die(f"ambiguous lang '{name}': matches {', '.join(sorted(hits))}")
    die(f"unknown lang '{name}'. known: {', '.join(sorted(langs))}")


def match_lang(name, langs):
    """Longest known lang whose fslug == name or is an 'fslug-' prefix; else None.
    Used to recover the base lang from an env folder or a feature filename stem."""
    best = None
    for lang in langs:
        s = fslug(lang)
        if name == s or name.startswith(s + "-"):
            if best is None or len(fslug(best)) < len(s):
                best = lang
    return best


def strip_testid(stem):
    """Drop a leading exam test-id prefix ('2021b78-...') if present, so the rest
    of the harness keeps seeing plain '<lang>-<feature>' stems."""
    return TESTID_RE.sub("", stem, count=1)


def testid_of(stem):
    """The leading exam test-id ('2021b78') of a feature stem, or '' if none."""
    m = TESTID_RE.match(stem)
    return m.group(0)[:-1] if m else ""


def gh_anchor(text):
    """GitHub-style heading slug: lowercase, drop punctuation, spaces -> hyphens.
    Used so the catalogue's index links match its section headings."""
    s = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return s.replace(" ", "-")


def split_feature(stem, langs):
    """'2021b78-implicit-refs-const' / 'implicit-refs-const'
    -> ('implicit-refs', 'const'); (None, stem) if no lang."""
    stem = strip_testid(stem)
    lang = match_lang(stem, langs)
    if lang is None:
        return None, stem
    return lang, stem[len(fslug(lang)) + 1:]


def lang_of_env(env_name, langs):
    """Recover the source lang from an env folder named <slug(lang)>-<env>."""
    best = match_lang(env_name, langs)
    if best is None:
        die(f"cannot tell which lang env '{env_name}' is "
            f"(expected name '<lang>-<something>')")
    return best


def feature_path(lang, feature):
    return FEATURES_DIR / f"{fslug(lang)}-{feature}.diff"


def all_features():
    """Every feature diff on disk, sorted by name."""
    return sorted(FEATURES_DIR.glob("*.diff")) if FEATURES_DIR.exists() else []


def lang_features(lang):
    """Feature files belonging to <lang> (test-id prefix ignored)."""
    base = fslug(lang)
    out = []
    for p in all_features():
        stem = strip_testid(p.stem)
        if stem == base or stem.startswith(base + "-"):
            out.append(p)
    return out


def resolve_feature(lang, feature):
    """The feature file for <lang>:<feature>, tolerating a test-id prefix; None if
    absent. Exact feature name (e.g. 'const'), not a substring."""
    want = f"{fslug(lang)}-{feature}"
    for p in lang_features(lang):
        if strip_testid(p.stem) == want:
            return p
    return None


def search_features(lang, needle):
    """Feature files of <lang> whose (test-id-prefixed) filename contains <needle>,
    case-insensitively. So both an exam id ('2025c93') and a feature word ('event')
    match. Empty needle returns all of the lang's features."""
    nl = needle.lower()
    return [p for p in lang_features(lang) if nl in p.stem.lower()]


def base_dir():
    return SUMMARY_ROOT / "envs"


# ----------------------------------------------------------- diff (export)

def make_diff(src, env):
    """Unified diff turning a pristine <src> lang into the current <env>, using
    git-style a/<rel> b/<rel> headers. Covers added/removed/edited .scm files."""
    rels = set()
    for root in (src, env):
        for p in root.rglob("*.scm"):
            rels.add(p.relative_to(root).as_posix())
    out = []
    for rel in sorted(rels):
        # trailing whitespace is never meaningful in these Scheme sources, so
        # normalize it away: whitespace-only edits don't show up as changes,
        # and emitted context/+ lines are clean. apply_hunks matches the same
        # way, so diffs stay importable against pristine regardless of EOL ws.
        a = [ln.rstrip() for ln in read_lines(src / rel)]
        b = [ln.rstrip() for ln in read_lines(env / rel)]
        if a != b:
            out.extend(difflib.unified_diff(
                a, b, fromfile=f"a/{rel}", tofile=f"b/{rel}", lineterm=""))
    # every emitted line is newline-free, so we own the joining: no glued lines
    # at file boundaries even when a file lacks a trailing newline.
    return "\n".join(out) + "\n" if out else ""


# ---------------------------------------------------------- patch (import)

def _strip_ab(header):
    """'a/lang.scm' / 'b/lang.scm' -> 'lang.scm'."""
    h = header.strip()
    if h.startswith(("a/", "b/")):
        return h[2:]
    return h


def parse_patch(text):
    """-> [(relpath, [(src_start, body_lines), ...]), ...]."""
    lines = text.split("\n")                # text is all-LF, lines are newline-free
    sections, i, n = [], 0, len(lines)
    while i < n:
        if lines[i].startswith("--- ") and i + 1 < n and lines[i + 1].startswith("+++ "):
            rel = _strip_ab(lines[i + 1][4:]) or _strip_ab(lines[i][4:])
            i += 2
            hunks = []
            while i < n and not lines[i].startswith("--- "):
                m = HUNK_RE.match(lines[i])
                if not m:
                    i += 1
                    continue
                src_start = int(m.group(1))
                i += 1
                body = []
                while i < n and not lines[i].startswith(("--- ", "@@")):
                    body.append(lines[i])
                    i += 1
                hunks.append((src_start, body))
            sections.append((rel, hunks))
        else:
            i += 1
    return sections


def apply_hunks(src_lines, hunks, rel):
    """Apply one file's hunks by exact context match; raise on any mismatch."""
    result, idx = [], 0
    for src_start, body in hunks:
        start = src_start - 1 if src_start > 0 else 0
        if start < idx:
            raise ValueError(f"{rel}: overlapping hunks")
        result.extend(src_lines[idx:start])
        idx = start
        for bline in body:
            if bline == "" or bline[0] == "\\":    # split artifact / no-newline marker
                continue
            tag, content = bline[0], bline[1:]
            if tag == " " or tag == "-":
                if idx >= len(src_lines) or src_lines[idx].rstrip() != content.rstrip():
                    raise ValueError(
                        f"{rel}: context mismatch near source line {idx + 1} "
                        f"(env has diverged from the feature's baseline)")
                idx += 1
                if tag == " ":
                    result.append(content)
            elif tag == "+":
                result.append(content)
    result.extend(src_lines[idx:])
    return result


def apply_diff(text, env):
    """Apply a feature diff onto <env>. Builds every file in memory first; if
    any hunk fails to match, nothing is written. -> sorted list of touched rels."""
    sections = parse_patch(text)
    if not sections:
        die("not a valid feature diff (no file sections found)")
    planned = {}
    for rel, hunks in sections:
        target = env / rel
        new_lines = apply_hunks(read_lines(target), hunks, rel)
        # written normalized: LF + trailing newline (portable across platforms)
        planned[rel] = "\n".join(new_lines) + "\n" if new_lines else ""
    for rel, content in planned.items():
        target = env / rel
        if content == "" and target.exists():
            target.unlink()                         # feature removed the file
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    return sorted(planned)


# ---------------------------------------------------------------- commands

def cmd_init(args):
    langs = discover_langs()
    lang = resolve_lang(args.lang, langs)
    if "/" in args.env or "\\" in args.env or args.env in ("", ".", ".."):
        die(f"bad env name '{args.env}' (must be a single folder name)")
    dest = base_dir() / f"{fslug(lang)}-{args.env}"
    if dest.exists():
        if not args.force:
            die(f"env already exists: {dest} (use --force to overwrite)")
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(langs[lang], dest)
    n = sum(1 for _ in dest.rglob("*.scm"))
    print(f"init: {dest.name}  (from {lang}, {n} .scm files)")
    return 0


def cmd_import(args):
    langs = discover_langs()
    env = base_dir() / args.env
    if not env.is_dir():
        die(f"no such env: {env}")
    lang = lang_of_env(args.env, langs)
    feat = resolve_feature(lang, args.feature)
    if feat is None:
        avail = sorted(p.name for p in lang_features(lang))
        die(f"no feature '{args.feature}' for lang '{lang}'. "
            + (f"available: {', '.join(avail)}" if avail else "no features yet"))
    try:
        touched = apply_diff(feat.read_text(encoding="utf-8"), env)
    except ValueError as e:
        die(f"{e}\nnothing was written.")
    print(f"import: applied {feat.name} -> {args.env}")
    for rel in touched:
        print(f"  {rel}")
    return 0


def run_env_tests(env):
    """Run an env's Racket suite. -> (passed: bool, reason: str)."""
    if not shutil.which("racket"):
        return False, "racket not on PATH (cannot verify tests)"
    cp = subprocess.run(["racket", "-e", '(require "top.scm") (run-all)'],
                        cwd=str(env), capture_output=True, text=True)
    raw = cp.stdout + cp.stderr
    low = raw.lower()
    if cp.returncode == 0 and "no bugs found" in low and "incorrect" not in low:
        return True, ""
    reason = next((ln.strip() for ln in raw.splitlines()
                   if "incorrect" in ln.lower() or "error" in ln.lower()), "")
    return False, reason or f"exit {cp.returncode}, 'no bugs found' not in output"


def cmd_export(args):
    langs = discover_langs()
    env = base_dir() / args.env
    if not env.is_dir():
        die(f"no such env: {env}")
    lang = lang_of_env(args.env, langs)
    text = make_diff(langs[lang], env)
    if not text:
        die(f"nothing to export: '{args.env}' is identical to pristine {lang}")
    # `feature` is a substring matched against this lang's feature files. A unique
    # hit is the file we overwrite; otherwise list the candidates so the user can
    # narrow it down (or, with no hit, see what exists).
    if args.new:
        feat = feature_path(lang, args.feature)
        if feat.exists():
            die(f"--new but {feat.name} already exists; export without --new to overwrite it")
    else:
        matches = search_features(lang, args.feature)
        if len(matches) != 1:
            names = matches if matches else lang_features(lang)
            head = (f"'{args.feature}' matches {len(matches)} features for lang '{lang}'"
                    if matches else
                    f"no feature for lang '{lang}' matches '{args.feature}' "
                    f"(pass --new to create features/{fslug(lang)}-{args.feature}.diff). existing")
            die(head + ":\n  " + ("\n  ".join(p.name for p in names) or "(none)"))
        feat = matches[0]
    if not args.no_verify:
        ok, reason = run_env_tests(env)
        if not ok:
            die(f"not exporting: '{args.env}' tests did not pass -- {reason}\n"
                f"fix the env, or pass --no-verify to export anyway.")
    feat.write_text(text, encoding="utf-8")
    print(f"export: {args.env} -> {feat.relative_to(SUMMARY_ROOT)}")
    return 0


def cmd_infer(rest):
    return infer_main(rest)


def cmd_list(args):
    langs = discover_langs()
    show_all = not (args.langs or args.envs or args.features)
    if args.langs or show_all:
        print("langs:")
        for name in sorted(langs):
            print(f"  {name:22} {langs[name].relative_to(SUMMARY_ROOT)}")
    if args.envs or show_all:
        print("envs:")
        base = base_dir()
        found = False
        if base.is_dir():
            for d in sorted(p for p in base.iterdir() if p.is_dir()):
                lang = match_lang(d.name, langs)
                if lang:
                    found = True
                    print(f"  {d.name:28} -> {lang}")
        if not found:
            print(f"  (none in {base})")
    if args.features or show_all:
        print("features:")
        feats = sorted(FEATURES_DIR.glob("*.diff")) if FEATURES_DIR.exists() else []
        if not feats:
            print("  (none)")
        for f in feats:
            lang, feature = split_feature(f.stem, langs)
            if lang:
                print(f"  {f.name:30} {lang} : {feature}")
            else:
                print(f"  {f.name}")
    return 0


def cmd_diff(args):
    """Like export, but print the env's diff to stdout instead of writing a file."""
    langs = discover_langs()
    env = base_dir() / args.env
    if not env.is_dir():
        die(f"no such env: {env}")
    lang = lang_of_env(args.env, langs)
    text = make_diff(langs[lang], env)
    if not text:
        print(f"# (no changes: '{args.env}' is identical to pristine {lang})")
        return 0
    sys.stdout.write(text)
    return 0


def cmd_test_all(args):
    """Apply every feature to a fresh env of its base lang, run the test suite,
    then remove the env. Reports PASS/FAIL per feature."""
    if not shutil.which("racket"):
        die("racket not found on PATH (needed to run tests)")
    langs = discover_langs()
    feats = sorted(FEATURES_DIR.glob("*.diff")) if FEATURES_DIR.exists() else []
    if not feats:
        die(f"no features in {FEATURES_DIR}")
    base = base_dir()
    base.mkdir(parents=True, exist_ok=True)
    fails = 0
    for f in feats:
        lang, feature = split_feature(f.stem, langs)
        if lang is None:
            print(f"  [skip] {f.name}: unknown base lang")
            fails += 1
            continue
        dest = base / (fslug(lang) + "-_testall")
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(langs[lang], dest)
        status, reason, detail = "PASS", "", ""
        try:
            apply_diff(f.read_text(encoding="utf-8"), dest)
            cp = subprocess.run(["racket", "-e", '(require "top.scm") (run-all)'],
                                cwd=str(dest), capture_output=True, text=True)
            raw = cp.stdout + cp.stderr
            low = raw.lower()  # EOPL casing varies by Racket version
            if not (cp.returncode == 0 and "no bugs found" in low and "incorrect" not in low):
                status = "FAIL"
                # prefer the first incorrect/error line; else say why we judged a fail
                reason = next((ln.strip() for ln in raw.splitlines()
                               if "incorrect" in ln.lower() or "error" in ln.lower()), "")
                if not reason:
                    reason = (f"exit {cp.returncode}, "
                              f"{'no ' if 'no bugs found' not in low else ''}"
                              "'no bugs found' in output")
                detail = raw
        except Exception as e:                       # noqa: BLE001 - report any failure
            status, reason, detail = "ERROR", str(e), str(e)
        finally:
            shutil.rmtree(dest, ignore_errors=True)
        if status != "PASS":
            fails += 1
        print(f"  [{'ok' if status == 'PASS' else 'XX'}] {lang:16} {feature:12} {status}"
              + (f"  -- {reason[:100]}" if reason else ""))
        if status != "PASS" and detail:
            tail = [ln for ln in detail.splitlines() if ln.strip()][-20:]
            for ln in tail:
                print(f"          | {ln}")
    print(f"\n{len(feats) - fails}/{len(feats)} features passed")
    return 1 if fails else 0


PREVIEW_SUFFIX = "-put-in-preview"


def _read_sexp(text, i):
    """text[i] is '('. Return (group_text, index_after_close), string-aware."""
    depth, in_str, k = 0, False, i
    while k < len(text):
        c = text[k]
        if in_str:
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[i:k + 1], k + 1
        k += 1
    return text[i:], len(text)


def _parse_test_entry(grp):
    """'(name "prog" expected)' -> (name, prog, expected) or None."""
    inner = grp[1:].lstrip()
    name = ""
    for c in inner:
        if c.isspace() or c in '("':
            break
        name += c
    q = grp.find('"')
    if not name or q < 0:
        return None
    end = grp.find('"', q + 1)
    if end < 0:
        return None
    prog = grp[q + 1:end]
    rest = grp[end + 1:].rstrip()
    if rest.endswith(")"):
        rest = rest[:-1]
    return name, prog, rest.strip()


def _format_prog(prog):
    """Trim outer blank lines and dedent continuation lines for a clean preview."""
    parts = prog.split("\n")
    tail_indents = [len(p) - len(p.lstrip()) for p in parts[1:] if p.strip()]
    if tail_indents:
        cut = min(tail_indents)
        parts = [parts[0]] + [p[cut:] for p in parts[1:]]
    parts = [p.rstrip() for p in parts]
    while parts and not parts[0]:
        parts.pop(0)
    while parts and not parts[-1]:
        parts.pop()
    return "\n".join(parts)


def _added_text(diff_text, target="tests.scm", include_context=False):
    """Lines within the diff section for <target>, scoped to one file so
    paren/quote scanning isn't derailed by other files' hunks (e.g. interp.scm).
    With include_context=True, reconstructs the post-image (context + added
    lines) so a test body whose closing paren is a context line stays balanced;
    otherwise returns added ('+') lines only."""
    out, in_section = [], False
    for ln in diff_text.split("\n"):
        if ln.startswith("--- "):
            in_section = False
        elif ln.startswith("+++ "):
            path = ln[4:].strip()
            in_section = (path == target or path.endswith("/" + target))
        elif in_section:
            if ln.startswith("+"):
                out.append(ln[1:])
            elif include_context and (ln.startswith(" ") or ln == ""):
                out.append(ln[1:] if ln.startswith(" ") else ln)
    return "\n".join(out)


def extract_notes(diff_text):
    """Collect ';; note - <text>' comments added in the tests, as preview notes
    (one bullet per note). A note CONTINUES onto the next line when the current
    line ends with a backslash '\\' (the marker is stripped and the lines join
    into one bullet) -- use it to wrap a long sentence across several
    ';; note -' lines. A plain ';;' comment line right after a note also
    continues it; a blank or code line ends the note."""
    def clean(c):
        return c[:-1].rstrip() if c.endswith("\\") else c
    notes, cur = [], None
    for ln in _added_text(diff_text).split("\n"):
        s = ln.strip()
        m = re.match(r";+\s*note\s*-\s*(.*)$", s, re.IGNORECASE)
        if m:
            piece = m.group(1).strip()
            if cur is not None and cur.endswith("\\"):
                cur = (clean(cur) + " " + piece).strip()      # \-joined note line
            elif cur is not None:
                notes.append(clean(cur))
                cur = piece
            else:
                cur = piece
        elif cur is not None and re.match(r";+\s*\S", s):
            cur = (clean(cur) + " " + re.match(r";+\s*(.*)$", s).group(1).strip()).strip()
        elif cur is not None:
            notes.append(clean(cur))
            cur = None
    if cur is not None:
        notes.append(clean(cur))
    return notes


def extract_previews(diff_text):
    """Pull (label, program, expected) from added test entries whose name ends
    in -put-in-preview. These double as runnable tests and as feature previews."""
    added = _added_text(diff_text, include_context=True)
    previews, seen = [], set()
    # anchor on each marker, then read the test entry from the '(' before it —
    # robust against unbalanced parens in preceding note comments.
    for m in re.finditer(re.escape(PREVIEW_SUFFIX), added):
        op = added.rfind("(", 0, m.start())
        if op < 0 or op in seen:
            continue
        seen.add(op)
        grp, _ = _read_sexp(added, op)
        parsed = _parse_test_entry(grp)
        if parsed and parsed[0].endswith(PREVIEW_SUFFIX):
            name, prog, expected = parsed
            previews.append((name[:-len(PREVIEW_SUFFIX)], prog, expected))
    return previews


def cmd_export_all(args):
    """Concatenate every feature diff into one Markdown file, ordered by exam year."""
    langs = discover_langs()
    feats = all_features()
    if not feats:
        die(f"no features in {FEATURES_DIR}")
    out = SUMMARY_ROOT / "features.md"
    lines = ["# Feature catalogue", "",
             f"{len(feats)} features, ordered by exam year. All feature tests pass.",
             "",
             "> Note: these solutions are not necessarily the most efficient or clean — "
             "this is just how I implemented the features.",
             "", "## Index", ""]
    # sort by exam test-id (year first); features with no exam mapping go last.
    parsed = [(f, testid_of(f.stem), *split_feature(f.stem, langs)) for f in feats]
    parsed.sort(key=lambda t: (t[1] == "", t[1], t[2] or "", t[3]))
    headings = {}
    for f, testid, lang, feature in parsed:
        title = f"{lang or '?'} : {feature}"
        if testid:
            title = f"{testid} — {title}"
        headings[f] = title
        lines.append(f"- [{title}](#{gh_anchor(title)})")
    lines.append("")
    for f, testid, lang, feature in parsed:
        diff_text = f.read_text(encoding="utf-8")
        lines.append(f"## {headings[f]}")
        lines.append("")
        lines.append(f"`{f.name}`")
        lines.append("")
        previews = extract_previews(diff_text)
        notes = extract_notes(diff_text)
        if previews or notes:
            lines.append("**Preview** — what the feature must do "
                         "(from `*-put-in-preview` tests):")
            lines.append("")
            for label, prog, expected in previews:
                lines.append(f"_{label}_")
                lines.append("")
                lines.append("```")
                lines.append(_format_prog(prog))
                lines.append("```")
                lines.append(f"⇒ `{expected}`")
                lines.append("")
            if notes:
                lines.append("Notes:")
                lines.append("")
                for note in notes:
                    lines.append(f"- {note}")
                lines.append("")
        lines.append("```diff")
        lines.append(diff_text.rstrip("\n"))
        lines.append("```")
        lines.append("")
        lines.append(f"[↑ back to top](#{gh_anchor('Feature catalogue')})")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"export-all: {len(feats)} features -> {out.relative_to(SUMMARY_ROOT)}")
    return 0


def cmd_smoke(args):
    """Smoke test: run test-all, export-all, and infer on an example.
    Exits non-zero if any step fails (so it can gate CI)."""
    example = "let f = proc (x : ?) -(x,1) in (f 10)"
    rc = 0
    for name, fn in (("test-all", lambda: cmd_test_all(args)),
                     ("export-all", lambda: cmd_export_all(args)),
                     (f"infer {example!r}", lambda: cmd_infer([example]))):
        print(f"\n=== {name} ===")
        r = fn() or 0
        if r:
            rc = r
            print(f"  !! {name} failed (exit {r})")
    print(f"\nsmoke: {'OK' if rc == 0 else 'FAILED'}")
    return rc


def cmd_test(args):
    """Run one env's Racket test suite: racket -e '(require "top.scm") (run-all)'."""
    if not shutil.which("racket"):
        die("racket not found on PATH (needed to run tests)")
    env = base_dir() / args.env
    if not env.is_dir():
        die(f"no such env: {env}")
    cp = subprocess.run(["racket", "-e", '(require "top.scm") (run-all)'], cwd=str(env))
    return cp.returncode


# ============================================================================
# infer: Hindley-Milner type inference (fully inlined; no external module)
# ============================================================================

_INFER_DOC = r'''
infer.py -- Hindley-Milner type inference for the EOPL INFERRED language.

Mirrors chapter7/inferred (inferrer.scm + unifier.scm) and the method you use by
hand on the exam:

  1. assign a fresh type variable to every binding and every sub-expression
  2. generate ONE constraint set from the AST (the rules in the table below)
  3. solve the constraints by unification (substitution + occurs check)

...and it prints every step so you can copy the calculation onto paper.

Surface syntax (identical to inferred/lang.scm):

    n                          integer literal           (e.g. 42, -7)
    -(e1, e2)                  difference
    zero?(e)                   zero test
    if e1 then e2 else e3
    x                          variable
    let x = e in e
    proc (x : t) e             t is a type or ?   e.g.  proc (x : ?) -(x,1)
    (e1 e2)                    application
    letrec t p (x : t) = e in e
    types:  int | bool | (t -> t) | ?

Free variables x, v, i default to int (matching EOPL init-tenv).

Constraint rules (what each node emits; T_e = the node's type variable):

    n              T_e = int
    x              T_e = tenv(x)
    zero?(e1)      T_e1 = int ;  T_e = bool
    -(e1,e2)       T_e1 = int ; T_e2 = int ;  T_e = int
    if c t f       T_c = bool ; T_t = T_f ;   T_e = T_t
    let x=e1 in b  bind x:T_e1 ;              T_e = T_b
    proc(x:a) b    bind x:a ;                 T_e = (a -> T_b)        a fresh if ?
    (rator rand)   T_rator = (T_rand -> T_e)
    letrec r p(x:a)=pb in b
                   bind p:(a->r), x:a ; T_pb = r ;  T_e = T_b         a,r fresh if ?

Usage:
    python3 infer.py 'let f = proc (x : ?) -(x,1) in (f 10)'
    echo 'proc (x : ?) (x x)' | python3 infer.py
    python3 infer.py --brief '(proc (x : int) x  5)'
'''



# ============================================================================
# Types
# ============================================================================

class Type: pass

class TInt(Type):
    def ext(self): return "int"
    def __eq__(self, o): return isinstance(o, TInt)
    def __hash__(self): return 1

class TBool(Type):
    def ext(self): return "bool"
    def __eq__(self, o): return isinstance(o, TBool)
    def __hash__(self): return 2

class TArrow(Type):
    def __init__(self, a, b): self.a, self.b = a, b
    def ext(self): return "(%s -> %s)" % (self.a.ext(), self.b.ext())
    def __eq__(self, o): return isinstance(o, TArrow) and self.a == o.a and self.b == o.b
    def __hash__(self): return hash(("->", self.a, self.b))

class TVar(Type):
    def __init__(self, name): self.name = name
    def ext(self): return self.name
    def __eq__(self, o): return isinstance(o, TVar) and self.name == o.name
    def __hash__(self): return hash(("tvar", self.name))

_counter = [-1]                        # first fresh() is t0 -> the whole program's type
_used = {}                             # named-variable counters (for shadowing)

def reset_names():
    _counter[0] = -1
    _used.clear()

def fresh():
    _counter[0] += 1
    return TVar("t%d" % _counter[0])

def var_tvar(name):
    """A type variable NAMED after a program variable: w -> tw, x -> tx.
    A shadowing re-use of the same name gets a numeric suffix (tx, tx2, ...)."""
    base = "t" + name
    if base in _used:
        _used[base] += 1
        return TVar("%s%d" % (base, _used[base]))
    _used[base] = 1
    return TVar(base)

# ============================================================================
# AST  (each node gets `.tv`, its type variable, in the numbering pass)
# ============================================================================

class Node:
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)
        self.tv = None

def otype_str(o):
    return "?" if o is None else o.ext()

def unparse(n):
    k = n.kind
    if k == "const":  return str(n.val)
    if k == "var":    return n.name
    if k == "zero":   return "zero?(%s)" % unparse(n.e)
    if k == "diff":   return "-(%s, %s)" % (unparse(n.a), unparse(n.b))
    if k == "if":     return "if %s then %s else %s" % (unparse(n.c), unparse(n.t), unparse(n.f))
    if k == "let":    return "let %s = %s in %s" % (n.name, unparse(n.e1), unparse(n.body))
    if k == "proc":   return "proc (%s : %s) %s" % (n.name, otype_str(n.ann), unparse(n.body))
    if k == "call":   return "(%s %s)" % (unparse(n.rator), unparse(n.rand))
    if k == "letrec": return "letrec %s %s (%s : %s) = %s in %s" % (
        otype_str(n.rann), n.pname, n.bvar, otype_str(n.xann),
        unparse(n.pbody), unparse(n.lbody))
    return "?"

def children(n):
    k = n.kind
    if k in ("const", "var"):     return []
    if k == "zero":               return [n.e]
    if k == "diff":               return [n.a, n.b]
    if k == "if":                 return [n.c, n.t, n.f]
    if k == "let":                return [n.e1, n.body]
    if k == "proc":               return [n.body]
    if k == "call":               return [n.rator, n.rand]
    if k == "letrec":             return [n.pbody, n.lbody]
    return []

# ============================================================================
# Lexer
# ============================================================================

class Tok:
    def __init__(self, kind, val=None): self.kind, self.val = kind, val
    def __repr__(self): return self.kind if self.val is None else "%s(%r)" % (self.kind, self.val)

SINGLE = {"(": "LP", ")": "RP", ",": "COMMA", ":": "COLON", "?": "QMARK", "=": "EQ"}

def lex(s):
    toks, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace(): i += 1; continue
        if c == "%":
            while i < n and s[i] != "\n": i += 1
            continue
        if c in SINGLE:
            toks.append(Tok(SINGLE[c])); i += 1; continue
        if c == "-":
            if i + 1 < n and s[i+1] == ">":
                toks.append(Tok("ARROW")); i += 2; continue
            if i + 1 < n and s[i+1].isdigit():
                j = i + 1
                while j < n and s[j].isdigit(): j += 1
                toks.append(Tok("NUM", int(s[i:j]))); i = j; continue
            toks.append(Tok("MINUS")); i += 1; continue
        if c.isdigit():
            j = i
            while j < n and s[j].isdigit(): j += 1
            toks.append(Tok("NUM", int(s[i:j]))); i = j; continue
        if c.isalpha():
            j = i
            while j < n and (s[j].isalnum() or s[j] in "_?"): j += 1
            toks.append(Tok("ID", s[i:j])); i = j; continue
        raise SyntaxError("unexpected character %r at position %d" % (c, i))
    toks.append(Tok("EOF"))
    return toks

# ============================================================================
# Parser  (recursive descent)
# ============================================================================

class Parser:
    def __init__(self, toks): self.toks, self.p = toks, 0
    def peek(self): return self.toks[self.p]
    def next(self): t = self.toks[self.p]; self.p += 1; return t
    def eat(self, kind):
        t = self.next()
        if t.kind != kind: raise SyntaxError("expected %s, got %r" % (kind, t))
        return t
    def eat_id(self, word):
        t = self.next()
        if t.kind != "ID" or t.val != word:
            raise SyntaxError("expected %r, got %r" % (word, t))

    def parse(self):
        e = self.expr(); self.eat("EOF"); return e

    def expr(self):
        t = self.peek()
        if t.kind == "NUM":
            self.next(); return Node("const", val=t.val)
        if t.kind == "MINUS":
            self.next(); self.eat("LP")
            a = self.expr(); self.eat("COMMA"); b = self.expr(); self.eat("RP")
            return Node("diff", a=a, b=b)
        if t.kind == "LP":
            self.next()
            f = self.expr(); a = self.expr(); self.eat("RP")
            return Node("call", rator=f, rand=a)
        if t.kind == "ID":
            w = t.val
            if w == "zero?":
                self.next(); self.eat("LP"); e = self.expr(); self.eat("RP")
                return Node("zero", e=e)
            if w == "if":
                self.next()
                c = self.expr(); self.eat_id("then"); th = self.expr()
                self.eat_id("else"); el = self.expr()
                return Node("if", c=c, t=th, f=el)
            if w == "let":
                self.next()
                name = self.eat("ID").val; self.eat("EQ")
                e1 = self.expr(); self.eat_id("in"); body = self.expr()
                return Node("let", name=name, e1=e1, body=body)
            if w == "proc":
                self.next(); self.eat("LP")
                name = self.eat("ID").val; self.eat("COLON"); ann = self.otype(); self.eat("RP")
                body = self.expr()
                return Node("proc", name=name, ann=ann, body=body)
            if w == "letrec":
                self.next()
                rann = self.otype(); pname = self.eat("ID").val
                self.eat("LP"); bvar = self.eat("ID").val; self.eat("COLON")
                xann = self.otype(); self.eat("RP"); self.eat("EQ")
                pbody = self.expr(); self.eat_id("in"); lbody = self.expr()
                return Node("letrec", rann=rann, pname=pname, bvar=bvar,
                            xann=xann, pbody=pbody, lbody=lbody)
            self.next(); return Node("var", name=w)
        raise SyntaxError("unexpected token %r" % t)

    def otype(self):
        if self.peek().kind == "QMARK":
            self.next(); return None
        return self.type()

    def type(self):
        t = self.peek()
        if t.kind == "ID" and t.val == "int":  self.next(); return TInt()
        if t.kind == "ID" and t.val == "bool": self.next(); return TBool()
        if t.kind == "LP":
            self.next(); a = self.type(); self.eat("ARROW"); b = self.type(); self.eat("RP")
            return TArrow(a, b)
        raise SyntaxError("expected a type, got %r" % t)

# ============================================================================
# Phase A -- number every sub-expression with a fresh type variable (pre-order)
# ============================================================================

def number(node, table):
    # consts have no type variable (a literal is `int`); vars use their NAMED
    # type variable (tw, tx, ...), assigned where they are bound. Only compound
    # sub-expressions get a numbered tvar, root first -> t0.
    if node.kind in ("const", "var"):
        return
    node.tv = fresh()
    table.append(node)                 # records (node.tv, source) in reading order
    for ch in children(node):
        number(ch, table)

# ============================================================================
# Phase B -- generate the constraint set
# ============================================================================

class Constraint:
    def __init__(self, lhs, rhs, reason, src):
        self.lhs, self.rhs, self.reason, self.src = lhs, rhs, reason, src

def emit(cs, lhs, rhs, reason, src):
    # skip trivially-true equations between identical concrete types (e.g. int = int
    # from a constant operand) -- nothing to solve, just noise.
    if not has_tvar(lhs) and not has_tvar(rhs) and lhs == rhs:
        return
    cs.append(Constraint(lhs, rhs, reason, src))

def gen(node, tenv, cs, binds):
    """Generate constraints for `node` (and its children) into `cs`, and RETURN
    the node's type: int for a const, the NAMED tvar for a var, the numbered tvar
    for a compound. tenv: name -> Type. binds: list of (name, Type) for display."""
    k, src = node.kind, unparse(node)

    if k == "const":
        return TInt()                                   # a literal IS int -- no tvar

    if k == "var":
        if node.name not in tenv:
            raise NameError("unbound variable: %s" % node.name)
        return tenv[node.name]                          # the var's named tvar (or annotation)

    if k == "zero":
        te = gen(node.e, tenv, cs, binds)
        emit(cs, te, TInt(), "zero? tests an int", src)
        emit(cs, node.tv, TBool(), "zero? yields a bool", src)
        return node.tv

    if k == "diff":
        ta = gen(node.a, tenv, cs, binds)
        tb = gen(node.b, tenv, cs, binds)
        emit(cs, ta, TInt(), "- needs int operands", src)
        emit(cs, tb, TInt(), "- needs int operands", src)
        emit(cs, node.tv, TInt(), "- yields an int", src)
        return node.tv

    if k == "if":
        tc = gen(node.c, tenv, cs, binds)
        tt = gen(node.t, tenv, cs, binds)
        tf = gen(node.f, tenv, cs, binds)
        emit(cs, tc, TBool(), "if condition is bool", src)
        emit(cs, tt, tf, "both branches agree", src)
        emit(cs, node.tv, tt, "if yields the branch type", src)
        return node.tv

    if k == "let":
        t1 = gen(node.e1, tenv, cs, binds)
        xt = var_tvar(node.name); binds.append((node.name, xt))
        emit(cs, xt, t1, "let binds %s to its rhs" % node.name, src)
        body_env = dict(tenv); body_env[node.name] = xt
        tb = gen(node.body, body_env, cs, binds)
        emit(cs, node.tv, tb, "let yields the body type", src)
        return node.tv

    if k == "proc":
        xt = var_tvar(node.name); binds.append((node.name, xt))
        if node.ann is not None:
            emit(cs, xt, node.ann, "annotation on %s" % node.name, src)
        body_env = dict(tenv); body_env[node.name] = xt
        tb = gen(node.body, body_env, cs, binds)
        emit(cs, node.tv, TArrow(xt, tb), "proc builds arg -> result", src)
        return node.tv

    if k == "call":
        tr = gen(node.rator, tenv, cs, binds)
        ta = gen(node.rand, tenv, cs, binds)
        emit(cs, tr, TArrow(ta, node.tv), "operator type = arg -> result", src)
        return node.tv

    if k == "letrec":
        arg_t = var_tvar(node.bvar)
        res_t = node.rann if node.rann is not None else fresh()
        ptv = var_tvar(node.pname)
        binds.append((node.pname, ptv)); binds.append((node.bvar, arg_t))
        emit(cs, ptv, TArrow(arg_t, res_t), "%s : arg -> result" % node.pname, src)
        if node.xann is not None:
            emit(cs, arg_t, node.xann, "annotation on %s" % node.bvar, src)
        rec_env = dict(tenv); rec_env[node.pname] = ptv
        body_env = dict(rec_env); body_env[node.bvar] = arg_t
        tpb = gen(node.pbody, body_env, cs, binds)
        emit(cs, tpb, res_t, "proc body matches declared result", src)
        tlb = gen(node.lbody, rec_env, cs, binds)
        emit(cs, node.tv, tlb, "letrec yields the in-body type", src)
        return node.tv

    raise RuntimeError("no rule for %s" % k)

# ============================================================================
# Unification
# ============================================================================

def occurs(vid, ty):
    if isinstance(ty, TVar):   return ty.name == vid
    if isinstance(ty, TArrow): return occurs(vid, ty.a) or occurs(vid, ty.b)
    return False

def subst_one(ty, vid, repl):
    """Replace TVar(vid) with repl inside ty."""
    if isinstance(ty, TVar):   return repl if ty.name == vid else ty
    if isinstance(ty, TArrow): return TArrow(subst_one(ty.a, vid, repl), subst_one(ty.b, vid, repl))
    return ty

def apply_subst(ty, sigma):
    if isinstance(ty, TVar):
        return apply_subst(sigma[ty.name], sigma) if ty.name in sigma else ty
    if isinstance(ty, TArrow):
        return TArrow(apply_subst(ty.a, sigma), apply_subst(ty.b, sigma))
    return ty

def extend(sigma, vid, ty):
    """Bind tvar vid -> ty, keeping sigma idempotent (substitute into old entries)."""
    new = {k: subst_one(v, vid, ty) for k, v in sigma.items()}
    new[vid] = ty
    return new

def has_tvar(ty):
    if isinstance(ty, TVar):   return True
    if isinstance(ty, TArrow): return has_tvar(ty.a) or has_tvar(ty.b)
    return False

def sigma_str(sigma):
    if not sigma: return "{}"
    items = sorted(sigma.items())
    return "{ " + ",  ".join("%s -> %s" % (k, v.ext()) for k, v in items) + " }"

def unify(constraints, verbose):
    sigma = {}
    work = [(c.lhs, c.rhs, c.reason) for c in constraints]
    step = 0
    while work:
        lhs, rhs, reason = work.pop(0)
        L, R = apply_subst(lhs, sigma), apply_subst(rhs, sigma)
        step += 1
        if verbose:
            print("  %d) choose equation:   %s = %s   [%s]"
                  % (step, lhs.ext(), rhs.ext(), reason))
            # bracket the substitution stage when applying subs leaves the equation the same
            if L == lhs and R == rhs:
                print("     [sub in equation:   %s = %s]" % (L.ext(), R.ext()))
            else:
                print("     sub in equation:   %s = %s" % (L.ext(), R.ext()))
        if L == R:
            if verbose: print("     identity -> discard")
            continue
        if isinstance(L, TVar):
            if occurs(L.name, R):
                raise TypeError("occurs check failed: %s occurs in %s (infinite type)"
                                % (L.ext(), R.ext()))
            sigma = extend(sigma, L.name, R)
            if verbose: print("     new/changed subs:  %s" % sigma_str(sigma))
        elif isinstance(R, TVar):
            if occurs(R.name, L):
                raise TypeError("occurs check failed: %s occurs in %s (infinite type)"
                                % (R.ext(), L.ext()))
            sigma = extend(sigma, R.name, L)
            if verbose: print("     new/changed subs:  %s   (sides switched: bind %s)"
                              % (sigma_str(sigma), R.ext()))
        elif isinstance(L, TArrow) and isinstance(R, TArrow):
            work.insert(0, (L.b, R.b, reason + " (result)"))
            work.insert(0, (L.a, R.a, reason + " (arg)"))
            if verbose: print("     compare equations: %s = %s ;  %s = %s"
                              % (L.a.ext(), R.a.ext(), L.b.ext(), R.b.ext()))
        else:
            raise TypeError("type clash: cannot unify %s with %s" % (L.ext(), R.ext()))
    return sigma

# ============================================================================
# Driver
# ============================================================================

def infer(source, verbose=True):
    reset_names()
    ast = Parser(lex(source)).parse()

    table = []
    number(ast, table)

    tenv = {"x": TInt(), "v": TInt(), "i": TInt()}     # EOPL init-tenv
    cs, binds = [], []
    root_type = gen(ast, tenv, cs, binds)              # the program's type variable (t0)

    if verbose:
        print("=" * 72)
        print("PROGRAM:  " + unparse(ast))
        print("=" * 72)

        print("\nInitial type environment (free vars):  x:int  v:int  i:int")
        print("Constants have no type variable (a literal is `int`).")

        print("\n--- Step 0: a type variable for every variable and compound sub-expression ---")
        for name, ty in binds:
            print("  %-4s = type of   %s   (variable)" % (ty.ext(), name))
        for nd in table:
            print("  %-4s = type of   %s" % (nd.tv.ext(), unparse(nd)))

        print("\n--- Step 1: constraints generated from the AST ---")
        for idx, c in enumerate(cs, 1):
            print("  C%-2d  %-22s  [%s]" % (idx, "%s = %s" % (c.lhs.ext(), c.rhs.ext()), c.reason))

        print("\n--- Step 2: unification (apply subs, then solve each equation) ---")

    sigma = unify(cs, verbose)
    result = apply_subst(root_type, sigma)

    if verbose:
        print("\n--- Final subs ---")
        print("  " + sigma_str(sigma))
        print("\n" + "=" * 72)
        print("TYPE OF PROGRAM:  %s   (= %s)" % (root_type.ext(), result.ext()))
        print("=" * 72)
    return result

def infer_main(argv):
    args = list(argv)
    brief = False
    if args and args[0] in ("--brief", "-b"):
        brief = True; args = args[1:]
    source = " ".join(args) if args else sys.stdin.read()
    source = source.strip()
    if not source:
        print(_INFER_DOC); return 0
    try:
        result = infer(source, verbose=not brief)
        if brief:
            print(result.ext())
    except (SyntaxError, NameError, TypeError) as e:
        print("TYPE ERROR: %s" % e)
        return 1

    return 0

# -------------------------------------------------------------------- main

def main(argv):
    # `infer` is a pure passthrough: grab everything after it untouched so
    # flags like --brief and the quoted expression are not parsed by argparse.
    if "infer" in argv:
        idx = argv.index("infer")
        return cmd_infer(argv[idx + 1:])

    fmt = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(
        prog="main.py", description=__doc__, formatter_class=fmt,
        epilog=textwrap.dedent("""\
            concepts
              lang      a canonical interpreter under chapter*/ (a dir with lang.scm + top.scm).
                        Referred to by name or any unambiguous suffix:  let, proc-ds, ds-rep, inferred
              env       a throwaway working copy under the base dir (default: envs/), named
                        <lang>-<env>, that you hand-edit to build up a feature
              feature   an env's edits captured as a portable unified diff in
                        features/<lang>-<feature>.diff, replayable onto any fresh env of that lang

            typical workflow
              python3 main.py init proc-ds tuples      # envs/proc-ds-tuples <- pristine proc-ds
              # ...hand-edit envs/proc-ds-tuples/{lang,interp,data-structures,tests}.scm...
              python3 main.py test proc-ds-tuples      # run that env's Racket test suite
              python3 main.py diff proc-ds-tuples      # eyeball the change so far
              python3 main.py export proc-ds-tuples tuples   # freeze -> features/proc-ds-tuples.diff

            replay a saved feature onto a clean env
              python3 main.py init proc-ds try && python3 main.py import tuples proc-ds-try

            check everything still works / regenerate the catalogue
              python3 main.py test-all                 # needs `racket` on PATH
              python3 main.py export-all               # rewrites features.md (repo root)
              python3 main.py smoke                    # all of the above + an infer example

            type-inference helper (independent of the env machinery)
              python3 main.py infer 'let f = proc (x : ?) -(x,1) in (f 10)'
              python3 main.py infer --brief '(proc (x : int) x  5)'
              echo 'proc (x : ?) (x x)' | python3 main.py infer

            note: `infer` swallows everything after it verbatim, so --brief and the quoted
            program reach the inferrer untouched. Working envs always live under envs/.
        """))
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    s = sub.add_parser(
        "init", formatter_class=fmt,
        help="copy a pristine lang into a new working env",
        description="Copy chapter*/<lang> into <base>/<lang>-<env>, a fresh working copy you "
                    "then hand-edit. Refuses to clobber an existing env unless --force.")
    s.add_argument("lang", help="source language: name or unambiguous suffix (e.g. let, proc-ds, ds-rep)")
    s.add_argument("env", help="short env tag; the folder becomes <lang>-<env> (e.g. 'tuples')")
    s.add_argument("--force", action="store_true", help="overwrite the env if it already exists")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser(
        "import", formatter_class=fmt,
        help="apply a saved feature diff onto an existing env",
        description="Apply features/<lang>-<feature>.diff onto an existing env (the env's base "
                    "lang is inferred from its folder name). Aborts without writing if the diff "
                    "does not apply cleanly.")
    s.add_argument("feature", help="feature name, e.g. 'tuples' (matches features/<lang>-tuples.diff)")
    s.add_argument("env", help="target env folder under the base dir, e.g. proc-ds-try")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser(
        "export", formatter_class=fmt,
        help="capture an env's edits back into a matching feature diff",
        description="Diff an env against its pristine source lang and overwrite the matching "
                    "feature file. <feature> is a substring matched against that lang's feature "
                    "files (by exam test-id or feature word); a unique hit is overwritten, "
                    "otherwise the candidate file names are listed.")
    s.add_argument("env", help="env folder whose edits to capture, e.g. proc-ds-tuples")
    s.add_argument("feature", help="substring identifying the target feature file, e.g. 'tuples' or '2021b57'")
    s.add_argument("--no-verify", action="store_true",
                   help="skip the test gate and export even if the env's tests fail")
    s.add_argument("--new", action="store_true",
                   help="create a NEW feature file features/<lang>-<feature>.diff "
                        "(feature is taken literally, not as a substring) instead of "
                        "overwriting an existing one")
    s.set_defaults(fn=cmd_export)

    s = sub.add_parser(
        "diff", formatter_class=fmt,
        help="print an env's current diff to stdout (no file written)",
        description="Like export, but stream the env-vs-pristine unified diff to stdout instead "
                    "of saving it. Handy for reviewing work in progress.")
    s.add_argument("env", help="env folder to diff against its pristine source lang")
    s.set_defaults(fn=cmd_diff)

    s = sub.add_parser(
        "test-all", formatter_class=fmt,
        help="apply every feature to a fresh env, run its tests, clean up",
        description="For each features/*.diff: init a fresh env of its base lang, apply the diff, "
                    "run `racket top.scm`'s (run-all), then delete the env. Reports PASS/FAIL per "
                    "feature and exits non-zero on any failure. Requires `racket` on PATH.")
    s.set_defaults(fn=cmd_test_all)

    s = sub.add_parser(
        "export-all", formatter_class=fmt,
        help="regenerate features.md (repo root) from all feature diffs",
        description="Concatenate every features/*.diff into a single annotated Markdown catalogue "
                    "at features.md (repo root), with an index grouped by lang : feature.")
    s.set_defaults(fn=cmd_export_all)

    s = sub.add_parser(
        "test", formatter_class=fmt,
        help="run one env's Racket test suite",
        description="Run an env's test suite by invoking "
                    "`racket -e '(require \"top.scm\") (run-all)'` inside the env directory, "
                    "streaming Racket's output. Exits with Racket's return code.")
    s.add_argument("env", help="env folder under envs/ to test, e.g. proc-ds-tuples")
    s.set_defaults(fn=cmd_test)

    s = sub.add_parser(
        "smoke", formatter_class=fmt,
        help="smoke test: run test-all, export-all, and infer on an example",
        description="Quick end-to-end smoke test of the harness: runs test-all, then export-all, "
                    "then infer on a sample program. Just exercises the three paths and prints "
                    "their output — it does not check the results.")
    s.set_defaults(fn=cmd_smoke)

    s = sub.add_parser(
        "infer", formatter_class=fmt,
        help="Hindley-Milner type inference for the INFERRED language",
        description="Type-infer an INFERRED-language program, printing the full constraint set "
                    "and step-by-step unification (the by-hand exam method). Everything after "
                    "'infer' is passed through verbatim; reads stdin if no program is given. "
                    "Use --brief to print just the final type. Run `python3 main.py infer` "
                    "with no program to print the surface-syntax reference.")
    s.set_defaults(fn=lambda a: cmd_infer([]))

    s = sub.add_parser(
        "list", formatter_class=fmt,
        help="list known langs / envs / features",
        description="Show what's available. With no flag, lists all three sections; pass one or "
                    "more flags to restrict the output.")
    s.add_argument("--langs", action="store_true", help="only list canonical languages")
    s.add_argument("--envs", action="store_true", help="only list working envs under the base dir")
    s.add_argument("--features", action="store_true", help="only list saved feature diffs")
    s.set_defaults(fn=cmd_list)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
