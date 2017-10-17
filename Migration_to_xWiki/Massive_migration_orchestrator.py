import codecs
import sys
from datetime import datetime

from PythonConfluenceAPI import ConfluenceAPI

import Configuration
import CustomModules.SQL_Connector
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Migration_to_xWiki.Users_association import Users
from CustomModules import Mechanics
from CustomModules.Mechanics import XWikiClient, MysqlConnector, Migrator

log_name = "Migration_log_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S", )) + '.txt'

target_pool = 'Delta migration'
parent = 'Delta migration'
migrate_statement = None
migrate_statement = "select page_title, platform from [dbo].[KnownPages] where page_title = 'SNMP tutorial and troubleshooting' and platform = 'confluence'"
title_like = None
#title_like = 'bug%'


log_statement = 'Task started, migrate_statement=', str(migrate_statement), 'title_like=', str(title_like)
with codecs.open(log_name, "w", "utf-8") as stream:   # or utf-8
    stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
print(*log_statement, sep=' ')

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
TaskPages_list = SQLConnector_instance.select_page_titles_platforms_by_filter(page_title=title_like, query=migrate_statement)
Total_pages_to_process = str(len(TaskPages_list))
task_pages_dict = {}

log_statement = 'Found pages:', Total_pages_to_process
print(*log_statement, sep=' ')
print(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S",)) + str(log_statement))
for entry in TaskPages_list:
    task_pages_dict.update({entry[0]: entry[1]})
counter = 0
for title, platform in task_pages_dict.items():
        try:
            result = Mechanics.Migrate_page(title, platform, target_pool, parent, MySQLconfig_INSTANCE, MysqlConnector_INSTANCE, SQLConfig, SQLConnector_instance, ConfluenceConfig, MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
            if result[0] is True:
                counter += 1
                log_statement = result[1], 'migrated in total:', str(counter) + '/' + Total_pages_to_process
                print(*log_statement, sep=' ')
                with codecs.open(log_name, "a", "utf-8") as stream:  # or utf-8
                    stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
            else:
                counter += 1
                log_statement = result[1], 'migrated in total:', str(counter) + '/' + Total_pages_to_process
                print(*log_statement, sep=' ')
                with codecs.open(log_name, "a", "utf-8") as stream:  # or utf-8
                    stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
        except Exception as exception:
            log_statement = 'ERROR: Failed on page:', title, 'from', platform, 'with error:'
            print(exception)
            print(*log_statement, sep=' ')
            with codecs.open(log_name, "a", "utf-8") as stream:  # or utf-8
                stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
            log_statement = sys.exc_info()[0]
            print(log_statement)
            with codecs.open(log_name, "a", "utf-8") as stream:  # or utf-8
                stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
