from flask import Flask, render_template, request
import sys
import os

# Add parent directory to Python path so we can import gle_parser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gle_parser import run_gle

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        file = request.files["codefile"]
        code = file.read().decode("utf-8")
        result = run_gle(code)
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
