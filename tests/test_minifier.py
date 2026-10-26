"""Unit tests for Stage 1 JavaScript minification CLI utility."""

import io
import os
import subprocess
import sys
from minifier import (
    collapse_whitespace,
    minify_javascript,
    parse_output_argument,
    remove_comments,
    run_minifier_cli,
)

EXIT_SUCCESS = 0
MIN_LENGTH = 0
FIRST_EXAMPLE_ID = 1
TOTAL_EXAMPLES_COUNT = 5


def test_remove_comments_single_and_multi():
    """Verify single and multi line comment stripping."""
    raw = "// comment\nvar a = 1; /* block */ var b = 2;"
    clean = remove_comments(raw)
    assert "// comment" not in clean
    assert "/* block */" not in clean
    assert "var a = 1;" in clean
    assert "var b = 2;" in clean


def test_remove_comments_inside_string():
    """Verify comment markers within strings are preserved."""
    raw = 'var url = "http://example.com/*test*/";'
    clean = remove_comments(raw)
    assert clean == raw


def test_collapse_whitespace():
    """Verify whitespace collapsing around operators."""
    raw = "var   x   =   10  ;   var  y = 20 ;"
    collapsed = collapse_whitespace(raw)
    assert "   " not in collapsed


def test_minify_javascript_end_to_end():
    """Verify end to end minification of code block."""
    raw = "function test() {\n    // comment\n    return 42;\n}"
    res = minify_javascript(raw)
    assert "// comment" not in res
    assert len(res) < len(raw)


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
