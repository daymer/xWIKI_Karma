from Users import Users
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Mechanics import xWikiClient, MysqlConnector, Migrator
import Mechanics
from PythonConfluenceAPI import ConfluenceAPI
import Configuration
from Mechanics import SQLConnector
import re
import requests
import sys

target_pool = 'Migrated Bugs'
parent = 'Migrated Bugs'
migrate_statement = None
title_like = 'bug%'

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
TaskPages_list = SQLConnector_instance.GetPagesByTitle(page_title=title_like, query=migrate_statement)
Total_pages_to_process = str(len(TaskPages_list))
TaskPages = {}
print('Found pages:', Total_pages_to_process)
for entry in TaskPages_list:
    TaskPages.update({entry[0]: entry[1]})
counter = 0
for title, platform in TaskPages.items():
    if bool(re.match('bug', title, re.I)):
        try:
            result = Mechanics.Migrate_dat_bitch(title, platform, target_pool, parent, MySQLconfig_INSTANCE, MysqlConnector_INSTANCE, SQLConfig, SQLConnector_instance, ConfluenceConfig, MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
            if result[0] is True:
                counter += 1
                print(result[1], 'migrated in total:', str(counter) + '/' + Total_pages_to_process)
            else:
                print(result[1], 'migrated in total:', str(counter) + '/' + Total_pages_to_process)
        except:
            print('ERROR: Failed on page:', title, 'from', platform, 'with error:')
            print(sys.exc_info()[0])
    else:
        print(title, 'skipped')
