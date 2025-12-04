from flask import Flask, render_template, request
import sys
import os
import json

# Add parent directory to Python path so we can import gle_parser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gle_parser import run_gle



# Add parent directory to Python path if needed (only if gle_parser is in parent)
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    ast_data = None

    if request.method == "POST":
        file = request.files["codefile"]
        code = file.read().decode("utf-8")

        output = run_gle(code)

        # Support run_gle returning either a single value or a tuple (result, ast)
        if isinstance(output, tuple) and len(output) == 2:
            result, ast_obj = output
            ast_data = json.dumps(ast_obj)
        else:
            result = output
            ast_data = json.dumps({"type": "Program", "globals": [], "functions": []})

    return render_template("index.html", result=result, ast=ast_data)

if __name__ == "__main__":
    app.run(debug=True)
