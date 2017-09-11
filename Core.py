from PythonConfluenceAPI import ConfluenceAPI
import Configuration
import pickle
from Mechanics import PageCreator, SQLConnector, ContributionComparator, CustomLogging, ExclusionsDict, MysqlConnector
global Contrib_Compare_inst


def initialize(logging_mode: str = 'silent'):
    global Contrib_Compare_inst
    # Main instance, used to analyze pages and create page contribution maps based on the content,
    # collected from one of supported platforms
    global Mysql_Connector_inst
    # Here used to connect to xWIKI DB to get a list of pages from a requested space
    global ConfluenceAPI_inst
    # ConfluenceAPI_inst - same for Confluence
    global SQL_Connector_inst
    # Used to store\load page contribution maps in\from SQL
    global Page_Creator_inst
    # Creates PAGE objects - data handlers for currently analyzed page
    global Logging
    # Just Logging
    Contrib_Compare_inst = ContributionComparator()
    SQL_Config_inst = Configuration.SQLConfig()
    Confluence_Config_inst = Configuration.ConfluenceConfig()
    MediaWIKI_Config_inst = Configuration.MediaWIKIConfig()
    xWiki_Config_inst = Configuration.xWikiConfig(['Migration pool', 'Sandbox', 'Main', 'StagingWiki'])
    MySQL_Config_inst = Configuration.MySQLConfig()
    Mysql_Connector_inst = MysqlConnector(MySQL_Config_inst)
    Page_Creator_inst = PageCreator(Confluence_Config_inst, MediaWIKI_Config_inst, xWiki_Config_inst)
    SQL_Connector_inst = SQLConnector(SQL_Config_inst)
    Logging = CustomLogging(logging_mode)
    # getting all pages in Confluence:
    ConfluenceAPI_inst = ConfluenceAPI(Confluence_Config_inst.USER, Confluence_Config_inst.PASS,
                                       Confluence_Config_inst.ULR)


initialize()

# Task:
#    Confluence: VB (Veeam B&R Basic knowledge), WB (Veeam Support Hints and Tricks), GZ (Ground Zero)
#    MediaWIKI: just all
#    xWIKI: ['Blog', 'Main', 'Sandbox', 'XWiki']
Task = {
    # 'VB': 'Confluence',
    # 'WB': 'Confluence',
    # 'GZ': 'Confluence',
    # 'ALL mWIKI': 'MediaWIKI'
    # 'Main': 'xWIKI',
    # 'Sandbox': 'xWIKI',
    # 'Migration pool': 'xWIKI',
    # 'Migrated bugs': 'xWIKI'
    'Main': 'xWIKI',
    'StagingWiki': 'xWIKI'
}
TaskExclusions = ExclusionsDict()
# TaskExclusions['Confluence'] = 'List of all KBs'
# TaskExclusions['MediaWIKI'] = 'Found Bugs'
# TaskExclusions['MediaWIKI'] = 'Registry values B&R'
# TaskExclusions['MediaWIKI'] = 'Veeam ONE Registry Keys'
# TaskExclusions['MediaWIKI'] = 'Patches and fixes for B&R'
# TaskExclusions['MediaWIKI'] = 'Bug%'
# TaskExclusions['MediaWIKI'] = 'BUG%'
# TaskExclusions['MediaWIKI'] = 'bug%'
# TaskExclusions['MediaWIKI'] = 'Case Handling'
# TaskExclusions['MediaWIKI'] = 'Team Members'
TaskExclusions['xWIKI'] = None
toAnalyze = []
TaskPages = {}
TotalSize = 0
for space, platform in Task.items():
    if platform == 'Confluence':
        respond = ConfluenceAPI_inst.get_content('page', space, None, 'current', None, None, 0, 500)
        size = respond['size']
        TotalSize += size
        print(size, 'Confluence pages were found in space', space)
        toAnalyze = respond['results']
        for page in toAnalyze:
            if TaskExclusions[platform] is not None:
                if not Page_Creator_inst.check_exclusions(page['title'], platform, TaskExclusions):
                    continue
                else:
                    TaskPages.update({page['title']: platform})
                    size += 1
            else:
                TaskPages.update({page['title']: platform})
                size += 1
    if platform == 'MediaWIKI':
        size = 0
        for page in Page_Creator_inst.MediaWikiAPI_instance.allpages():
            if TaskExclusions[platform] is not None:
                if not Page_Creator_inst.check_exclusions(page.name, platform, TaskExclusions):
                    # print(page.name, 'was excluded, total excluded:', Page_Creator_inst.TotalExcluded)
                    continue
                else:
                    TaskPages.update({page.name: platform})
                    size += 1
            else:
                TaskPages.update({page.name: platform})
                size += 1
        print(size, 'MediaWIKI pages were found in space', space)
        TotalSize += size
    if platform == 'xWIKI':
        size = 0
        print('Looking for pages in the following xWIKI space:', space)
        for page in Mysql_Connector_inst.get_XWD_FULLNAMEs(space):
            if TaskExclusions[platform] is not None:
                if not Page_Creator_inst.check_exclusions(page, platform, TaskExclusions):
                    continue
                else:
                    TaskPages.update({page: platform})
                    size += 1
            else:
                TaskPages.update({page: platform})
                size += 1
        print(size, 'xWIKI pages were found in space', space)
        TotalSize += size
Logging.log_task_start(TotalSize, Page_Creator_inst.TotalExcluded)

# startin main process
for title, platform in TaskPages.items():
    Logging.page_analysis_started(title)
    CurrentPage = Page_Creator_inst.create_new_page_by_title_and_platform(title, platform)
    if CurrentPage is None:
        Logging.skip_some_page(title)
        continue
    CurrentPage.page_id = Page_Creator_inst.collect_page_id(CurrentPage)
    if CurrentPage.page_id is None:
        Logging.skip_some_page(title)
        continue
    # incremental or full mode
    CurrentPage.dbVersion = SQL_Connector_inst.CheckExistencebyID(CurrentPage)
    CurrentPage.page_versions = Page_Creator_inst.collect_page_history(CurrentPage)
    CurrentPage.page_author = Page_Creator_inst.collect_page_author(CurrentPage)
    Logging.page_processing_started(CurrentPage)
    if CurrentPage.dbVersion == None:
        Logging.page_processing_target(CurrentPage)
        # getting sources for all versions
        for VersionNumber in range(1, CurrentPage.page_versions + 1):
            new_version = Page_Creator_inst.get_version_content_by_version(VersionNumber, CurrentPage)
            CurrentPage.add_new_page_version(new_version)
        # comparing all versions
        try:
            Contrib_Compare_inst.initial_compare(CurrentPage)
        except:
            print(CurrentPage.PageVersionsDict)
        CurrentPage.TOTALCharacters = len(CurrentPage.VersionsGlobalArray)
        for VersionNum in range(1, CurrentPage.page_versions + 1):
            # print(CurrentPage.contributors[VersionNum] +' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
            UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
            if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) == None:
                CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: len(UserXContribute)})
            else:
                NowInDict = CurrentPage.TotalContribute[CurrentPage.contributors[VersionNum]]
                CurrentPage.TotalContribute.update(
                    {CurrentPage.contributors[VersionNum]: NowInDict + len(UserXContribute)})
        # Showing stats, counting percents
        Logging.page_counting_finished(CurrentPage)
        Logging.page_summary(CurrentPage)
        # pushing new page to SQL
        CurrentPage.pageSQL_id = SQL_Connector_inst.PushNewPage(CurrentPage)
        SQL_Connector_inst.PushNewDatagram(CurrentPage)
        SQL_Connector_inst.PushContributionDatagramByID(CurrentPage)
        SQL_Connector_inst.PushContributionByUser(CurrentPage)
    elif CurrentPage.dbVersion < CurrentPage.page_versions:
        SQL_Connector_inst.UpdateKnownPagesLast_check(CurrentPage)
        # getting sources for all missing versions + latest in DB
        for VersionNumber in range(CurrentPage.dbVersion, CurrentPage.page_versions + 1):
            new_version = Page_Creator_inst.get_version_content_by_version(VersionNumber, CurrentPage)
            CurrentPage.add_new_page_version(new_version)
        Logging.page_processing_target(CurrentPage)
        # loading old datagram
        CurrentPage.pageSQL_id = SQL_Connector_inst.GetPageSQLID(CurrentPage)
        TempArray = SQL_Connector_inst.GetDatagrams(CurrentPage)
        CurrentPage.VersionsGlobalArray = pickle.loads(TempArray[0])
        TempContributors = pickle.loads(TempArray[1])
        # comparing latest versions
        Contrib_Compare_inst.incremental_compare(CurrentPage)
        CurrentPage.TOTALCharacters = len(CurrentPage.VersionsGlobalArray)
        for version, user in TempContributors.items():  # Warning! dict.update is used, which means that accidentally matching pairs version:user will be overwritten.
            CurrentPage.contributors.update({version: user})
        # recalculating contribution for all versions
        for VersionNum in range(1, CurrentPage.page_versions + 1):
            # print(CurrentPage.contributors[VersionNum] +' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
            UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
            if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) == None:
                CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: len(UserXContribute)})
            else:
                NowInDict = CurrentPage.TotalContribute[CurrentPage.contributors[VersionNum]]
                CurrentPage.TotalContribute.update(
                    {CurrentPage.contributors[VersionNum]: NowInDict + len(UserXContribute)})
        # Showing stats, counting percents
        Logging.page_counting_finished(CurrentPage)
        Logging.page_summary(CurrentPage)
        # pushing updates to SQL
        SQL_Connector_inst.UpdatePagebyID(CurrentPage)
        SQL_Connector_inst.UpdateDatagramByID(CurrentPage)
        SQL_Connector_inst.PushContributionDatagramByID(CurrentPage)
        SQL_Connector_inst.PushContributionByUser(CurrentPage)
    elif CurrentPage.dbVersion == CurrentPage.page_versions:
        SQL_Connector_inst.UpdateKnownPagesLast_check(CurrentPage)

Logging.log_task_ended()
