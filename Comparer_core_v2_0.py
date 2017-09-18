from PythonConfluenceAPI import ConfluenceAPI
import Configuration
import pickle
from Mechanics import SQLConnector, ContributionComparator, MysqlConnector, PageCreator, xWikiClient
from Page_mechanics import PageXWiki
import logging
from datetime import datetime
import argparse
import os


GlobalStartTime = datetime.now()

log_level = None
task_pages_dict = None
log_to_file = None

##############################################################
#                      Test variables                        #
UseTestVarsSwitch = False
TestVars = {
    'log_level': 'INFO',
    'log_to_file': False,
    'task_pages_dict': {'Sandbox.Pages.test.WebHome': 'xWIKI'}
}
#                                                            #
##############################################################

if UseTestVarsSwitch is True:
    log_level = TestVars['log_level']
    log_to_file = TestVars['log_to_file']
    task_pages_dict = TestVars['task_pages_dict']
else:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_level", type=str)
    parser.add_argument("log_to_file", type=str)
    parser.add_argument("-t", "--title", type=str)
    parser.add_argument("-p", "--platform", type=str)
    parser.add_argument("-b", "--binary_dict_id", type=str)
    args = parser.parse_args()
    log_level = args.log_level
    log_to_file = bool(eval(args.log_to_file))
    if args.title and args.platform:
        task_pages_dict = {args.title: args.platform}
    elif args.binary_dict_id:
        str_environ = os.environ[args.binary_dict_id]
        task_pages_dict = pickle.loads(str_environ.encode('latin1'))
if log_level is None or task_pages_dict is None or log_to_file is None:
    exit(1)


def initialize(logging_mode: str = 'INFO', log_to_file_var: bool = False):
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
    if log_to_file_var is True:
        log_name = "Core_v2.0_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S", )) + '.log'
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
    xwikiclient_inst = xWikiClient(xWiki_Config_inst.api_root, xWiki_Config_inst.auth_user,
                                   xWiki_Config_inst.auth_pass)
    return contrib_compare_inst, Mysql_connector_inst, confluenceAPI_inst, SQL_connector_inst, Page_creator_inst, logger_inst, xwikiclient_inst

Contrib_Compare_inst, Mysql_Connector_inst, ConfluenceAPI_inst, SQL_Connector_inst, Page_Creator_inst, Logger, xWikiClient_inst = initialize(logging_mode=log_level, log_to_file_var=log_to_file)
Logger.info('Initialization finished, job started at ' + str(GlobalStartTime))

TaskStartTime = datetime.now()
for title, platform in task_pages_dict.items():
    # Creating new page instance. Practically, page inst is everything what we need to get page index
    PageAnalysisStartTime = datetime.now()
    Logger.info(title + ': Task initialized.')
    if platform.lower() == 'xwiki':
        # title is not a valid term in case of xWIki. Pages there have 2 separate options:
        # page (used in api path) and title (unused).
        # So, first we have to find it's name to make sure that the provided page exists
        real_title = Mysql_Connector_inst.get_XWD_TITLE(title)
        if real_title is None:
            Logger.error('Unable to find title of page "' + title + '". Skipping.')
            continue
        CurrentPage = PageXWiki(page=title, page_title=real_title, xWikiClient_inst=xWikiClient_inst)
        if CurrentPage is None:
            Logger.error('Unable to initialize PageXWiki instance "' + title + '". Skipping.')
            continue
        if CurrentPage.page_id is None:
            Logger.warning(title + ' is redirect or unable to find ID, skipping')
            continue
    # incremental or full mode
    CurrentPage.dbVersion = SQL_Connector_inst.CheckExistencebyID(CurrentPage)

    #FULL MODE:
    if CurrentPage.dbVersion is None:
        Logger.info('"' + CurrentPage.page_title + '" will be processed in FULL mode')
        PageAnalysisEndTime = datetime.now()
        Logger.debug('Page "' + CurrentPage.page_title + '" with ID ' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found')
        Logger.debug('Collecting sources and calculating difference... ')
        # getting sources for all versions
        for VersionNumber in range(1, CurrentPage.page_versions + 1):
            CurrentPage.add_new_page_version(CurrentPage.get_version_content_by_version(VersionNumber))
        # comparing all versions
        try:
            Contrib_Compare_inst.initial_compare(CurrentPage)
        except:
            print(CurrentPage.PageVersionsDict)
            exit()
        CurrentPage.TotalCharacters = len(CurrentPage.VersionsGlobalArray)
        for VersionNum in range(1, CurrentPage.page_versions + 1):
            UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
            # print(CurrentPage.contributors[VersionNum] + ' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
            if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) == None:
                CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: len(UserXContribute)})
            else:
                NowInDict = CurrentPage.TotalContribute[CurrentPage.contributors[VersionNum]]
                CurrentPage.TotalContribute.update(
                    {CurrentPage.contributors[VersionNum]: NowInDict + len(UserXContribute)})
        # Showing stats, counting percents
        PageCountingEndTime = datetime.now()
        Logger.debug('... Done')
        Logger.debug('Characters in TOTAL: ' + str(CurrentPage.TotalCharacters))
        if CurrentPage.TotalCharacters != 0:
            for Contributor, Value in CurrentPage.TotalContribute.items():
                Percent = (Value / CurrentPage.TotalCharacters) * 100
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
        Logger.info(CurrentPage.page_title + ' was added to DB')
        SQL_Connector_inst.PushNewDatagram(CurrentPage)
        SQL_Connector_inst.PushContributionDatagramByID(CurrentPage)
        SQL_Connector_inst.PushContributionByUser(CurrentPage)
    elif CurrentPage.dbVersion < CurrentPage.page_versions:
        Logger.info('"' + CurrentPage.page_title + '" will be processed in INCREMENTAL mode')
        PageAnalysisEndTime = datetime.now()
        Logger.info('Page "' + CurrentPage.page_title + '" with ID ' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found')
        Logger.debug('Sources are loaded, collecting incremental data and calculating difference... ')
        SQL_Connector_inst.UpdateKnownPagesLast_check(CurrentPage)
        # getting sources for all missing versions + latest in DB
        for VersionNumber in range(CurrentPage.dbVersion, CurrentPage.page_versions + 1):
            CurrentPage.add_new_page_version(CurrentPage.get_version_content_by_version(VersionNumber))
        PageAnalysisEndTime = datetime.now()
        Logger.info('Page "' + CurrentPage.page_title + '" with ID ' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found')
        Logger.debug('Sources are loaded, calculating difference... ')
        # loading old datagram
        CurrentPage.pageSQL_id = SQL_Connector_inst.GetPageSQLID(CurrentPage)
        TempArray = SQL_Connector_inst.GetDatagrams(CurrentPage)
        CurrentPage.VersionsGlobalArray = pickle.loads(TempArray[0])
        TempContributors = pickle.loads(TempArray[1])
        # comparing latest versions
        Contrib_Compare_inst.incremental_compare(CurrentPage)
        CurrentPage.TotalCharacters = len(CurrentPage.VersionsGlobalArray)
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
        Logger.debug('Characters in TOTAL: ' + str(CurrentPage.TotalCharacters))
        if CurrentPage.TotalCharacters != 0:
            for Contributor, Value in CurrentPage.TotalContribute.items():
                Percent = (Value / CurrentPage.TotalCharacters) * 100
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
        Logger.info('Page "' + CurrentPage.page_title + '" is up-to-date')
        PageAnalysisEndTime = datetime.now()
        SQL_Connector_inst.UpdateKnownPagesLast_check(CurrentPage)

TaskEndTime = datetime.now()
TotalElapsed = TaskEndTime - TaskStartTime
Logger.info('Task finished, total time wasted: ' + str(TotalElapsed))
