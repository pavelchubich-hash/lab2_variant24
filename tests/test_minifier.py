"""Unit tests for Stage 1 JavaScript minification CLI utility."""

import io
import os
import subprocess
import sys

SRC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"
)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

minifier = __import__("minifier")
minify_javascript = minifier.minify_javascript
parse_output_argument = minifier.parse_output_argument
run_minifier_cli = minifier.run_minifier_cli

EXIT_SUCCESS = 0
MIN_LENGTH = 0
FIRST_EXAMPLE_ID = 1
TOTAL_EXAMPLES_COUNT = 5


def test_minify_javascript():
    """Verify JavaScript code minification using jsmin."""
    source = "/* comment */\nfunction add(a, b) {\n    return a + b;\n}"
    result = minify_javascript(source)
    assert "/* comment */" not in result
    assert len(result) < len(source)


def test_parse_output_argument():
    """Verify parsing of CLI arguments for output destination."""
    default_out = parse_output_argument(["script.py"])
    assert default_out == "minified_output.js"

    custom_out = parse_output_argument(["script.py", "-o", "custom.js"])
    assert custom_out == "custom.js"


def test_run_minifier_cli_via_stdin(monkeypatch, tmp_path):
    """Verify CLI function execution with mocked stdin."""
    target_file = str(tmp_path / "out.js")
    monkeypatch.setattr(sys, "stdin", io.StringIO("var a = 1;"))
    res_path = run_minifier_cli(["cli.py", "-o", target_file])
    assert res_path == target_file
    assert os.path.exists(target_file)


def test_demonstration_examples_via_subprocess():
    """Verify 5 demonstrated examples using subprocess execution."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, "src", "minifier.py")

    limit_idx = TOTAL_EXAMPLES_COUNT + FIRST_EXAMPLE_ID
    for idx in range(FIRST_EXAMPLE_ID, limit_idx):
        in_path = os.path.join(base_dir, "examples", f"input{idx}.js")
        out_path = os.path.join(base_dir, "examples", f"output{idx}.js")

        with open(in_path, "r", encoding="utf-8") as in_f:
            source = in_f.read()

        proc = subprocess.run(
            [sys.executable, script_path, "-o", out_path],
            input=source,
            text=True,
            capture_output=True,
            check=False,
        )
        assert proc.returncode == EXIT_SUCCESS
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > MIN_LENGTH


if __name__ == "__main__":
    test_demonstration_examples_via_subprocess()
