from Users import Users
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator
import Mechanics
from PythonConfluenceAPI import ConfluenceAPI
import Configuration
from Mechanics import PageCreator, SQLConnector, ContribBuilder, CustomLogging, ExclusionsDict
import re
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


# Task:
#    Confluence: VB (Veeam B&R Basic knowledge), WB (Veeam Support Hints and Tricks), GZ (Ground Zero)
#    MediaWIKI: just all
#    xWIKI: ['Blog', 'Main', 'Sandbox', 'XWiki']
Task = {
    #'VB': 'Confluence',
    #'WB': 'Confluence',
    #'GZ': 'Confluence',
    'ALL mWIKI': 'MediaWIKI'
    #'Main': 'xWIKI',
    #'Sandbox': 'xWIKI',
    #'Migration pool': 'xWIKI'
}
TaskExclusions = ExclusionsDict()
TaskExclusions['Confluence'] = 'List of all KBs'
TaskExclusions['MediaWIKI'] = 'Found Bugs'
TaskExclusions['MediaWIKI'] = 'Registry values B&R'
TaskExclusions['MediaWIKI'] = 'Veeam ONE Registry Keys'
TaskExclusions['MediaWIKI'] = 'Patches and fixes for B&R'
#TaskExclusions['MediaWIKI'] = 'Bug%'
#TaskExclusions['MediaWIKI'] = 'BUG%'
#TaskExclusions['MediaWIKI'] = 'bug%'
TaskExclusions['MediaWIKI'] = 'Case Handling'
TaskExclusions['MediaWIKI'] = 'Team Members'
TaskExclusions['xWIKI'] = None
toAnalyze = []
TaskPages = {}
TotalSize = 0
for space, platform in Task.items():
    if platform =='Confluence':
        respond = confluenceAPI.get_content('page', space, None, 'current', None, None, 0, 500)
        size = respond['size']
        TotalSize += size
        print(size, 'Confluence pages were found in space', space)
        toAnalyze = respond['results']
        for page in toAnalyze:
            if TaskExclusions[platform] is not None:
                if not PAGE_CREATOR.check_exclusions(page['title'], platform, TaskExclusions):
                    continue
                else:
                    TaskPages.update({page['title']: platform})
                    size += 1
            else:
                TaskPages.update({page['title']: platform})
                size += 1
    if platform =='MediaWIKI':
        size = 0
        for page in PAGE_CREATOR.MediaWikiAPI.allpages():
            if TaskExclusions[platform] is not None:
                if not PAGE_CREATOR.check_exclusions(page.name, platform, TaskExclusions):
                    #print(page.name, 'was excluded, total excluded:', PAGE_CREATOR.TotalExcluded)
                    continue
                else:
                    TaskPages.update({page.name: platform})
                    size += 1
            else:
                TaskPages.update({page.name: platform})
                size += 1
        #print(size, 'MediaWIKI pages were found in space', space)
        TotalSize += size
    if platform == 'xWIKI':
        size = 0
        for page in PAGE_CREATOR.xWikiAPI.page_names(space):
            if TaskExclusions[platform] is not None:
                if not PAGE_CREATOR.check_exclusions(page, platform, TaskExclusions):
                    continue
                else:
                    TaskPages.update({page: platform})
                    size += 1
            else:
                TaskPages.update({page: platform})
                size += 1
        print(size, 'xWIKI pages were found in space', space)
        TotalSize += size
CustomLogging.log_task_start(TotalSize, PAGE_CREATOR.TotalExcluded)

#startin main process
counter = 0
for title, platform in TaskPages.items():
    if bool(re.match('bug', title, re.I)):
        try:
            result = Mechanics.Migrate_dat_bitch(title, platform, target_pool, parent, MySQLconfig_INSTANCE, MysqlConnector_INSTANCE, SQLConfig, SQLConnector, ConfluenceConfig, MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)
            counter += 1
            print(result, 'migrated in total:', counter)
        except requests.exceptions.HTTPError as error:
            print('ERROR: Failed on page:', title, 'from', platform, 'with error:')
            print(error)
        except:
            print('ERROR: Failed on page:', title, 'from', platform, 'with error:')
            print('other error')
    else:
        print(title, 'skipped')
