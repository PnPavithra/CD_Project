#!/usr/bin/env python3
"""
GLE-style 3-phase parser demo for a small C-like language.

Phases:
- Phase 1 (GLOBAL): check function structure only
- Phase 2 (LOCAL): check control structures (if/while/return, blocks)
- Phase 3 (EXPRESSION): full expression parsing and detailed errors
"""

import re
from dataclasses import dataclass
from typing import List, Optional

# ---------------------------
# Token definition & Lexer
# ---------------------------

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

master_pat = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

def lex(code: str) -> List[Token]:
    tokens = []
    line_num = 1
    line_start = 0
    for mo in master_pat.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        col = mo.start() - line_start + 1
        if kind == "NEWLINE":
            line_num += 1
            line_start = mo.end()
        elif kind == "SKIP":
            continue
        elif kind == "ID" and value in KEYWORDS:
            tokens.append(Token(value.upper(), value, line_num, col))
        elif kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character {value!r} at line {line_num} col {col}")
        else:
            tokens.append(Token(kind, value, line_num, col))
    tokens.append(Token("EOF", "", line_num, 1))
    return tokens

# ---------------------------
# Parse Error
# ---------------------------

@dataclass
class ParseError(Exception):
    message: str
    line: int
    column: int
    phase: str
    hint: Optional[str] = None

    def __str__(self):
        base = f"[{self.phase}] Line {self.line}, Col {self.column}: {self.message}"
        if self.hint:
            base += f" Hint: {self.hint}"
        return base

# ---------------------------
# Parser base class
# ---------------------------

class ParserBase:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.current
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def match(self, *types) -> bool:
        if self.current.type in types:
            self.advance()
            return True
        return False

    def expect(self, ttype: str, phase: str, message: str, hint: Optional[str] = None) -> Token:
        if self.current.type == ttype:
            return self.advance()
        raise ParseError(message, self.current.line, self.current.column, phase, hint)

# ---------------------------
# Phase 1: GLOBAL parsing
# ---------------------------

class Phase1Parser(ParserBase):
    PHASE = "GLOBAL"

    def parse(self):
        functions = []
        while self.current.type != "EOF":
            functions.append(self.parse_function())
        return functions

    def parse_function(self):
        # int <id>() { ... }
        self.expect("INT", self.PHASE, "Expected 'int' at start of function definition.",
                    "Did you forget the return type?")
        name_tok = self.expect("ID", self.PHASE, "Expected function name after 'int'.",
                               "Add a valid identifier name for the function.")
        self.expect("LPAREN", self.PHASE, "Expected '(' after function name.",
                    "Add '(' to start the parameter list (even if it's empty).")
        self.expect("RPAREN", self.PHASE, "Expected ')' after '('.",
                    "Close the parameter list with ')'.")
        lbrace_tok = self.current
        self.expect("LBRACE", self.PHASE, "Expected '{' to start function body.",
                    "Add '{' to begin the function body.")
        # Skip until matching RBRACE
        depth = 1
        while depth > 0 and self.current.type != "EOF":
            if self.current.type == "LBRACE":
                depth += 1
            elif self.current.type == "RBRACE":
                depth -= 1
            self.advance()
        if depth != 0:
            # no matching closing brace
            raise ParseError("Function body not properly closed with '}'.",
                             lbrace_tok.line, lbrace_tok.column, self.PHASE,
                             "Ensure every '{' has a matching '}'.")
        return {"name": name_tok.value}

# ---------------------------
# Phase 2: LOCAL parsing
# ---------------------------

class Phase2Parser(ParserBase):
    PHASE = "LOCAL"

    def parse(self):
        while self.current.type != "EOF":
            self.parse_function()

    def parse_function(self):
        self.expect("INT", self.PHASE, "Expected 'int' at start of function definition.",
                    "Did you forget the return type?")
        self.expect("ID", self.PHASE, "Expected function name after 'int'.")
        self.expect("LPAREN", self.PHASE, "Expected '(' after function name.")
        self.expect("RPAREN", self.PHASE, "Expected ')' to close parameter list.")
        self.parse_block()

    def parse_block(self):
        self.expect("LBRACE", self.PHASE, "Expected '{' to start a block.",
                    "Add '{' to begin the block after this statement.")
        while self.current.type not in ("RBRACE", "EOF"):
            self.parse_statement()
        self.expect("RBRACE", self.PHASE, "Expected '}' to close the block.",
                    "Make sure all opened '{' blocks are closed with '}'.")

    def parse_statement(self):
        if self.current.type == "IF":
            self.parse_if()
        elif self.current.type == "WHILE":
            self.parse_while()
        elif self.current.type == "RETURN":
            self.parse_return()
        elif self.current.type == "LBRACE":
            self.parse_block()
        else:
            # treat as expression/other statement and skip until ';'
            self.skip_until_semicolon()

    def parse_if(self):
        if_tok = self.advance()
        if not self.match("LPAREN"):
            raise ParseError("Expected '(' after 'if'.", if_tok.line, if_tok.column, self.PHASE,
                             "Write 'if (<condition>) { ... }'.")
        # check empty or malformed condition
        if self.current.type == "RPAREN":
            raise ParseError("Empty condition in 'if'.", self.current.line, self.current.column,
                             self.PHASE, "Add a condition like 'if (x > 0)'.")
        # skip until matching ')'
        depth = 1
        while depth > 0 and self.current.type != "EOF":
            if self.current.type == "LPAREN":
                depth += 1
            elif self.current.type == "RPAREN":
                depth -= 1
            self.advance()
        if depth != 0:
            raise ParseError("Missing ')' to close 'if' condition.",
                             if_tok.line, if_tok.column, self.PHASE,
                             "Ensure every '(' has a matching ')'.")
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' after 'if' condition.",
                             self.current.line, self.current.column, self.PHASE,
                             "Write 'if (cond) { ... }'.")
        self.parse_block()
        if self.current.type == "ELSE":
            self.advance()
            if self.current.type == "IF":
                self.parse_if()
            else:
                if self.current.type != "LBRACE":
                    raise ParseError("Expected '{' after 'else'.",
                                     self.current.line, self.current.column, self.PHASE,
                                     "Write 'else { ... }'.")
                self.parse_block()

    def parse_while(self):
        while_tok = self.advance()
        if not self.match("LPAREN"):
            raise ParseError("Expected '(' after 'while'.", while_tok.line, while_tok.column,
                             self.PHASE, "Write 'while (<condition>) { ... }'.")
        if self.current.type == "RPAREN":
            raise ParseError("Empty condition in 'while'.", self.current.line, self.current.column,
                             self.PHASE, "Add a loop condition like 'while (i < n)'.")
        depth = 1
        while depth > 0 and self.current.type != "EOF":
            if self.current.type == "LPAREN":
                depth += 1
            elif self.current.type == "RPAREN":
                depth -= 1
            self.advance()
        if depth != 0:
            raise ParseError("Missing ')' to close 'while' condition.",
                             while_tok.line, while_tok.column, self.PHASE,
                             "Ensure every '(' has a matching ')'.")
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' after 'while' condition.",
                             self.current.line, self.current.column, self.PHASE,
                             "Write 'while (cond) { ... }'.")
        self.parse_block()

    def parse_return(self):
        ret_tok = self.advance()
        if self.current.type == "SEMICOL":
            self.advance()
        else:
            self.skip_until_semicolon(required=True, ctx_tok=ret_tok, ctx_word="return")

    def skip_until_semicolon(self, required=False, ctx_tok=None, ctx_word=None):
        while self.current.type not in ("SEMICOL", "EOF", "RBRACE"):
            self.advance()
        if self.current.type == "SEMICOL":
            self.advance()
        elif required:
            raise ParseError(f"Missing ';' after {ctx_word} statement.",
                             ctx_tok.line if ctx_tok else self.current.line,
                             ctx_tok.column if ctx_tok else self.current.column,
                             self.PHASE, f"Terminate the {ctx_word} statement with ';'.")

# ---------------------------
# Phase 3: EXPRESSION parsing
# ---------------------------

class Phase3Parser(ParserBase):
    PHASE = "EXPRESSION"

    def parse(self):
        while self.current.type != "EOF":
            self.parse_function()

    def parse_function(self):
        self.expect("INT", self.PHASE, "Expected 'int' at start of function definition.")
        self.expect("ID", self.PHASE, "Expected function name after 'int'.")
        self.expect("LPAREN", self.PHASE, "Expected '(' after function name.")
        self.expect("RPAREN", self.PHASE, "Expected ')' after '('.")
        self.parse_block()

    def parse_block(self):
        self.expect("LBRACE", self.PHASE, "Expected '{' to start a block.")
        while self.current.type not in ("RBRACE", "EOF"):
            self.parse_statement()
        self.expect("RBRACE", self.PHASE, "Expected '}' to close the block.")

    def parse_statement(self):
        if self.current.type == "IF":
            self.parse_if()
        elif self.current.type == "WHILE":
            self.parse_while()
        elif self.current.type == "RETURN":
            self.parse_return()
        elif self.current.type == "LBRACE":
            self.parse_block()
        else:
            if self.current.type == "SEMICOL":
                self.advance()
            else:
                self.parse_expression()
                self.expect("SEMICOL", self.PHASE, "Missing ';' after expression.",
                            "End the statement with ';'.")

    def parse_if(self):
        if_tok = self.advance()
        self.expect("LPAREN", self.PHASE, "Expected '(' after 'if'.",
                    "Write 'if (<condition>) { ... }'.")
        self.parse_expression()
        self.expect("RPAREN", self.PHASE, "Expected ')' after if condition.",
                    "Close the condition: 'if (x > 0)'.")
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' after 'if' condition.", self.current.line,
                             self.current.column, self.PHASE,
                             "Write 'if (cond) { ... }'.")
        self.parse_block()
        if self.current.type == "ELSE":
            self.advance()
            if self.current.type == "IF":
                self.parse_if()
            else:
                if self.current.type != "LBRACE":
                    raise ParseError("Expected '{' after 'else'.", self.current.line,
                                     self.current.column, self.PHASE,
                                     "Write 'else { ... }'.")
                self.parse_block()

    def parse_while(self):
        while_tok = self.advance()
        self.expect("LPAREN", self.PHASE, "Expected '(' after 'while'.",
                    "Write 'while (<condition>) { ... }'.")
        self.parse_expression()
        self.expect("RPAREN", self.PHASE, "Expected ')' after while condition.",
                    "Close the condition: 'while (i < n)'.")
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' after 'while' condition.", self.current.line,
                             self.current.column, self.PHASE,
                             "Write 'while (cond) { ... }'.")
        self.parse_block()

    def parse_return(self):
        ret_tok = self.advance()
        if self.current.type == "SEMICOL":
            self.advance()
        else:
            self.parse_expression()
            self.expect("SEMICOL", self.PHASE, "Missing ';' after return value.",
                        "Write 'return value;'.")

    # Expression grammar
    def parse_expression(self):
        return self.parse_equality()

    def parse_equality(self):
        node = self.parse_comparison()
        while self.current.type == "OP" and self.current.value in ("==", "!="):
            op = self.advance()
            right = self.parse_comparison()
            node = ("binop", op.value, node, right)
        return node

    def parse_comparison(self):
        node = self.parse_term()
        while self.current.type == "OP" and self.current.value in ("<", ">", "<=", ">="):
            op = self.advance()
            right = self.parse_term()
            node = ("binop", op.value, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current.type == "OP" and self.current.value in ("+", "-"):
            op = self.advance()
            right = self.parse_factor()
            node = ("binop", op.value, node, right)
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.current.type == "OP" and self.current.value in ("*", "/"):
            op = self.advance()
            right = self.parse_unary()
            node = ("binop", op.value, node, right)
        return node

    def parse_unary(self):
        if self.current.type == "OP" and self.current.value in ("+", "-"):
            op = self.advance()
            right = self.parse_unary()
            return ("unary", op.value, right)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current
        if tok.type == "NUMBER":
            self.advance()
            return ("num", tok.value)
        if tok.type == "ID":
            self.advance()
            return ("id", tok.value)
        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.expect("RPAREN", self.PHASE, "Expected ')' after expression.",
                        "Every '(' must be closed with ')'.")
            return expr
        raise ParseError("Expected an expression here, but found "
                         f"'{tok.value}' ({tok.type}).",
                         tok.line, tok.column, self.PHASE,
                         "Use a variable, number, or '( expression )'.")

# ---------------------------
# GLE driver
# ---------------------------

def run_gle(code: str):
    tokens = lex(code)
    # Phase 1
    try:
        Phase1Parser(tokens).parse()
    except ParseError as e:
        return e
    # Phase 2
    try:
        Phase2Parser(tokens).parse()
    except ParseError as e:
        return e
    # Phase 3
    try:
        Phase3Parser(tokens).parse()
    except ParseError as e:
        return e
    return None

# ---------------------------
# Simple CLI
# ---------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python gle_parser.py <source-file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        code = f.read()

    error = run_gle(code)
    if error is None:
        print("No syntax errors found by GLE parser.")
    else:
        print("GLE syntax error report:")
        print(error)
