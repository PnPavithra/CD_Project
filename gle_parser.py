# gle_parser.py
import re
import json
from lexer import lex
from exceptions import ParseError
from phase1 import Phase1Parser
from phase2 import Phase2Parser
from phase3 import Phase3Parser



def extract_function_blocks(code):
    """
    Extract functions reliably, even with indentation, comments, or line breaks.
    Returns: list of {name, params_text, body_text, start_line, end_line}
    """

    # More tolerant function header pattern
    header_re = re.compile(
        r'\b([A-Za-z_][\w\s\*\&<>:]*)\s+'     # return type
        r'([A-Za-z_]\w*)\s*'                  # function name
        r'\((.*?)\)\s*'                        # parameters
        r'\{',                                 # opening brace
        re.DOTALL
    )

    funcs = []

    for m in header_re.finditer(code):
        name = m.group(2)
        params_txt = m.group(3).strip()

        # Find matching closing brace
        brace_start = m.end() - 1
        depth = 1
        pos = brace_start + 1

        while pos < len(code) and depth > 0:
            if code[pos] == "{":
                depth += 1
            elif code[pos] == "}":
                depth -= 1
            pos += 1

        body = code[brace_start + 1 : pos - 1]

        start_line = code[:m.start()].count("\n") + 1
        end_line = code[:pos].count("\n") + 1

        funcs.append({
            "name": name,
            "params_text": params_txt,
            "body_text": body,
            "start_line": start_line,
            "end_line": end_line
        })

    return funcs


def parse_parameters(params_text):
    if not params_text:
        return []
    parts = [p.strip() for p in params_text.split(',') if p.strip()]
    params = []
    for p in parts:
        # naive: last token is param name
        tokens = p.split()
        pname = tokens[-1]
        ptype = " ".join(tokens[:-1]) if len(tokens) > 1 else ""
        params.append({"type": ptype, "name": pname})
    return params

def extract_local_declarations(body_text):
    """
    Extract simple local declarations inside a function.
    """
    decls = []
    decl_re = re.compile(r'\b([A-Za-z_][\w<>]*)\s+([A-Za-z_]\w*)\s*(=.*)?;')

    for line in body_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        m = decl_re.match(stripped)
        if m:
            decls.append({
                "type": m.group(1),
                "name": m.group(2),
                "line": stripped
            })

    return decls


def extract_expressions(body_text):
    """
    Extract expressions such as assignments, function calls, returns.
    """
    exprs = []

    for i, line in enumerate(body_text.split("\n"), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # Skip declarations
        if re.match(r'\b[A-Za-z_][\w<>]*\s+[A-Za-z_]\w*\s*(=.*)?;', stripped):
            continue

        # Anything else ending with ; is an expression
        if stripped.endswith(";"):
            exprs.append({
                "text": stripped.rstrip(";"),
                "lineno": i
            })

    return exprs


def find_global_declarations(code, function_blocks):
    """
    Identify global declarations only outside function ranges.
    """
    globals_list = []
    lines = code.split("\n")

    # Mark lines that are inside functions so we can skip them
    inside_func = [False] * len(lines)

    for f in function_blocks:
        start = f["start_line"] - 1
        end = f["end_line"] - 1
        for i in range(start, end + 1):
            inside_func[i] = True

    decl_re = re.compile(r'\b([A-Za-z_][\w<>]*)\s+([A-Za-z_]\w*)\s*(=.*)?;')

    for i, line in enumerate(lines):
        if inside_func[i]:
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m = decl_re.match(stripped)
        if m:
            globals_list.append({
                "type": m.group(1),
                "name": m.group(2),
                "line": stripped
            })

    return globals_list


def run_gle(code: str):
    """
    Runs the 3-phase parser for real error detection
    AND preserves your original AST extraction.
    """
    # Normalize newlines
    code = code.replace("\r\n", "\n").replace("\r", "\n")

    # ============================================================
    # 🌟 1) REAL ERROR DETECTION USING YOUR THREE-PHASE PARSER
    # ============================================================
    try:
        tokens = lex(code)                     # LEXICAL ANALYSIS
        Phase1Parser(tokens).parse()           # GLOBAL + BLOCK STRUCTURE
        Phase2Parser(tokens).parse()           # STATEMENTS + SEMICOLONS
        Phase3Parser(tokens).parse()           # EXPRESSIONS
        parser_error = None                    # No error found

    except ParseError as e:
        # Format real compiler-style error message
        parser_error = (
            f"❌ ERROR in {e.phase} PHASE:\n"
            f"Message: {e.message}\n"
            f"Line: {e.line}\n"
            f"Column: {e.column}"
        )

    except Exception as e:
        parser_error = f"❌ INTERNAL ERROR: {str(e)}"

    # ============================================================
    # 🌟 2) YOUR ORIGINAL AST GENERATION (UNCHANGED)
    # ============================================================
    try:
        functions = extract_function_blocks(code)
        globals_found = find_global_declarations(code, functions)

        ast = {"type": "Program", "globals": [], "functions": []}

        for g in globals_found:
            ast["globals"].append(g)

        for f in functions:
            params = parse_parameters(f["params_text"])
            locals_ = extract_local_declarations(f["body_text"])
            expressions = extract_expressions(f["body_text"])

            ast["functions"].append({
                "type": "Function",
                "name": f["name"],
                "params": params,
                "locals": locals_,
                "expressions": expressions,
                "start_line": f["start_line"],
                "end_line": f["end_line"]
            })

    except Exception as e:
        # AST error → return empty AST but keep parser error
        return (
            parser_error or f"❌ AST ERROR: {str(e)}",
            {"type": "Program", "globals": [], "functions": []}
        )

    # ============================================================
    # 🌟 3) RETURN PHASE PARSER ERRORS OR SUCCESS MESSAGE
    # ============================================================
    if parser_error:
        return parser_error, ast      # Return real parsing error + AST

    return (
        f"Parsed: {len(ast['globals'])} global(s), {len(ast['functions'])} function(s).",
        ast
    )