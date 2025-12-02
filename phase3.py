# phase3.py

from parser_base import ParserBase
from exceptions import ParseError

class Phase3Parser(ParserBase):
    PHASE = "EXPRESSION"

    def parse(self):
        while self.current.type != "EOF":
            self.parse_function()

    def parse_function(self):
        self.expect("INT", self.PHASE, "Expected 'int' at start of function.")
        self.expect("ID", self.PHASE, "Expected function name.")
        self.expect("LPAREN", self.PHASE, "Expected '(' after function name.")
        self.expect("RPAREN", self.PHASE, "Expected ')' after '('.")
        self.parse_block()

    def parse_block(self):
        self.expect("LBRACE", self.PHASE, "Expected '{' to start block.")
        while self.current.type not in ("RBRACE", "EOF"):
            self.parse_statement()
        self.expect("RBRACE", self.PHASE, "Expected '}' to close block.")

    # -----------------------------
    # STATEMENTS
    # -----------------------------
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
            if self.current.type != "SEMICOL":
                self.parse_expression()
            self.expect("SEMICOL", self.PHASE,
                        "Missing ';' after statement.",
                        "End statements with ';'.")

    def parse_if(self):
        if_tok = self.advance()
        self.expect("LPAREN", self.PHASE, "Expected '(' after if.")
        self.parse_expression()
        self.expect("RPAREN", self.PHASE, "Expected ')' after if condition.")
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' after if condition.",
                             self.current.line, self.current.column, self.PHASE)
        self.parse_block()

        if self.current.type == "ELSE":
            self.advance()
            if self.current.type == "IF":
                self.parse_if()
            else:
                if self.current.type != "LBRACE":
                    raise ParseError("Expected '{' after else.",
                                     self.current.line, self.current.column, self.PHASE)
                self.parse_block()

    def parse_while(self):
        while_tok = self.advance()
        self.expect("LPAREN", self.PHASE, "Expected '(' after while.")
        self.parse_expression()
        self.expect("RPAREN", self.PHASE, "Expected ')' after while condition.")
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' after while condition.",
                             self.current.line, self.current.column, self.PHASE)
        self.parse_block()

    def parse_return(self):
        ret = self.advance()
        if self.current.type == "SEMICOL":
            self.advance()
        else:
            self.parse_expression()
            self.expect("SEMICOL", self.PHASE,
                        "Missing ';' after return value.")

    # -----------------------------
    # EXPRESSIONS
    # -----------------------------
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
            self.expect("RPAREN", self.PHASE,
                        "Expected ')' after expression.",
                        "Ensure every '(' has a matching ')'.")
            return expr

        raise ParseError(
            f"Expected expression but found '{tok.value}'",
            tok.line, tok.column, self.PHASE,
            "Use a valid variable, number, or '( expression )'."
        )
