import re

Indent_Regex = re.compile('(\t*)')

def check_tabs(physical_line):
    indent = Indent_Regex.match(physical_line).group(1)
    print(indent)

import sys
import dinodon_log as log

if __name__ == '__main__':
    lint_files = filter(lambda parm: "dinodon" not in parm and parm.endswith(".py"), sys.argv)

    if len(lint_files) == 0:
        log.error("no file to lint!")