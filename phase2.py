# phase2.py

from parser_base import ParserBase
from exceptions import ParseError

class Phase2Parser(ParserBase):
    PHASE = "LOCAL"

    def parse(self):
        while self.current.type != "EOF":
            self.parse_function()

    def parse_function(self):
        self.expect("INT", self.PHASE, "Expected 'int'.")
        self.expect("ID", self.PHASE, "Expected function name.")
        self.expect("LPAREN", self.PHASE, "Expected '('.")
        self.expect("RPAREN", self.PHASE, "Expected ')'.")
        self.parse_block()

    def parse_block(self):
        self.expect("LBRACE", self.PHASE, "Expected '{'.")
        while self.current.type not in ("RBRACE", "EOF"):
            self.parse_statement()
        self.expect("RBRACE", self.PHASE, "Missing '}'.")

    def parse_statement(self):
        if self.current.type == "IF":
            self.parse_if()
        elif self.current.type == "WHILE":
            self.parse_while()
        elif self.current.type == "RETURN":
            self.parse_return()
        else:
            self.skip_to_semicolon()

    def parse_if(self):
        if_tok = self.advance()
        if not self.match("LPAREN"):
            raise ParseError("Missing '(' after if",
                             if_tok.line, if_tok.column, self.PHASE)
        # skip until ')'
        while self.current.type not in ("RPAREN", "EOF"):
            self.advance()
        self.expect("RPAREN", self.PHASE, "Missing ')' after if condition.")
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' after if condition.",
                             self.current.line, self.current.column, self.PHASE)
        self.parse_block()

    def parse_while(self):
        self.advance()
        self.expect("LPAREN", self.PHASE, "Expected '(' after while.")
        while self.current.type not in ("RPAREN", "EOF"):
            self.advance()
        self.expect("RPAREN", self.PHASE, "Missing ')' in while condition.")
        self.parse_block()

    def parse_return(self):
        self.advance()
        if self.current.type == "SEMICOL":
            self.advance()
        else:
            self.skip_to_semicolon(required=True)

    def skip_to_semicolon(self, required=False):
        while self.current.type not in ("SEMICOL", "EOF"):
            self.advance()
        if self.current.type == "SEMICOL":
            self.advance()
        elif required:
            raise ParseError("Missing ';'", self.current.line,
                             self.current.column, self.PHASE)
