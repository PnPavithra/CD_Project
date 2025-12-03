from flask import Flask, render_template, request
import sys
import os
import json

# Add parent directory to Python path so we can import gle_parser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gle_parser import run_gle

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    ast_data = "{}"

    if request.method == "POST":
        file = request.files["codefile"]
        code = file.read().decode("utf-8")

        output = run_gle(code)

        if isinstance(output, tuple) and len(output) == 2:
            result, ast_data = output
        else:
            result = output

    return render_template("index.html", result=result, ast=ast_data)


if __name__ == "__main__":
    app.run(debug=True)
