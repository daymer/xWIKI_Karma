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
from datetime import datetime
import codecs

target_pool = 'Migration pool'
parent = 'Migration pool'
migrate_statement = "SELECT page_title, platform FROM [Karma].[dbo].[KnownPages] where page_title not like LOWER('%bug%') and platform != 'xWiki'"
title_like = None


log_statement = 'Task started, migrate_statement=', str(migrate_statement), 'title_like=', str(title_like)
with codecs.open("Migration_log.txt", "w", "utf-8") as stream:   # or utf-8
    stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
print(*log_statement, sep=' ')

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

log_statement = 'Found pages:', Total_pages_to_process
print(*log_statement, sep=' ')
print(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S",))+ str(log_statement))
for entry in TaskPages_list:
    TaskPages.update({entry[0]: entry[1]})
counter = 0
for title, platform in TaskPages.items():
        if title == 'Veeam BandR releases':
            continue
        try:
            result = Mechanics.Migrate_dat_bitch(title, platform, target_pool, parent, MySQLconfig_INSTANCE, MysqlConnector_INSTANCE, SQLConfig, SQLConnector_instance, ConfluenceConfig, MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
            if result[0] is True:
                counter += 1
                log_statement = result[1], 'migrated in total:', str(counter) + '/' + Total_pages_to_process
                print(*log_statement, sep=' ')
                with codecs.open("Migration_log.txt", "a", "utf-8") as stream:  # or utf-8
                    stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
            else:
                log_statement = result[1], 'migrated in total:', str(counter) + '/' + Total_pages_to_process
                print(*log_statement, sep=' ')
                with codecs.open("Migration_log.txt", "a", "utf-8") as stream:  # or utf-8
                    stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
        except:
            log_statement = 'ERROR: Failed on page:', title, 'from', platform, 'with error:'
            print(*log_statement, sep=' ')
            with codecs.open("Migration_log.txt", "a", "utf-8") as stream:  # or utf-8
                stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
            log_statement = sys.exc_info()[0]
            print(log_statement)
            with codecs.open("Migration_log.txt", "a", "utf-8") as stream:  # or utf-8
                stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
