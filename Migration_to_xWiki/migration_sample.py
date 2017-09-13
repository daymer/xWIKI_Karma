from PythonConfluenceAPI import ConfluenceAPI

import Configuration
import Mechanics
from Configuration import MySQLConfig, MediaWIKIConfig
from Mechanics import xWikiClient, MysqlConnector, Migrator
from Migration_to_xWiki.Users_association import Users

target_pool = 'Migration pool'
parent = 'Migration pool'


MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
SQLConfig = Configuration.SQLConfig()
xWikiConfig = Configuration.xWikiConfig(target_pool)
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
ConfluenceConfig_instance = Configuration.ConfluenceConfig()
confluenceAPI_instance = ConfluenceAPI(username=ConfluenceConfig_instance.USER, password=ConfluenceConfig_instance.PASS, uri_base=ConfluenceConfig_instance.ULR)
MediaWIKIConfig = MediaWIKIConfig()
Migrator = Migrator(ConfluenceConfig=ConfluenceConfig_instance, MediaWIKIConfig=MediaWIKIConfig, xWikiConfig=xWikiConfig)
UserList = Users()
SQLConnector_instance = Mechanics.SQLConnector(SQLConfig)

title = 'Hyper-V Basics'
platform = 'Confluence'
result = Mechanics.Migrate_dat_bitch(title, platform, target_pool, parent, MySQLconfig_INSTANCE,
                                     MysqlConnector_INSTANCE, SQLConfig, SQLConnector_instance, ConfluenceConfig_instance,
                                     MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
print(result)
