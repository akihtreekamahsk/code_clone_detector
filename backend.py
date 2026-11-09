import ast
import difflib
import re

class NormalizeIdentifiers(ast.NodeTransformer):
    """Normalize variable/function/class/argument names for structural comparison."""
    def __init__(self):
        self.names = {}
        self.counter = 0

    def normalized(self, name):
        if name not in self.names:
            self.counter += 1
            self.names[name] = f"id_{self.counter}"
        return self.names[name]

    def visit_Name(self, node):
        node.id = self.normalized(node.id)
        return self.generic_visit(node)

    def visit_arg(self, node):
        node.arg = self.normalized(node.arg)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        node.name = self.normalized(node.name)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        node.name = self.normalized(node.name)
        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        node.name = self.normalized(node.name)
        return self.generic_visit(node)

def preprocess_code(code):
    lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(re.sub(r"\s+", " ", stripped))
    return "\n".join(lines)

def text_similarity(code1, code2):
    a, b = preprocess_code(code1), preprocess_code(code2)
    if not a and not b:
        return 100.0
    return round(difflib.SequenceMatcher(None, a, b).ratio() * 100, 2)

def ast_signature(code):
    tree = ast.parse(code)
    tree = NormalizeIdentifiers().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.dump(tree, include_attributes=False)

def ast_similarity(code1, code2):
    try:
        sig1, sig2 = ast_signature(code1), ast_signature(code2)
        score = difflib.SequenceMatcher(None, sig1, sig2).ratio() * 100
        return round(score, 2), None
    except SyntaxError as exc:
        return None, f"AST parsing failed: {exc.msg} (line {exc.lineno})"

def compare_lines(code1, code2):
    lines1, lines2 = code1.splitlines(), code2.splitlines()
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    counts = {"unchanged": 0, "added": 0, "removed": 0, "changed": 0}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            counts["unchanged"] += i2 - i1
        elif tag == "insert":
            counts["added"] += j2 - j1
        elif tag == "delete":
            counts["removed"] += i2 - i1
        elif tag == "replace":
            counts["changed"] += max(i2 - i1, j2 - j1)
    return counts

def make_diff(code1, code2):
    return "\n".join(difflib.unified_diff(
        code1.splitlines(), code2.splitlines(),
        fromfile="File 1", tofile="File 2", lineterm=""
    ))

def calculate_similarity(code1, code2):
    ast_score, ast_error = ast_similarity(code1, code2)
    text_score = text_similarity(code1, code2)
    line_counts = compare_lines(code1, code2)
    # Prefer AST when both files parse; otherwise fall back to text similarity.
    overall = ast_score if ast_score is not None else text_score
    if overall >= 80:
        label = "High similarity"
        explanation = "The files have a high level of structural/text similarity."
    elif overall >= 50:
        label = "Moderate similarity"
        explanation = "The files share some structure or text, but also contain differences."
    else:
        label = "Low similarity"
        explanation = "The files appear substantially different."
    return {
        "similarity_score": round(overall, 2),
        "ast_similarity": ast_score,
        "text_similarity": text_score,
        "classification": label,
        "explanation": explanation,
        "ast_error": ast_error,
        "line_counts": line_counts,
        "diff": make_diff(code1, code2),
    }