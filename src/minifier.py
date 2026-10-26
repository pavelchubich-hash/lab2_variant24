"""JavaScript minification module for Stage 1 computational task."""

import sys

DEFAULT_OUTPUT_PATH = "minified_output.js"
SHORT_OUTPUT_FLAG = "-o"
LONG_OUTPUT_FLAG = "--output"
MIN_VALID_INDEX = 0
NEXT_OFFSET = 1
DOUBLE_OFFSET = 2
MIN_ARGS_COUNT = 1
EMPTY_LENGTH = 0
SINGLE_SPACE = " "
EMPTY_STRING = ""
NEWLINE_CHAR = "\n"


def _process_comment_chars(ch: str, nxt: str, state: dict) -> int:
    """Update comment flags and return consumed character count."""
    if state["in_single"]:
        if ch == NEWLINE_CHAR:
            state["in_single"] = False
            state["result"].append(ch)
        return NEXT_OFFSET
    if state["in_multi"]:
        if ch == "*" and nxt == "/":
            state["in_multi"] = False
            return DOUBLE_OFFSET
        return NEXT_OFFSET
    if ch == "/" and nxt == "/":
        state["in_single"] = True
        return DOUBLE_OFFSET
    if ch == "/" and nxt == "*":
        state["in_multi"] = True
        return DOUBLE_OFFSET
    return MIN_VALID_INDEX


def _process_string_chars(
    code: str, idx: int, total: int, state: dict
) -> int:
    """Handle character inside or entering a string literal."""
    ch = code[idx]
    if state["in_string"]:
        state["result"].append(ch)
        if ch == "\\" and idx + NEXT_OFFSET < total:
            state["result"].append(code[idx + NEXT_OFFSET])
            return DOUBLE_OFFSET
        if ch == state["quote"]:
            state["in_string"] = False
            state["quote"] = EMPTY_STRING
        return NEXT_OFFSET
    if ch in ("'", '"', "`"):
        state["in_string"] = True
        state["quote"] = ch
        state["result"].append(ch)
        return NEXT_OFFSET
    return MIN_VALID_INDEX


def remove_comments(source_code: str) -> str:
    """Remove single-line and multi-line comments from JavaScript source."""
    state = {
        "result": [],
        "in_string": False,
        "quote": EMPTY_STRING,
        "in_single": False,
        "in_multi": False,
    }
    idx = MIN_VALID_INDEX
    total = len(source_code)
    while idx < total:
        ch = source_code[idx]
        nxt = (
            source_code[idx + NEXT_OFFSET]
            if idx + NEXT_OFFSET < total
            else EMPTY_STRING
        )
        if state["in_single"] or state["in_multi"]:
            idx += _process_comment_chars(ch, nxt, state)
            continue
        step = _process_string_chars(source_code, idx, total, state)
        if step > MIN_VALID_INDEX:
            idx += step
            continue
        c_step = _process_comment_chars(ch, nxt, state)
        if c_step > MIN_VALID_INDEX:
            idx += c_step
            continue
        state["result"].append(ch)
        idx += NEXT_OFFSET
    return "".join(state["result"])


def _handle_ws_char(char: str, res: list) -> None:
    """Format whitespace outside string literals."""
    delimiters = " \n;{}(),:=+-*/"
    if char in ("\n", "\t", " "):
        if res and res[-NEXT_OFFSET] not in delimiters:
            res.append(SINGLE_SPACE)
    elif char in ";{}(),:=+-*/":
        if res and res[-NEXT_OFFSET] == SINGLE_SPACE:
            res.pop()
        res.append(char)
    else:
        res.append(char)


def collapse_whitespace(code: str) -> str:
    """Collapse consecutive whitespace and trim redundant spaces."""
    lines = [line.strip() for line in code.splitlines()]
    trimmed_code = "\n".join([line for line in lines if len(line) > 0])
    state = {"result": [], "in_string": False, "quote": EMPTY_STRING}
    idx = MIN_VALID_INDEX
    total = len(trimmed_code)

    while idx < total:
        step = _process_string_chars(trimmed_code, idx, total, state)
        if step > MIN_VALID_INDEX:
            idx += step
            continue
        _handle_ws_char(trimmed_code[idx], state["result"])
        idx += NEXT_OFFSET

    return "".join(state["result"])


def minify_javascript(source_code: str) -> str:
    """Minify JavaScript source by removing comments and extra spaces."""
    without_comments = remove_comments(source_code)
    return collapse_whitespace(without_comments)


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


def run_minifier_cli(args: list) -> str:
    """Read stdin, minify JavaScript code, and save result to disk."""
    output_path = parse_output_argument(args)
    input_data = sys.stdin.read()
    minified = minify_javascript(input_data)
    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write(minified)
    return output_path


if __name__ == "__main__":
    run_minifier_cli(sys.argv)
