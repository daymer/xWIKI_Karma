import codecs
import sys
from datetime import datetime

from PythonConfluenceAPI import ConfluenceAPI

import Configuration
import Mechanics
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Mechanics import xWikiClient, MysqlConnector, Migrator
from Migration_to_xWiki.Users_association import Users

log_name = "Migration_log_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S", )) + '.txt'

target_pool = 'Delta bugs'
parent = 'Delta bugs'
migrate_statement = None
migrate_statement = "select page_title, platform from [dbo].[KnownPages] where last_modified > '2017-10-01'  and page_title like LOWER('bug%')"
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
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
ConfluenceConfig_instance = Configuration.ConfluenceConfig()
confluenceAPI_instance = ConfluenceAPI(username=ConfluenceConfig_instance.USER, password=ConfluenceConfig_instance.PASS, uri_base=ConfluenceConfig_instance.ULR)
MediaWIKIConfig = MediaWIKIConfig()
Migrator = Migrator(ConfluenceConfig=ConfluenceConfig_instance, MediaWIKIConfig=MediaWIKIConfig, xWikiConfig=xWikiConfig)
UserList = Users()
SQLConnector_instance = Mechanics.SQLConnector(SQLConfig)
TaskPages_list = SQLConnector_instance.GetPagesByTitle(page_title=title_like, query=migrate_statement)
Total_pages_to_process = str(len(TaskPages_list))
task_pages_dict = {}

log_statement = 'Found pages:', Total_pages_to_process
print(*log_statement, sep=' ')
print(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S",))+ str(log_statement))
for entry in TaskPages_list:
    task_pages_dict.update({entry[0]: entry[1]})
counter = 0
for title, platform in task_pages_dict.items():
        if title == 'Veeam B&R releases':
            continue
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
        except:
            log_statement = 'ERROR: Failed on page:', title, 'from', platform, 'with error:'
            print(*log_statement, sep=' ')
            with codecs.open(log_name, "a", "utf-8") as stream:  # or utf-8
                stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
            log_statement = sys.exc_info()[0]
            print(log_statement)
            with codecs.open(log_name, "a", "utf-8") as stream:  # or utf-8
                stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")
