import re
from typing import List

BUILTIN_SHADOW = [
    "list", "dict", "str", "int", "float", "tuple", "set", "type",
    "len", "map", "filter", "print", "input", "range", "sum", "max",
    "min", "open", "file",
]

LOOP_RE = re.compile(r"^\s*(for\b|while\b)")


def _is_recursive(code: str) -> bool:
    matches = list(re.finditer(r"def\s+(\w+)\s*\(", code))
    for i, m in enumerate(matches):
        name = m.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
        body = code[m.end():end]
        if re.search(r"\b" + re.escape(name) + r"\s*\(", body):
            return True
    return False


def _loop_depth(code: str) -> int:
    active: List[int] = []
    max_depth = 0
    for raw in code.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        while active and indent <= active[-1]:
            active.pop()
        if LOOP_RE.match(raw):
            active.append(indent)
            max_depth = max(max_depth, len(active))
    return max_depth


def estimate_complexity(code: str) -> dict:
    depth = _loop_depth(code)
    uses_sort = bool(re.search(r"\b(sorted)\s*\(", code) or ".sort()" in code)
    recursive = _is_recursive(code)

    if recursive:
        time = "O(2^n) / O(n^depth) — recursive. Usually exponential unless memoized."
        space = "O(n) — recursion depth on the call stack."
    elif depth >= 2:
        time = f"O(n^{depth}) — nested loops (depth {depth})."
        space = "O(1) — constant auxiliary space beyond the input."
    elif uses_sort:
        time = "O(n log n) — sorting dominates the runtime."
        space = "O(n) — in-place sort keeps this low; sorted() copies the list."
    elif depth == 1:
        time = "O(n) — single pass over the input."
        space = "O(1) — constant auxiliary space."
    else:
        time = "O(1) — no loops detected, constant-time operations."
        space = "O(1) — constant auxiliary space."

    return {
        "time_complexity": time,
        "space_complexity": space,
        "explanation": (
            f"Detected {depth} level(s) of loop nesting, "
            f"{'recursion' if recursive else 'no recursion'}, "
            f"{'sorting' if uses_sort else 'no built-in sorting'}."
        ),
    }


def rate_code(code: str) -> dict:
    lines = code.splitlines()
    non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    n = len(non_empty)

    readability = 10.0
    performance = 10.0
    security = 10.0
    notes: List[str] = []

    if not code.strip():
        return {
            "overall": 0,
            "readability": 0,
            "performance": 0,
            "security": 0,
            "breakdown": "Empty code — nothing to rate.",
        }

    # --- Readability ---
    if n > 200:
        readability -= 2
        notes.append("Very long file — consider splitting into functions/modules.")
    long_lines = sum(1 for l in lines if len(l) > 100)
    if long_lines:
        readability -= min(2, long_lines * 0.5)
        notes.append(f"{long_lines} line(s) exceed 100 chars.")
    if not re.search(r'"""|\'\'\'', code) and n > 30:
        readability -= 1
        notes.append("No docstrings — document key functions and modules.")
    if len(re.findall(r"\b[a-z]\b", code)) > 12 and not any(
        kw in code for kw in ("for ", "while ", "in ")
    ):
        readability -= 1
        notes.append("Too many single-letter variable names.")

    # --- Performance ---
    depth = _loop_depth(code)
    if depth >= 2:
        performance -= 2 * (depth - 1)
        notes.append(f"Nested loops (depth {depth}) suggest O(n^{depth}). One pass or a hash map might do?")
    if _is_recursive(code):
        performance -= 2
        notes.append("Recursion without memoization can blow up to exponential — cache or iterate.")
    if re.search(r"for\s+\w+\s+in\b", code) and re.search(r"\b(if|while)\s+[\w\[\]\.\s]+?\s+(not\s+)?in\b", code):
        performance -= 1
        notes.append("`x in list` inside a loop is O(n) per check — use a set for O(1).")
        if depth >= 1:
            performance -= 1
            notes.append("Membership scan inside nested loops pushes the effective cost to O(n^(k+1)).")

    # --- Security ---
    if re.search(r"\b(eval|exec)\s*\(", code):
        security -= 4
        notes.append("eval/exec run arbitrary code — remove or strictly sanitize.")
    if re.search(r"subprocess", code) and re.search(r"shell\s*=\s*True", code):
        security -= 3
        notes.append("subprocess(shell=True) is injection-prone — pass argument lists instead.")
    if re.search(r"SELECT.*\{|INSERT INTO.*\{", code, re.IGNORECASE):
        security -= 3
        notes.append("String-built SQL — use parameterized queries.")
    if re.search(
        r"(api[_-]?key|password|secret)\s*=\s*[\"'][^\"']+[\"']", code, re.IGNORECASE
    ):
        security -= 2
        notes.append("Hardcoded secrets — move them to environment variables.")
    if re.search(r"\bopen\s*\(", code) and not re.search(r"with\s+open\s*\(", code):
        security -= 1
        notes.append("open() without a context manager can leak file handles.")

    readability = max(0, min(10, round(readability)))
    performance = max(0, min(10, round(performance)))
    security = max(0, min(10, round(security)))
    overall = round((readability + performance + security) / 3)

    return {
        "overall": overall,
        "readability": readability,
        "performance": performance,
        "security": security,
        "breakdown": " | ".join(notes) if notes else "Looks clean overall. Ask the tutor for detailed guidance.",
    }


def find_bugs(code: str) -> dict:
    findings: List[dict] = []
    lines = code.splitlines()

    def add(severity: str, line_no: int, message: str, hint: str) -> None:
        findings.append(
            {"severity": severity, "line": line_no, "message": message, "hint": hint}
        )

    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped:
            continue

        if re.search(r"if\s+\w+\s*=\s*[^=]", stripped):
            add("error", i, "Assignment `=` used inside an if condition instead of comparison `==`.", "Use `==` to compare values.")
        if re.match(r"^\s*except\s*:", raw):
            add("warning", i, "Bare `except:` catches everything, including KeyboardInterrupt/SystemExit.", "Catch specific exceptions, e.g. `except ValueError:`.")
        if re.search(r"\b(is|is not)\s+[\"']", stripped):
            add("warning", i, "`is` tests identity, not equality — string literals from different sources won't match.", "Use `==` for string comparison.")
        if re.search(r"\b(eval|exec)\s*\(", stripped):
            add("critical", i, "`eval`/`exec` execute arbitrary code — a serious security risk.", "Avoid them or strictly validate input.")
        m = re.search(r"def\s+(\w+)\s*\(([^)]*)\)", stripped)
        if m and re.search(r"\[\s*\]|\{\s*\}", m.group(2)):
            add("warning", i, "Mutable default argument is shared across all calls.", "Use `None` and build the object inside the function.")

    for i, raw in enumerate(lines, 1):
        m = re.match(r"^\s*(\w+)\s*=", raw)
        if m and m.group(1) in BUILTIN_SHADOW:
            add("warning", i, f"Assigning to the built-in name `{m.group(1)}` shadows the builtin.", f"Rename it (e.g. `{m.group(1)}_`).")
            break

    loop_depth = _loop_depth(code)

    if loop_depth >= 1 and re.search(r"\b(if|while)\s+[\w\[\]\.\s]+?\s+(not\s+)?in\s+\w+", code):
        add(
            "warning",
            0,
            f"List-membership check (`x in list`) inside a loop is O(n) each time — with {loop_depth} loop(s) this multiplies the cost.",
            "Convert the list to a set for O(1) membership.",
        )

    double_index = {}
    for m in re.finditer(r"(\w+)\[(\w+)\]\[(\w+)\]", code):
        var, first, _ = m.group(1), m.group(2), m.group(3)
        double_index.setdefault(var, set()).add(first)
    for var, firsts in double_index.items():
        if len(firsts) > 1:
            add(
                "warning",
                0,
                f"`{var}` is indexed by different row variables ({', '.join(sorted(firsts))}) — rows of unequal length will raise IndexError.",
                "Normalize row lengths or guard with `if j < len(row):` before indexing.",
            )

    return {"bugs": findings}
