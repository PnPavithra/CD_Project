# ui.py

from gle_parser import run_gle

print("=== GLE Parser UI ===")
filename = input("Enter test case filename: ")

try:
    with open(filename, "r") as f:
        code = f.read()
        result = run_gle(code)
        print("\n--- Result ---")
        print(result)
except FileNotFoundError:
    print("File not found!")
