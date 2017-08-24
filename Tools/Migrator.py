import Configuration
from  Users import Users
from Configuration import MySQLConfig, ConfluenceConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator


MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)

SQLConfig = Configuration.SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
ConfluenceConfig = ConfluenceConfig()
Migrator = Migrator(ConfluenceConfig)
xWikiConfig = Configuration.xWikiConfig('Migration pool')
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
UserList = Users()
PageTitle = 'Bug 102730 - Object reference not set to an instance of an object, tape medium not found'
platform = 'MediaWIKI'
SQLQuery = SQLConnector.GetDatagramsByPageTitleandPlatform(PageTitle, platform)
datagram = SQLQuery[0]
contributors_datagram = SQLQuery[1]

UniqueUsers = set(contributors_datagram.values())
# print(UniqueUsers)
# print(contributors_datagram)

for idx, user in enumerate(UniqueUsers):
    for version, author in contributors_datagram.items():
        if author == user:
            for symbol in datagram:
                if symbol[1] == version:
                    symbol[1] = idx
global_counter_of_symbols = 0
version = 0
latest_text = None
last_version = None
for idx, author in enumerate(UniqueUsers):
    version +=1
    text = ''
    counter_of_symbols = 0
    for symbol in datagram:
        if symbol[1] <= idx:
            text += symbol[0]
            if symbol[1] == idx:
                counter_of_symbols += 1
    global_counter_of_symbols += counter_of_symbols
    print(author, 'with id:', idx, 'has contributed:',counter_of_symbols)
    if counter_of_symbols == 0:
        version -= 1
        continue
    author = UserList.users[author]
    if author is None:
        author = "XWiki.root"
    if platform == 'Confluence':
        syntax = 'confluence+xhtml/1.0'
    elif platform == 'MediaWIKI':
        syntax = 'mediawiki/1.6'
    else:
        syntax = 'xwiki/2.1'
    DataTuple = (
        ('space', 'Migration pool'),
        ('parent', 'Migration pool'),
        ('title', PageTitle),
        ('content', text),
        ('author', author),
        ('version', version),
        ('syntax', syntax),  # 'confluence/1.0' 'xwiki/2.1' 'MediaWiki/1.6'
        ('test', False),
        ('only_update', False),
        ('last_run', False),
    )
    MysqlConnector_INSTANCE.add_new_version(*DataTuple)
    latest_text = text
    last_version = version +1

if latest_text is not None and last_version is not None:
    content = latest_text + ' '
    DataTuple = (
            ('space', 'Migration pool'),
            ('parent', 'Migration pool'),
            ('title', PageTitle),
            ('content', content),
            ('author', "XWiki.TestTest"),
            ('version', last_version),
            ('syntax', syntax),  # 'confluence/1.0' 'xwiki/2.1' 'MediaWiki/1.6'
            ('test', False),
            ('only_update', False),
            ('last_run', True),
        )
    MysqlConnector_INSTANCE.add_new_version(*DataTuple)
    tags = False
    if platform == 'Confluence':
        page_id = SQLConnector.GetPageID_by_title_and_platform(PageTitle, platform)
        tags = Migrator.get_tags(platform=platform, id=page_id, test_str=None)
    elif platform == 'MediaWIKI':
        tags = Migrator.get_tags(platform=platform, id=None, test_str=latest_text)
    if PageTitle.startswith('Bug') or PageTitle.startswith('bug') or PageTitle.startswith('BUG'):
        tags.append('bug')
    if tags is not False:
        result = xWikiClient.add_tag_to_page(dict(DataTuple)['space'], dict(DataTuple)['title'], tags, title=None, parent=None)
        print(result, len(tags), 'tags:', tags)
    else:
        print('No tags were found')