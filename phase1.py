from lexer import Token
from exceptions import ParseError
from parser_base import ParserBase

class Phase1Parser(ParserBase):
    PHASE = "GLOBAL"

    def parse(self):
        while self.current.type != "EOF":
            self.parse_function()

    def parse_function(self):
        # ------------------------
        # 1. Parse return type
        # ------------------------
        self.expect("INT", self.PHASE, "Expected 'int' at function start.")

        # Allow newline/space before function name
        while self.current.type in ("SKIP", "NEWLINE"):
            self.advance()

        # ------------------------
        # 2. Parse function name
        # ------------------------
        if self.current.type != "ID":
            raise ParseError("Expected function name.",
                             self.current.line, self.current.column, self.PHASE)

        self.advance()  # consume function name

        # Allow whitespace before '('
        while self.current.type in ("SKIP", "NEWLINE"):
            self.advance()

        # ------------------------
        # 3. Opening Parenthesis
        # ------------------------
        if self.current.type != "LPAREN":
            raise ParseError("Expected '(' after function name.",
                             self.current.line, self.current.column, self.PHASE)
        self.advance()

        # ------------------------
        # 4. Parse params (we ignore content)
        # ------------------------
        while self.current.type not in ("RPAREN", "EOF"):
            self.advance()

        if self.current.type != "RPAREN":
            raise ParseError("Expected ')' after '('.",
                             self.current.line, self.current.column, self.PHASE)
        self.advance()

        # Allow whitespace before '{'
        while self.current.type in ("SKIP", "NEWLINE"):
            self.advance()

        # ------------------------
        # 5. Opening brace {
        # ------------------------
        if self.current.type != "LBRACE":
            raise ParseError("Expected '{' to start function body.",
                             self.current.line, self.current.column, self.PHASE)

        lbrace = self.current
        self.advance()

        # ------------------------
        # 6. Scan until matching }
        # ------------------------
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
