import re
from enum import Enum
import ast

VERSION = "0.1.0"

# Regex types

INDENT_REGEX = re.compile('(\t+)')
EXTRANEOUS_WHITESPACE_REGEX = re.compile('[\[({] | [\]});:]')

# Violation

class ViolationLevel(Enum):
    WARNING = 0
    ERROR = 1


class ViolationType(Enum):
    HAS_TAB = 1
    BLANK_LINE_WHITESPACE = 2
    TRAILING_WHITESPACE = 3
    LINE_TOO_LONG = 4
    EXTRANEOUS_WHITESPACE = 5
    MULTIPLE_IMPORT = 6
    BLANK_LINE_AFTER_DECORATOR = 7
    NOT_ENOUGH_BLANK_LINES = 8
    TOO_MANY_BLANK_LINES = 9

#
# Check functions:
# Return type: tuple : (Level: ViolationLevel, 
#               Type: ViolationType,
#               Line info: (line_number: int, offset: int),
#               Description: str)
#

# Check physical lines

def check_tabs(physical_line, line_number):
    # Test case:
    # if True:\n\tb = 1\na = 2

    match_obj = INDENT_REGEX.search(physical_line)
    if match_obj is not None:
        offset = match_obj.span()[0]
        return (ViolationLevel.ERROR, ViolationType.HAS_TAB, (line_number, offset),
            "Indentation contains tabs")


def check_trailing_whitespace(physical_line, line_number):
    # Test case:
    # if True: \nb = 1\na = 2\n    \n

    whitespace_charset = " \t\v"
    real_line = physical_line.rstrip(whitespace_charset)
    if real_line != physical_line:
        if len(real_line) == 0:
            return (ViolationLevel.ERROR, ViolationType.BLANK_LINE_WHITESPACE, \
                (line_number, 0), "Blank line contains whitespace")
        else:
            return (ViolationLevel.ERROR, ViolationType.TRAILING_WHITESPACE, \
                (line_number, len(real_line)), "Line with trailing whitespace")


def check_line_length(physical_line, line_number):
    # Test case:
    # a = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    
    real_line = physical_line.lstrip()
    length = len(real_line)
    
    if length > 79:
        # Ignore long shebang line
        if line_number == 0 and physical_line.startswith('#!'):
            return

        # Ignore comments
        if real_line.startswith("#"):
            return
        
        return (ViolationLevel.ERROR, ViolationType.LINE_TOO_LONG, \
            (line_number, 0), "Line too long")


# Check logical lines

_previous_logical = {
    "previous_line": "",
    "blank_lines": 0,
    "previous_code_segment": ""
}

def check_extraneous_whitespace(logical_line, line_number, extarParams):
    # Test case:
    # aaa( aa[1], {bb: 2})
    
    # Ignore comment
    if logical_line.strip().startswith("#"):
        return

    for match_obj in EXTRANEOUS_WHITESPACE_REGEX.finditer(logical_line):
        text = match_obj.group()
        # [({\s
        if text.endswith(" "):
            offset = match_obj.span()[0]
            char = text[0]
            return (ViolationLevel.ERROR, ViolationType.EXTRANEOUS_WHITESPACE, \
                (line_number, offset), "Whitespace after %s" % char)
        # \s])}:; 
        else:
            offset = match_obj.span()[1] - 1
            char = text[-1]
            return (ViolationLevel.ERROR, ViolationType.EXTRANEOUS_WHITESPACE, \
                (line_number, offset), "Whitespace before %s" % char)


def check_multiple_import(logical_line, line_number, extarParams):
    # Test case:
    # import re, copy

    if logical_line.startswith("import"):
        if "," in logical_line:
            return (ViolationLevel.ERROR, ViolationType.MULTIPLE_IMPORT, \
                (line_number, 0), "Multiple import in one line")


def check_correct_blank_lines(logical_line, line_number, extar_params):
    # Test case:
    # def a():\n    return\ndef b(): \n    return 1
    
    if logical_line == "\n":
        previous_line = extar_params["previous_line"].strip()
        if previous_line.startswith("@"):
            return (ViolationLevel.ERROR, ViolationType.BLANK_LINE_AFTER_DECORATOR, \
                (line_number, 0), "Blank line after decorator")

    previous_code_segment = extar_params["previous_code_segment"]
    blank_lines = extar_params["blank_lines"]
    if logical_line.startswith("def") or logical_line.startswith("class"):
        if previous_code_segment == "function" or previous_code_segment == "class":
            if blank_lines < 2:
                return (ViolationLevel.ERROR, ViolationType.NOT_ENOUGH_BLANK_LINES, \
                    (line_number, 0), "Expected 2 blank lines, found %d" % blank_lines)
            if blank_lines > 2:
                return (ViolationLevel.ERROR, ViolationType.TOO_MANY_BLANK_LINES, \
                    (line_number, 0), "Expected 2 blank lines, found %d" % blank_lines)

# Check AST

def check_naming(node):
    # Test case:
    # 
    if isinstance(node, ast.Assign):
        return (ViolationLevel.ERROR, ViolationType.TOO_MANY_BLANK_LINES, \
                    (node.lineno, 0), "Assign")

# Core checks

ALL_CHECKS = {
    "physical_line": [
        check_tabs,
        check_trailing_whitespace,
        check_line_length],
    "logical_line": [
        check_extraneous_whitespace,
        check_multiple_import,
        check_correct_blank_lines],
    "ast": [check_naming]
}

import sys
import copy

# use `# dinodon:disable xxx` to disable a specific rule
# use `# dinodon:enable xxx` to enable a specific rule
def _update_current_checks(lint_type, line, current_checks):
    real_line = line.strip()

    if real_line.startswith("# dinodon:"):
        real_line = real_line[10:]
        if real_line.startswith("disable"):
            function_names = real_line.split(" ")[1:]
            remove_functions = [func for func in ALL_CHECKS[lint_type] \
                if func.__name__ in function_names]
            return list(set(current_checks) - set(remove_functions))
        if real_line.startswith("enable"):
            function_names = real_line.split(" ")[1:]
            add_functions = [func for func in ALL_CHECKS[lint_type] \
                if func.__name__ in function_names]
            return list(set(current_checks) | set(add_functions))
    else:
        return current_checks


def _check_physical_lines(lint_file):
    results = []

    with open(lint_file, 'r') as f:
        current_checks = copy.deepcopy(ALL_CHECKS["physical_line"])
        for (index, line) in enumerate(f.readlines()):
            line_number = index + 1
            current_checks = _update_current_checks("physical_line", line, current_checks)

            for check in current_checks:
                result = check(line, line_number)
                if result is not None:
                    results.append(result)

    return results


def _check_logical_lines(lint_file):
    results = []

    with open(lint_file, 'r') as f:
        current_checks = copy.deepcopy(ALL_CHECKS["logical_line"])
        for (index, line) in enumerate(f.readlines()):
            line_number = index + 1
            current_checks = _update_current_checks("logical_line", line, current_checks)
            
            for check in current_checks:
                result = check(line, line_number, _previous_logical)
                if result is not None:
                    results.append(result)

            # set common logical info
            _previous_logical["previous_line"] = line

            if line == "\n":
                _previous_logical["blank_lines"] += 1
            elif not line.strip().startswith("#"):
                _previous_logical["blank_lines"] = 0

            if line.startswith("def"):
                _previous_logical["previous_code_segment"] = "function"
            elif line.startswith("class"):
                _previous_logical["previous_code_segment"] = "class"
            elif line != "\n" and line[0] != " ":
                _previous_logical["previous_code_segment"] = "other"

    return results


def _check_ast(lint_file):
    results = []

    with open(lint_file, 'r') as f:
        current_checks = copy.deepcopy(ALL_CHECKS["ast"])

        code = f.read()
        root_node = ast.parse(code)

        custom_configs = []
        for (index, line) in enumerate(code.split("\n")):
            line_number = index + 1
            real_line = line.strip()
            if real_line.startswith("# dinodon:"):
                custom_configs.append((line_number, line))

        stack = [root_node]
        while len(stack):
            node = stack.pop()

            children = list(ast.iter_child_nodes(node))
            children.reverse()
            stack += children
            
            if len(custom_configs) and hasattr(node, "lineno") \
                and custom_configs[0][0] < node.lineno:
                config_line = custom_configs.pop(0)
                current_checks = _update_current_checks("ast", config_line[1], current_checks)

            for check in current_checks:
                result = check(node)
                if result is not None:
                    results.append(result)

    return results


def _check_single_file(lint_file):
    physical_results = _check_physical_lines(lint_file)
    logical_results = _check_logical_lines(lint_file)
    ast_results = _check_ast(lint_file)

    total_results = physical_results + logical_results + ast_results
    # sort by line number
    total_results.sort(key=lambda result: result[2][0])
    for result in total_results:
        _log_result(result)

# Log

class Log:
    def info(message):
        print(message)

    def error(message):
        print("Error: %s" % message)
        # return

    def warning(message):
        print("Warning: %s" % message)


def _log_result(result):
    violation_level, violation_type, (line_number, column), description = result

    message = "line %d, column %d <%s>" \
        % (line_number, column, description)

    if violation_level == ViolationLevel.WARNING:
        Log.warning(message)
    else:
        Log.error(message)

# Command Line

def _show_help_info():
    Log.info("""  Usage:
    python3 dinodon.py [command] [options] [files]
  Command:
    self-check: Run lint for dinodon itself
    help: Display general or command-specific help
    version: Display the current version of dinodon
    run: Run lint for specific file""")


def _show_version():
    Log.info(VERSION)

if __name__ == '__main__':
    lint_files = []
    commands = []
    options = []

    if "dinodon.py" in sys.argv:
        sys.argv.remove("dinodon.py")

    for parm in sys.argv:
        if parm.endswith(".py") and not parm.startswith("dinodon"):
            lint_files.append(parm)
        elif parm.startswith("--"):
            options.append(parm)
        else:
            commands.append(parm)

    if len(commands) > 0:
        # 1. self check
        if "self-check" == commands[0]:
            _check_single_file("dinodon.py")

        # 2. show help
        if "help" == commands[0]:
            _show_help_info()

        # 3. show version
        if "version" == commands[0]:
            _show_version()

        # 4. run lint
        if "run" == commands[0]:
            print()
    
    else:
        # Log.error("Please run dinodon with a command")
        _check_single_file("dinodon.py")