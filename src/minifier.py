"""JavaScript minification module using jsmin library."""

import sys
from jsmin import jsmin

DEFAULT_OUTPUT_PATH = "minified_output.js"
SHORT_OUTPUT_FLAG = "-o"
LONG_OUTPUT_FLAG = "--output"
DOUBLE_OFFSET = 2
MIN_ARGS_COUNT = 1


def parse_output_argument(args: list) -> str:
    """Extract output file path from command line arguments."""
    total_args = len(args)
    if total_args > MIN_ARGS_COUNT:
        first_arg = args[MIN_ARGS_COUNT]
        if first_arg in (SHORT_OUTPUT_FLAG, LONG_OUTPUT_FLAG):
            if total_args > DOUBLE_OFFSET:
                return args[DOUBLE_OFFSET]
        return first_arg
    return DEFAULT_OUTPUT_PATH


def minify_javascript(source_code: str) -> str:
    """Minify JavaScript source using jsmin."""
    return jsmin(source_code)


def run_minifier_cli(args: list) -> str:
    """Read stdin, minify JavaScript code, and save result to disk."""
    output_path = parse_output_argument(args)
    input_data = sys.stdin.read()
    minified = jsmin(input_data)
    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write(minified)
    return output_path


if __name__ == "__main__":
    run_minifier_cli(sys.argv)
