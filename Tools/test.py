import re

def re_info_for_bug_page(page_content: str):
    bug_id = None
    product = None
    tbfi = None
    components = None
    regex = r"\*\*Bug ID:\*\* (.*)"
    matches = re.search(regex, page_content)
    if matches:
        bug_id = matches.group(1)
    regex = r"\*\*Product:\*\* (.*)"
    matches = re.search(regex, page_content)
    if matches:
        product = matches.group(1)
    regex = r"\*\*To be fixed in:\*\* (.*)"
    matches = re.search(regex, page_content)
    if matches:
        tbfi = matches.group(1)
    regex = r"\*\*Components:\*\* (.*)"
    matches = re.search(regex, page_content)
    if matches:
        components = matches.group(1)
    print(bug_id, product, tbfi, components)
    return bug_id, product, tbfi, components

