import Configuration
from  Users import Users
from Configuration import MySQLConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector


MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)

SQLConfig = Configuration.SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
xWikiConfig = Configuration.xWikiConfig('Migration pool')
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
UserList = Users()
PageTitle = 'VixDiskLibSample'
platform = 'MediaWIKI'

DataTuple = (
    ('space', 'Migration pool'),
    ('parent', 'Migration pool'),
    ('title', PageTitle),
    #('content', content),
    ('author', "XWiki.TestTest"),
    #('version', last_version),
    #('syntax', syntax),  # 'confluence/1.0' 'xwiki/2.1'
    ('test', False),
    ('only_update', False),
    ('last_run', True),
)

tags = []
result = xWikiClient.add_tag_to_page(dict(DataTuple)['space'], dict(DataTuple)['title'], tags, title=None, parent=None)
print(result)