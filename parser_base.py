# parser_base.py

class ParserBase:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    @property
    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.current
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def match(self, *types):
        if self.current.type in types:
            self.advance()
            return True
        return False

    def expect(self, ttype, phase, message, hint=None):
        if self.current.type == ttype:
            return self.advance()
        from exceptions import ParseError
        raise ParseError(message, self.current.line,
                         self.current.column, phase, hint)
