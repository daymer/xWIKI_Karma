from Users import Users
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Mechanics import xWikiClient, MysqlConnector, Migrator
import Mechanics
from PythonConfluenceAPI import ConfluenceAPI
import Configuration
from Mechanics import SQLConnector
import re
import requests


target_pool = 'Migrated Bugs'
parent = 'Migrated Bugs'


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

title = 'Bug 49790 - "Next run" field in EM doesn\'t match corresponding field in B&R console if the time offset from UTC isn\'t multiple of hour (e.g. UTC +05:30, UTC +09:30).'
platform = 'MediaWIKI'
result = Mechanics.Migrate_dat_bitch(title, platform, target_pool, parent, MySQLconfig_INSTANCE,
                                     MysqlConnector_INSTANCE, SQLConfig, SQLConnector_instance, ConfluenceConfig_instance,
                                     MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
print(result)
