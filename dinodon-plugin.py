import re

IS_WITH_SINGLETON_REGEX = re.compile("(!=|==)\s*(True|False|None)")

def check_is_with_singleton(physical_line, line_number):
    match_obj = IS_WITH_SINGLETON_REGEX.search(physical_line)

    if match_obj is not None:
        offset = match_obj.span()[0]
        return (0, 12, (line_number, offset), "Use equal with singleton")

plugins = {
    "physical_line": [check_is_with_singleton],
    "logical_line": [],
    "ast": []
}