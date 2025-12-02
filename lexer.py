# lexer.py

import re
from dataclasses import dataclass

@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

KEYWORDS = {"int", "if", "else", "while", "return"}

TOKEN_SPEC = [
    ("NUMBER",   r'\d+'),
    ("ID",       r'[A-Za-z_]\w*'),
    ("STRING",   r'"[^"\n]*"'),
    ("OP",       r'==|!=|<=|>=|\+|-|\*|/|<|>|='),
    ("LPAREN",   r'\('),
    ("RPAREN",   r'\)'),
    ("LBRACE",   r'\{'),
    ("RBRACE",   r'\}'),
    ("SEMICOL",  r';'),
    ("COMMA",    r','),
    ("NEWLINE",  r'\n'),
    ("SKIP",     r'[ \t\r]+'),
    ("MISMATCH", r'.'),
]

master_pat = re.compile("|".join(
    f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC
))

def lex(code: str):
    tokens = []
    line = 1
    line_start = 0

    for mo in master_pat.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        col = mo.start() - line_start + 1

        if kind == "NEWLINE":
            line += 1
            line_start = mo.end()
            continue
        if kind == "SKIP":
            continue
        if kind == "ID" and value in KEYWORDS:
            tokens.append(Token(value.upper(), value, line, col))
        elif kind == "MISMATCH":
            raise Exception(f"Unexpected character {value} at line {line}")
        else:
            tokens.append(Token(kind, value, line, col))

    tokens.append(Token("EOF", "", line, 1))
    return tokens
