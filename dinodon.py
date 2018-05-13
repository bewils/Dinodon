import re

# Regex types

Indent_Regex = re.compile('(\t+)')

# Levels

Level_Warning = 0
Level_Error = 1

# Types

Type_Has_Tab = 1
Type_Blank_Line_Whitespace = 2
Type_Trailing_Whitespace = 3
Type_Line_Too_Long = 4

#
# Check functions:
# Return type: (Type: int, 
#               Level: int {warning/error},
#               Line info: (int, int) {line number/offset},
#               Description: str)
#

def check_tabs(physical_line, line_number):
    """Test case:
    if True:\n\tb = 1\na = 2
    """
    match_obj = Indent_Regex.search(physical_line)
    if match_obj is not None:
        offset = match_obj.span()[0]
        return (Type_Has_Tab, Level_Error, (line_number, offset), "Indentation contains tabs")

def check_trailing_whitespace(physical_line, line_number):
    """Test case:
    if True: \nb = 1\na = 2\n    \n
    """
    whitespace_charset = " \t\v"
    real_line = physical_line.rstrip(whitespace_charset)
    if real_line != physical_line:
        if len(real_line) == 0:
            return (Type_Blank_Line_Whitespace, Level_Error, (line_number, 0), "Blank line contains whitespace")
        else:
            return (Type_Trailing_Whitespace, Level_Error, (line_number, len(real_line)), "Line with trailing whitespace")

def check_line_length(physical_line, line_number):
    """Test case:
    a = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    """
    length = len(physical_line)
    
    if length > 79:
        # Ignore long shebang line
        if line_number == 0 and physical_line.startswith('#!'):
            return

        real_line = physical_line.lstrip()
        # Ignore comments
        if real_line.startswith("#"):
            return
        
        return (Type_Line_Too_Long, Level_Error, (line_number, 0), "Line too long")


import sys
import dinodon_log as log

if __name__ == '__main__':
    lint_files = filter(lambda parm: "dinodon" not in parm and parm.endswith(".py"), sys.argv)

    if len(lint_files) == 0:
        log.error("no file to lint!")

    text = a = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    for line_number, line in  enumerate(text.split("\n")):
        print(check_line_length(line_number, line))