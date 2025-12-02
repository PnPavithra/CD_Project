# phase1.py

from lexer import Token
from exceptions import ParseError
from parser_base import ParserBase

class Phase1Parser(ParserBase):
    PHASE = "GLOBAL"

    def parse(self):
        while self.current.type != "EOF":
            self.parse_function()

    def parse_function(self):
        self.expect("INT", self.PHASE, "Expected 'int' at function start.")
        self.expect("ID", self.PHASE, "Expected function name.")
        self.expect("LPAREN", self.PHASE, "Expected '(' after function name.")
        self.expect("RPAREN", self.PHASE, "Expected ')' after '('.")
        lbrace = self.current
        self.expect("LBRACE", self.PHASE, "Expected '{' to start function body.")

        depth = 1
        while depth > 0 and self.current.type != "EOF":
            if self.current.type == "LBRACE":
                depth += 1
            elif self.current.type == "RBRACE":
                depth -= 1
            self.advance()

        if depth != 0:
            raise ParseError("Missing closing '}' for function.",
                             lbrace.line, lbrace.column, self.PHASE)
