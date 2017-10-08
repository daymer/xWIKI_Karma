from PythonConfluenceAPI import ConfluenceAPI

import Configuration
import CustomModules.SQL_Connector
from Configuration import MySQLConfig, MediaWIKIConfig
from Migration_to_xWiki.Users_association import Users
from CustomModules import Mechanics
from CustomModules.Mechanics import XWikiClient, MysqlConnector, Migrator

target_pool = 'Migration pool'
parent = 'Migration pool'


MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
SQLConfig = Configuration.SQLConfig()
xWikiConfig = Configuration.xWikiConfig(target_pool)
xWikiClient = XWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
ConfluenceConfig_instance = Configuration.ConfluenceConfig()
confluenceAPI_instance = ConfluenceAPI(username=ConfluenceConfig_instance.USER, password=ConfluenceConfig_instance.PASS, uri_base=ConfluenceConfig_instance.ULR)
MediaWIKIConfig = MediaWIKIConfig()
Migrator = Migrator(ConfluenceConfig=ConfluenceConfig_instance, MediaWIKIConfig=MediaWIKIConfig, xWikiConfig=xWikiConfig)
UserList = Users()
SQLConnector_instance = CustomModules.SQL_Connector.SQLConnector(SQLConfig)

title = 'Hyper-V Basics'
platform = 'Confluence'
result = Mechanics.Migrate_page(title, platform, target_pool, parent, MySQLconfig_INSTANCE,
                                MysqlConnector_INSTANCE, SQLConfig, SQLConnector_instance, ConfluenceConfig_instance,
                                MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
print(result)
