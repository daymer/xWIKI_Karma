# coding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility

import re

regex = r"<component><name>(.[^<]*)</name></component>"

test_str = "<components><component><name>BackupToTape</name></component><component><name>BackupValidator</name></component><component><name>BoSS</name></component></components>"

matches = re.finditer(regex, test_str, re.IGNORECASE)
if matches:
    for match in matches:
        print(match.group(1))

exit()
for matchNum, match in enumerate(matches):
    matchNum = matchNum + 1

    print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
                                                                        end=match.end(), match=match.group()))

    for groupNum in range(0, len(match.groups())):
        groupNum = groupNum + 1

        print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum, start=match.start(groupNum),
                                                                        end=match.end(groupNum),
                                                                        group=match.group(groupNum)))

# Note: for Python 2.7 compatibility, use ur"" to prefix the regex and u"" to prefix the test string and substitution.
