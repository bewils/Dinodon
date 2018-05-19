import re
from enum import Enum

Version = "0.1.0"

# Regex types

Indent_Regex = re.compile('(\t+)')
Extraneous_Whitespace_Regex = re.compile('[\[({] | [\]});:]')

# Violation

class ViolationLevel(Enum):
    Warning = 0
    Error = 1


class ViolationType(Enum):
    Has_Tab = 1
    Blank_Line_Whitespace = 2
    Trailing_Whitespace = 3
    Line_Too_Long = 4
    Extraneous_Whitespace = 5
    Multiple_Import = 6
    Blank_Line_After_Decorator = 7
    Not_Enough_Blank_Lines = 8
    Too_Many_Blank_Lines = 9

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

    match_obj = Indent_Regex.search(physical_line)
    if match_obj is not None:
        offset = match_obj.span()[0]
        return (ViolationLevel.Error, ViolationType.Has_Tab, (line_number, offset),
            "Indentation contains tabs")


def check_trailing_whitespace(physical_line, line_number):
    # Test case:
    # if True: \nb = 1\na = 2\n    \n

    whitespace_charset = " \t\v"
    real_line = physical_line.rstrip(whitespace_charset)
    if real_line != physical_line:
        if len(real_line) == 0:
            return (ViolationLevel.Error, ViolationType.Blank_Line_Whitespace, \
                (line_number, 0), "Blank line contains whitespace")
        else:
            return (ViolationLevel.Error, ViolationType.Trailing_Whitespace, \
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
        
        return (ViolationLevel.Error, ViolationType.Line_Too_Long, \
            (line_number, 0), "Line too long")


# Check logical lines

_previous_logical = {
    "previous_line": "",
    "blank_lines": 0,
    "previous_code_segment": ""}

def check_extraneous_whitespace(logical_line, line_number):
    # Test case:
    # aaa( aa[1], {bb: 2})
    
    # Ignore comment
    if logical_line.strip().startswith("#"):
        return

    for match_obj in Extraneous_Whitespace_Regex.finditer(logical_line):
        text = match_obj.group()
        # [({\s
        if text.endswith(" "):
            offset = match_obj.span()[0]
            char = text[0]
            return (ViolationLevel.Error, ViolationType.Extraneous_Whitespace, \
                (line_number, offset), "Whitespace after %s" % char)
        # \s])}:; 
        else:
            offset = match_obj.span()[1] - 1
            char = text[-1]
            return (ViolationLevel.Error, ViolationType.Extraneous_Whitespace, \
                (line_number, offset), "Whitespace before %s" % char)


def check_multiple_import(logical_line, line_number):
    # Test case:
    # import re, copy

    if logical_line.startswith("import"):
        if "," in logical_line:
            return (ViolationLevel.Error, ViolationType.Multiple_Import, \
                (line_number, 0), "Multiple import in one line")


def check_correct_blank_lines(logical_line, line_number):
    # Test case:
    # def a():\n    return\ndef b(): \n    return 1
    
    if logical_line == "\n":
        previous_line = _previous_logical["previous_line"].strip()
        if previous_line.startswith("@"):
            return (ViolationLevel.Error, ViolationType.Blank_Line_After_Decorator, \
                (line_number, 0), "Blank line after decorator")

    previous_code_segment = _previous_logical["previous_code_segment"]
    blank_lines = _previous_logical["blank_lines"]
    if logical_line.startswith("def") or logical_line.startswith("class"):
        if previous_code_segment == "function" or previous_code_segment == "class":
            if blank_lines < 2:
                return (ViolationLevel.Error, ViolationType.Not_Enough_Blank_Lines, \
                    (line_number, 0), "Expected 2 blank lines, found %d" % blank_lines)
            if blank_lines > 2:
                return (ViolationLevel.Error, ViolationType.Too_Many_Blank_Lines, \
                    (line_number, 0), "Expected 2 blank lines, found %d" % blank_lines)

# Check AST

# Core checks

All_Checks = {
    "physical_line": [
        check_tabs,
        check_trailing_whitespace,
        check_line_length],
    "logical_line": [
        check_extraneous_whitespace,
        check_multiple_import,
        check_correct_blank_lines],
    "ast": []
}

import sys
import copy

# use `# dinodon:disable xxx` to disable a specific rule
# use `# dinodon:enable xxx` to enable a specific rule
def _update_current_checks(lintType, line, current_checks):
    real_line = line.strip()

    if real_line.startswith("# dinodon:"):
        real_line = real_line[10:]
        if real_line.startswith("disable"):
            function_names = real_line.split(" ")[1:]
            remove_functions = filter(lambda func: func.__name__ in function_names, \
                All_Checks[lintType])
            return list(set(current_checks) - set(remove_functions))
        if real_line.startswith("enable"):
            function_names = real_line.split(" ")[1:]
            add_functions = filter(lambda func: func.__name__ in function_names, \
                All_Checks[lintType])
            return list(set(current_checks) | set(add_functions))
    else:
        return current_checks


def _check_physical_lines(lint_file):
    with open(lint_file, 'r') as f:
        current_checks = copy.deepcopy(All_Checks["physical_line"])
        for (line_number, line) in enumerate(f.readlines()):
            current_checks = _update_current_checks("physical_line", line, current_checks)

            for check in current_checks:
                result = check(line, line_number + 1)
                if result is not None:
                    _log_result(result)


def _check_logical_lines(lint_file):
    with open(lint_file, 'r') as f:
        current_checks = copy.deepcopy(All_Checks["logical_line"])
        for (line_number, line) in enumerate(f.readlines()):
            current_checks = _update_current_checks("logical_line", line, current_checks)
            
            for check in current_checks:
                result = check(line, line_number + 1)
                if result is not None:
                    _log_result(result)

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


# Log

class Log:
    def info(message):
        print(message)

    def error(message):
        print("Error: %s" % message)

    def warning(message):
        print("Warning: %s" % warning)


def _log_result(result):
    violation_level, violation_type, (line_number, column), description = result

    message = "line %d, column %d <%s>" \
        % (line_number, column, description)

    if violation_level == ViolationLevel.Warning:
        Log.warning(message)
    else:
        Log.error(message)

# Command Line Options

def _show_help_info():
    Log.info("""
Usage:
    python3 dinodon.py [files] [options]
Options:
    --help: Display general or command-specific help
    --version: Display the current version of dinodon
    """)

def _show_version():
    Log.info(Version)

if __name__ == '__main__':
    lint_files = list(filter(lambda parm: "dinodon" not in parm and parm.endswith(".py"), sys.argv))
    options = list(filter(lambda parm: not parm.endswith(".py"), sys.argv))

    if len(options) > 0:
        is_linting = True

        # 1. self check
        if "--self-check" == options[0]:
            _check_physical_lines("dinodon.py")
            _check_logical_lines("dinodon.py")

        # 2. show help
        if "--help" == options[0]:
            _show_help_info()
            is_linting = False

        # 3. show version
        if "--version" == options[0]:
            _show_version()
            is_linting = False

    else:
        if len(lint_files) != 0:
            _check_physical_lines(lint_files[0])
            _check_logical_lines(lint_files[0])
        else:
            Log.error("no file to lint!")

