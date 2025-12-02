# exceptions.py

from dataclasses import dataclass

@dataclass
class ParseError(Exception):
    message: str
    line: int
    column: int
    phase: str
    hint: str = None

    def __str__(self):
        output = f"[{self.phase}] Line {self.line}, Col {self.column}: {self.message}"
        if self.hint:
            output += f" Hint: {self.hint}"
        return output
