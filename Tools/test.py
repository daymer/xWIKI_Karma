from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig, xWikiConfig, SQLConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator



MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)

SQLConfig = SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
ConfluenceConfig = ConfluenceConfig()
MediaWIKIConfig = MediaWIKIConfig()
xWikiConfig = xWikiConfig('Migration pool')
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
Migrator = Migrator(ConfluenceConfig=ConfluenceConfig, MediaWIKIConfig=MediaWIKIConfig, xWikiConfig=xWikiConfig)

PageTitle = 'Investigating error "The storage file was not verified."'
platform = 'Confluence'
page_id = SQLConnector.GetPageID_by_title_and_platform(PageTitle, platform)
Migrator.current_page_id = page_id
attachments = Migrator.make_and_attach(platform=platform, file_name='image2017-1-24 12:28:38.png', page=PageTitle, space='Migration pool')
