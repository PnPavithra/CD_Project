# gle_parser.py

from lexer import lex
from phase1 import Phase1Parser
from phase2 import Phase2Parser
from phase3 import Phase3Parser

def run_gle(code: str):
    tokens = lex(code)

    # Global Phase
    try:
        Phase1Parser(tokens).parse()
    except Exception as e:
        return str(e)

    # Local Phase
    try:
        Phase2Parser(tokens).parse()
    except Exception as e:
        return str(e)

    # Expression Phase
    try:
        Phase3Parser(tokens).parse()
    except Exception as e:
        return str(e)

    return "No syntax errors found."