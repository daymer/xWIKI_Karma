import traceback
import Configuration
from Mechanics import PageCreator, SQLConnector, ContribBuilder, CustomLogging, ExclusionsDict, xWikiClient
SQLConfig = Configuration.SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
xWikiConfig = Configuration.xWikiConfig('Migration pool')
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)

PageTitle = 'OS typical builds and versions'
platform = 'xWIKI'
SQLQuery = SQLConnector.GetDatagramsByPageTitleandPlatform(PageTitle,platform)
datagram = SQLQuery[0]
contributors_datagram = SQLQuery[1]

print(datagram)
text = ''
for counter in range(1,len(contributors_datagram)+1):
    for letter in datagram:
        if letter[1] == counter:
            text += letter[0]
    print('Contribute of user ' +str(counter) + ':')
    print(text)
    text = ''

exit()
UniqueUsers = set(contributors_datagram.values())
for version, author in contributors_datagram.items():
    print(version, author)
    text = ''
    for symbol in datagram:
        if symbol[1] <= version:
            text += symbol[0]
    xWikiClient.submit_page('Migration pool', PageTitle, text, PageTitle, 'Migration pool')
    if version == 3:
        exit()
   #print(text)

