from Users import Users
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator
import Mechanics
from PythonConfluenceAPI import ConfluenceAPI
import Configuration
from Mechanics import PageCreator, SQLConnector, ContribBuilder, CustomLogging, ExclusionsDict
import requests
target_pool = 'Migrated Bugs'
parent = 'Migrated Bugs'

#------------------------- from Core.py
ConfluenceConfig = Configuration.ConfluenceConfig()
ContribBuilder = ContribBuilder()
SQLConfig = Configuration.SQLConfig()
xWikiConfig = Configuration.xWikiConfig()
MediaWIKIConfig = MediaWIKIConfig()
PAGE_CREATOR = PageCreator(ConfluenceConfig, MediaWIKIConfig, xWikiConfig)
SQLConnector = SQLConnector(SQLConfig)
CustomLogging = CustomLogging('silent')
#getting all pages in Confluence:
confluenceAPI = ConfluenceAPI(ConfluenceConfig.USER, ConfluenceConfig.PASS, ConfluenceConfig.ULR)


#------------------------- from Core_migration.py
MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
SQLConfig = Configuration.SQLConfig()
xWikiConfig = Configuration.xWikiConfig(target_pool)
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
Migrator = Migrator(ConfluenceConfig=ConfluenceConfig, MediaWIKIConfig=MediaWIKIConfig, xWikiConfig=xWikiConfig)
UserList = Users()

title = 'Bug 103397 - Veeam Agent for Windows Integration with B&R console gives incorrect end time for sessions. BEM shows broken throughput.'
platform = 'MediaWIKI'
result = Mechanics.Migrate_dat_bitch(title, platform, target_pool, parent, MySQLconfig_INSTANCE,
                                     MysqlConnector_INSTANCE, SQLConfig, SQLConnector, ConfluenceConfig,
                                     MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
print(result)

'''
try:
    result = Mechanics.Migrate_dat_bitch(title, platform, target_pool, parent, MySQLconfig_INSTANCE,
                                         MysqlConnector_INSTANCE, SQLConfig, SQLConnector, ConfluenceConfig,
                                         MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
    print(result)

except requests.exceptions.HTTPError as error:
    print(error)
'''