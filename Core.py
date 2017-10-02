from PythonConfluenceAPI import ConfluenceAPI
import Configuration
import pickle
from Mechanics import PageCreator, SQLConnector, ContributionComparator, ExclusionsDict, MysqlConnector
import logging
from datetime import datetime
GlobalStartTime = datetime.now()

def initialize(logging_mode: str = 'INFO', log_to_file: bool = True):
    ###################################################################################################################
    # Contrib_Compare_inst                                                                                            #
    # Main instance, used to analyze pages and create page contribution maps based on the content,                    #
    # collected from one of supported platforms                                                                       #
    # Mysql_Connector_inst                                                                                            #
    # Here used to connect to xWIKI DB to get a list of pages from a requested space                                  #
    # ConfluenceAPI_inst                                                                                              #
    # ConfluenceAPI_inst - same for Confluence                                                                        #
    # SQL_Connector_inst                                                                                              #
    # Used to store\load page contribution maps in\from SQL                                                           #
    # Page_Creator_inst                                                                                               #
    # Creates PAGE objects - data handlers for currently analyzed page                                                #
    ###################################################################################################################
    logger_inst = logging.getLogger()
    logger_inst.setLevel(logging_mode)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    if log_to_file is True:
        log_name = "Core_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S", )) + '.log'
        fh = logging.FileHandler(log_name)
        fh.setLevel(logging_mode)
        fh.setFormatter(formatter)
        logger_inst.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging_mode)
    ch.setFormatter(formatter)
    logger_inst.addHandler(ch)
    contrib_compare_inst = ContributionComparator()
    SQL_config_inst = Configuration.SQLConfig()
    confluence_config_inst = Configuration.ConfluenceConfig()
    MediaWIKI_Config_inst = Configuration.MediaWIKIConfig()
    xWiki_Config_inst = Configuration.xWikiConfig(['Migration pool', 'Sandbox', 'Main', 'StagingWiki'])
    MySQL_Config_inst = Configuration.MySQLConfig()
    Mysql_connector_inst = MysqlConnector(MySQL_Config_inst)
    Page_creator_inst = PageCreator(confluence_config_inst, MediaWIKI_Config_inst, xWiki_Config_inst)
    SQL_connector_inst = SQLConnector(SQL_config_inst)
    # getting all pages in Confluence:
    confluenceAPI_inst = ConfluenceAPI(confluence_config_inst.USER, confluence_config_inst.PASS,
                                       confluence_config_inst.ULR)
    return contrib_compare_inst, Mysql_connector_inst, confluenceAPI_inst, SQL_connector_inst, Page_creator_inst, logger_inst

Contrib_Compare_inst, Mysql_Connector_inst, ConfluenceAPI_inst, SQL_Connector_inst, Page_Creator_inst, Logger = initialize('INFO')
Logger.info('Initialization finished, job started at ' + str(GlobalStartTime))
# Task:
#    Confluence: VB (Veeam B&R Basic knowledge), WB (Veeam Support Hints and Tricks), GZ (Ground Zero)
#    MediaWIKI: just all
#    xWIKI: ['Blog', 'Main', 'Sandbox', 'XWiki']
Task = {
    # 'VB': 'Confluence',
    # 'WB': 'Confluence',
    # 'GZ': 'Confluence',
    'ALL mWIKI': 'MediaWIKI'
    # 'Main': 'xWIKI',
    # 'Sandbox': 'xWIKI',
    # 'Migration pool': 'xWIKI',
    # 'Migrated bugs': 'xWIKI'
    #'Main': 'xWIKI',
    #'StagingWiki': 'xWIKI'
}
TaskExclusions = ExclusionsDict()
TaskExclusions['Confluence'] = 'List of all KBs'
TaskExclusions['MediaWIKI'] = 'Found Bugs'
TaskExclusions['MediaWIKI'] = 'Registry values B&R'
TaskExclusions['MediaWIKI'] = 'Veeam ONE Registry Keys'
TaskExclusions['MediaWIKI'] = 'Patches and fixes for B&R'
# TaskExclusions['MediaWIKI'] = 'Bug%'
# TaskExclusions['MediaWIKI'] = 'BUG%'
# TaskExclusions['MediaWIKI'] = 'bug%'
TaskExclusions['MediaWIKI'] = 'Case Handling'
TaskExclusions['MediaWIKI'] = 'Team Members'
# TaskExclusions['xWIKI'] = 'Main.WebHome'
# TaskExclusions['xWIKI'] = 'StagingWiki.WebHome'
# TaskExclusions['xWIKI'] = 'StagingWiki.Personal Spaces%'


def build_task_array(task_dict: dict, task_exclusions_dict: dict, Logger):
    global task_pages_dict, platform
    task_pages_dict = {}
    total_size = 0
    for space, platform in task_dict.items():
        if platform == 'Confluence':
            respond = ConfluenceAPI_inst.get_content('page', space, None, 'current', None, None, 0, 500)
            size = respond['size']
            total_size += size
            Logger.info(str(size) + ' Confluence pages were found in space ' + space)
            try:
                confluence_pages_from_api = respond['results']
            except:
                Logger.error('Unable to get Confluence pages from API, aborting this space')
                continue
            for page in confluence_pages_from_api:
                if task_exclusions_dict[platform] is not None:
                    if not Page_Creator_inst.check_exclusions(page['title'], platform, task_exclusions_dict):
                        continue
                    else:
                        task_pages_dict.update({page['title']: platform})
                        size += 1
                else:
                    task_pages_dict.update({page['title']: platform})
                    size += 1
        if platform == 'MediaWIKI':
            size = 0
            for page in Page_Creator_inst.MediaWikiAPI_instance.allpages():
                if task_exclusions_dict[platform] is not None:
                    if not Page_Creator_inst.check_exclusions(page.name, platform, task_exclusions_dict):
                        Logger.debug(page.name + ' was excluded, total excluded: ' + str(Page_Creator_inst.TotalExcluded))
                        continue
                    else:
                        task_pages_dict.update({page.name: platform})
                        size += 1
                else:
                    task_pages_dict.update({page.name: platform})
                    size += 1
            Logger.info(str(size) + ' MediaWIKI pages were found in space "' + space + '"')
            total_size += size
        if platform == 'xWIKI':
            size = 0
            Logger.debug('Looking for pages in the following xWIKI space: "' + space + '"')
            for page in Mysql_Connector_inst.get_XWD_FULLNAMEs(space):
                if task_exclusions_dict[platform] is not None:
                    if not Page_Creator_inst.check_exclusions(page, platform, task_exclusions_dict):
                        Logger.debug(page + ' was excluded, total excluded: ' + str(Page_Creator_inst.TotalExcluded))
                        continue
                    else:
                        task_pages_dict.update({page: platform})
                        size += 1
                else:
                    task_pages_dict.update({page: platform})
                    size += 1
            Logger.info(str(size) + ' xWIKI pages were found in space "' + space + '"')
            total_size += size
    TaskStartTime = datetime.now()
    Logger.info(str(total_size) + ' pages were found in all spaces, excluded: ' + str(Page_Creator_inst.TotalExcluded))
    return task_pages_dict, TaskStartTime

task_pages_dict, TaskStartTime = build_task_array(task_dict=Task, task_exclusions_dict=TaskExclusions, Logger=Logger)

# starting main process
Logger.info('Starting main process...')
for title, platform in task_pages_dict.items():
    PageAnalysisStartTime = datetime.now()
    Logger.info(title + ' : Task initialized, getting sources...')
    CurrentPage = Page_Creator_inst.create_new_page_by_title_and_platform(title, platform)
    if CurrentPage is None:
        Logger.warning(title + ' is redirect or unable to find ID, skipping')
        continue
    CurrentPage.page_id = Page_Creator_inst.collect_page_id(CurrentPage)
    if CurrentPage.page_id is None:
        Logger.warning(title + ' is redirect or unable to find ID, skipping')
        continue
    # incremental or full mode
    CurrentPage.dbVersion = SQL_Connector_inst.CheckExistencebyID(CurrentPage)
    CurrentPage.page_versions = Page_Creator_inst.collect_page_history(CurrentPage)
    CurrentPage.page_author = Page_Creator_inst.collect_page_author(CurrentPage)

    if CurrentPage.dbVersion is None:
        Logger.info('"' + CurrentPage.page_title + '" will be processed in FULL mode')
        PageAnalysisEndTime = datetime.now()
        Logger.debug('Page "' + CurrentPage.page_title + '" with ID ' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found', '\n',
                  'Sources are collected, calculating difference... ')
        # getting sources for all versions
        for VersionNumber in range(1, CurrentPage.page_versions + 1):
            new_version = Page_Creator_inst.get_version_content_by_version(VersionNumber, CurrentPage)
            CurrentPage.add_new_page_version(new_version)
        # comparing all versions
        try:
            Contrib_Compare_inst.initial_compare(CurrentPage)
        except:
            Logger.critical('initial compare has failed on the following PageVersionsDict:')
            Logger.critical(CurrentPage.PageVersionsDict)
            exit(1)
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
        PageCountingEndTime = datetime.now()
        Logger.info(CurrentPage.page_title + ' was added to DB')
        Logger.debug('Characters in TOTAL: ' + str(CurrentPage.TOTALCharacters))
        if CurrentPage.TOTALCharacters != 0:
            for Contributor, Value in CurrentPage.TotalContribute.items():
                Percent = (Value / CurrentPage.TOTALCharacters) * 100
                Logger.debug('Contribution of ' + Contributor + ' = ' + str(Percent) + '%' + ' (' + str(
                    Value) + ') characters')
        Logger.info('Time elapsed: Analysis: ' + str(PageAnalysisEndTime - PageAnalysisStartTime) + ' + Diff calc: ' +
                    str(PageCountingEndTime - PageAnalysisEndTime) + ' = ' + str(
                        PageCountingEndTime - PageAnalysisStartTime))
        PageAnalysisStartTime = None
        PageAnalysisEndTime = None
        PageCountingEndTime = None
        # pushing new page to SQL
        CurrentPage.pageSQL_id = SQL_Connector_inst.PushNewPage(CurrentPage)
        SQL_Connector_inst.PushNewDatagram(CurrentPage)
        SQL_Connector_inst.PushContributionDatagramByID(CurrentPage)
        SQL_Connector_inst.PushContributionByUser(CurrentPage)
    elif CurrentPage.dbVersion < CurrentPage.page_versions:
        Logger.info('"' + CurrentPage.page_title + '" will be processed in INCREMENTAL mode')
        PageAnalysisEndTime = datetime.now()
        Logger.info('Page "' + CurrentPage.page_title + '" with ID ' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found ' +
                  'Sources are collected, calculating difference... ')
        SQL_Connector_inst.UpdateKnownPagesLast_check(CurrentPage)
        # getting sources for all missing versions + latest in DB
        for VersionNumber in range(CurrentPage.dbVersion, CurrentPage.page_versions + 1):
            new_version = Page_Creator_inst.get_version_content_by_version(VersionNumber, CurrentPage)
            CurrentPage.add_new_page_version(new_version)
        PageAnalysisEndTime = datetime.now()
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
        PageCountingEndTime = datetime.now()
        Logger.info('... Done')
        Logger.debug('Characters in TOTAL: ' + str(CurrentPage.TOTALCharacters))
        if CurrentPage.TOTALCharacters != 0:
            for Contributor, Value in CurrentPage.TotalContribute.items():
                Percent = (Value / CurrentPage.TOTALCharacters) * 100
                Logger.debug('Contribution of ' + Contributor + ' = ' + str(Percent) + '%' + ' (' + str(
                    Value) + ') characters')
        Logger.info('Time elapsed: Analysis: ' + str(PageAnalysisEndTime - PageAnalysisStartTime) + ' + Diff calc: ' +
                     str(PageCountingEndTime - PageAnalysisEndTime) + ' = ' + str(PageCountingEndTime - PageAnalysisStartTime))
        PageAnalysisStartTime = None
        PageAnalysisEndTime = None
        PageCountingEndTime = None
        # pushing updates to SQL
        SQL_Connector_inst.UpdatePagebyID(CurrentPage)
        SQL_Connector_inst.UpdateDatagramByID(CurrentPage)
        SQL_Connector_inst.PushContributionDatagramByID(CurrentPage)
        SQL_Connector_inst.PushContributionByUser(CurrentPage)
    elif CurrentPage.dbVersion == CurrentPage.page_versions:
        Logger.info('"' + CurrentPage.page_title + '" is up-to-date')
        PageAnalysisEndTime = datetime.now()
        SQL_Connector_inst.UpdateKnownPagesLast_check(CurrentPage)

TaskEndTime = datetime.now()
TotalElapsed = TaskEndTime - TaskStartTime
Logger.info('Task finished, total time wasted:' + str(TotalElapsed))
