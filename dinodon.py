import re

# Regex types

Indent_Regex = re.compile('(\t+)')
Extraneous_Whitespace_Regex = re.compile('[\[({] | [\]});:]')

# Levels

Level_Warning = 0
Level_Error = 1

# Types

Type_Has_Tab = 1
Type_Blank_Line_Whitespace = 2
Type_Trailing_Whitespace = 3
Type_Line_Too_Long = 4
Type_Extraneous_Whitespace = 5

#
# Check functions:
# Return type: tuple : (Type: int, 
#               Level: int {warning/error},
#               Line info: (int, int) {line number/offset},
#               Description: str)
#

# Check physical lines

def check_tabs(physical_line, line_number):
    # Test case:
    # if True:\n\tb = 1\na = 2

    match_obj = Indent_Regex.search(physical_line)
    if match_obj is not None:
        offset = match_obj.span()[0]
        return (Type_Has_Tab, Level_Error, (line_number, offset),
            "Indentation contains tabs")


def check_trailing_whitespace(physical_line, line_number):
    # Test case:
    # if True: \nb = 1\na = 2\n    \n

    whitespace_charset = " \t\v"
    real_line = physical_line.rstrip(whitespace_charset)
    if real_line != physical_line:
        if len(real_line) == 0:
            return (Type_Blank_Line_Whitespace, Level_Error, (line_number, 0),
                "Blank line contains whitespace")
        else:
            return (Type_Trailing_Whitespace, Level_Error, (line_number, len(real_line)),
                "Line with trailing whitespace")


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
        
        return (Type_Line_Too_Long, Level_Error, (line_number, 0), "Line too long")


def check_extraneous_whitespace(physical_line, line_number):
    # Test case:
    # spam( ham[1], {eggs: 2})
    
    # Ignore comment
    if physical_line.strip().startswith("#"):
        return

    for match_obj in Extraneous_Whitespace_Regex.finditer(physical_line):
        text = match_obj.group()
        # [({\s
        if text.endswith(" "):
            offset = match_obj.span()[0]
            char = text[0]
            return (Type_Extraneous_Whitespace, Level_Error, (line_number, offset), 
                "Whitespace after %s" % char)
        # \s])}:; 
        else:
            offset = match_obj.span()[1] - 1
            char = text[-1]
            return (Type_Extraneous_Whitespace, Level_Error, (line_number, offset), 
                "Whitespace before %s" % char)


# Check logical lines

def check_blank_line():

    return

# Check AST

# All checks

All_Checks = {
    "physical_line": [
        check_tabs,
        check_trailing_whitespace,
        check_line_length,
        check_extraneous_whitespace],
    "logical_line": [],
    "ast": []
}

import sys
import copy
import dinodon_log as log

def _check_physical_lines(lint_file):
    with open(lint_file, 'r') as f:
        current_checks = copy.deepcopy(All_Checks["physical_line"])
        for (line_number, line) in enumerate(f.readlines()):
            real_line = line.strip()
            # config custom lint
            if real_line.startswith("# dinodon:"):
                real_line = real_line[10:]
                if real_line.startswith("disable"):
                    function_names = real_line.split(" ")[1:]
                    remove_functions = filter(lambda func: func.__name__ in function_names, \
                        All_Checks["physical_line"])
                    current_checks = list(set(current_checks) - set(remove_functions))
                if real_line.startswith("enable"):
                    function_names = real_line.split(" ")[1:]
                    add_functions = filter(lambda func: func.__name__ in function_names, \
                        All_Checks["physical_line"])
                    current_checks = list(set(current_checks) | set(add_functions))

            for check in current_checks:
                result = check(line, line_number + 1)
                if result is not None:
                    print(result)

if __name__ == '__main__':
    # lint_files = list(filter(lambda parm: "dinodon" not in parm and parm.endswith(".py"), sys.argv))
    lint_files = list(filter(lambda parm: parm.endswith(".py"), sys.argv))

    if len(lint_files) == 0:
        log.error("no file to lint!")

    # dinodon:disable check_line_length
    a = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    # dinodon:enable check_line_length
    b = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    _check_physical_lines(lint_files[0])