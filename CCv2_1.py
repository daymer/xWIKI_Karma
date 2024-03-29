import argparse
import logging
import os
import pickle
import re
from datetime import datetime
import requests
import urllib3


from PythonConfluenceAPI import ConfluenceAPI
from mwclient import Site

import Configuration
from CustomModules.Mechanics import ContributionComparator, MysqlConnector, XWikiClient
from CustomModules.PageMechanics import PageXWiki, PageMediaWiki, PageConfluence
from CustomModules.SQL_Connector import SQLConnector

GlobalStartTime = datetime.now()

log_level = None
task_pages_dict = None
log_to_file = None
token = None

##############################################################
#                      Test variables                        #
UseTestVarsSwitch = False
TestVars = {
    'log_level': 'DEBUG',
    'log_to_file': False,
    'task_pages_dict': {'Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI.939ab1d4f9f24331e952b7dccf0c7c1b': 'xWIKI'}
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
    parser.add_argument("token", type=str)
    parser.add_argument("-t", "--title", type=str)
    parser.add_argument("-p", "--platform", type=str)
    parser.add_argument("-b", "--binary_dict_id", type=str)
    args = parser.parse_args()
    log_level = args.log_level
    log_to_file = bool(eval(args.log_to_file))
    token = args.token
    if args.title and args.platform:
        task_pages_dict = {args.title: args.platform}
    elif args.binary_dict_id:
        str_environ = os.environ[args.binary_dict_id]
        task_pages_dict = pickle.loads(str_environ.encode('latin1'))
if log_level is None or task_pages_dict is None or log_to_file is None or token is None:
    exit(1)


def initialize(task_pages_dict: dict, logging_mode: str = 'INFO', log_to_file_var: bool = False, contrib_log_mode: str = 'silent'):
    ###################################################################################################################
    # Contrib_Compare_inst - used to analyze pages and create page contribution maps based on the content,            #
    # collected from one of supported platforms                                                                       #
    # mysql_connector_inst, sql_connector_inst - used to store\load page contribution maps in\from SQL\mySQL          #
    # xWikiAPI_inst, mWikiAPI_instance, ConfluenceAPI_inst - used to get data from the supported sources              #
    #                                                                                                                 #
    ###################################################################################################################
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger_inst = logging.getLogger()
    logger_inst.setLevel(logging_mode)
    integration_config = Configuration.Integration()
    if log_to_file_var is True:
        if len(task_pages_dict) == 1:
            task_pages_dict_temp = task_pages_dict.copy()
            log_title, log_platform = task_pages_dict_temp.popitem()
            log_name = integration_config.CC_log_location + "Core_v2.1_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S")) + '_' + str(log_title).replace('/', '').replace('\\', '').replace(' ', '_').replace('"', '_') + '_' + log_platform + '.log'
        else:
            log_name = integration_config.CC_log_location + "Core_v2.1_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S")) + '.log'
        fh = logging.FileHandler(log_name)
        fh.setLevel(logging_mode)
        fh.setFormatter(formatter)
        logger_inst.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging_mode)
    ch.setFormatter(formatter)
    logger_inst.addHandler(ch)
    contrib_compare_inst = ContributionComparator(contrib_log_mode)
    sql__config_inst = Configuration.SQLConfig()
    confluence__config_inst = Configuration.ConfluenceConfig()
    m_wiki__config_inst = Configuration.MediaWIKIConfig()
    x_wiki__config_inst = Configuration.XWikiConfig(['Migration pool', 'Sandbox', 'Main', 'StagingWiki'])
    mysql__config_inst = Configuration.MySQLConfig()
    mysql_connector_inst = MysqlConnector(mysql__config_inst)
    sql_connector_inst = SQLConnector(sql__config_inst)
    confluence_api_inst = ConfluenceAPI(confluence__config_inst.USER, confluence__config_inst.PASS,
                                       confluence__config_inst.ULR)
    x_wiki_api_inst = XWikiClient(x_wiki__config_inst.api_root, x_wiki__config_inst.auth_user,
                                  x_wiki__config_inst.auth_pass)
    m_wiki_api_instance = Site((m_wiki__config_inst.Protocol, m_wiki__config_inst.URL), path=m_wiki__config_inst.APIPath,
                                          clients_useragent=m_wiki__config_inst.UserAgent)
    search_config_inst = Configuration.SearchConfig()
    return contrib_compare_inst, mysql_connector_inst, confluence_api_inst, sql_connector_inst, logger_inst, x_wiki_api_inst, m_wiki_api_instance, search_config_inst

Contrib_Compare_inst, Mysql_Connector_inst, ConfluenceAPI_inst, SQL_Connector_inst, Logger, xWikiAPI_inst, mWikiAPI_instance, Search_Config = initialize(task_pages_dict, logging_mode=log_level, log_to_file_var=log_to_file)
Logger.info('Initialization finished, job started at ' + str(GlobalStartTime) + ', token: ' + token)
TaskStartTime = datetime.now()


def re_info_for_bug_page(page_content_func: str, page_title: str):
    logger = logging.getLogger()
    logger.debug(page_content_func)
    bug_id_func = None
    product_func = None
    tbfi_func = None
    components_func = None
    style = None
    bug_title = None
    added_to_wiki_func = None
    added_to_wiki_by_func = None
    fix_link = None
    # determination of page syntax
    # checking if a page has syntax version comment
    regex = r"{{comment}}\nVersion=(.*)\n{{\/comment}}"
    matches = re.search(regex, page_content_func, re.IGNORECASE)
    if matches:
        syntax_version = matches.group(1).replace('\r', '')
        if syntax_version == '1.0':
            style = 'xwiki_versioning'
        else:
            logger.critical('syntax_version of bug is not supported, syntax version: ' + str(syntax_version))
            return False
    else:
        # determination of legacy style
        regex = r"\*\*Components:\*\* (.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            style = 'xwiki'
        else:
            regex = r"'''Components: '''(.*)"
            matches = re.search(regex, page_content_func)
            if matches:
                style = 'mwiki'
            else:
                # extra check for moved space
                regex = r"\*\*Components: \*\*(.*)"
                matches = re.search(regex, page_content_func)
                if matches:
                    style = 'xmwiki_moved_space'
    logger.debug('Bug style is: ' + str(style))
    if style is None:
        return False
    elif style == 'xwiki_versioning':
        if syntax_version == '1.0':
            regex = r"Bug \d* - (.*)$"
            matches = re.search(regex, page_title, re.IGNORECASE)
            if matches:
                bug_title = matches.group(1).replace('\r', '')
            logger.debug('bug_title:' + str(bug_title))
            regex = r"\*\*Bug ID:\*\* (.*)"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                bug_id_func = matches.group(1).replace('\r', '')
            regex = r"\*\*Product:\*\* (.*)"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                product_func = matches.group(1).replace('\r', '')
            regex = r"\*\*To be fixed in:\*\* (.*)"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                tbfi_func = matches.group(1).replace('\r', '')
            regex = r"\*\*Components:\*\* (.*)"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                components_func = matches.group(1).replace('\r', '')
            regex = r"\*\*Added:\*\* (.*) by"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                added_to_wiki_func = matches.group(1).replace('\r', '')
            regex = r"\*\*Added:\*\* .* by \[\[(.*)>>"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                added_to_wiki_by_func = matches.group(1).replace('\r', '')
            regex = r"\*\*Private fix external URL \(it IS accessible to customers!\):\*\* (.*)"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                fix_link = matches.group(1).replace('\r', '')
                logger.debug('re_info_for_bug_page: fix_link: ' + str(fix_link))
    elif style == 'xwiki':
        bug_title = page_content_func.split('\n')[1]
        logger.debug('bug_title:' + bug_title)
        regex = r"\*\*Bug ID:\*\* (.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            bug_id_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Product:\*\* (.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            product_func = matches.group(1).replace('\r', '')
        regex = r"\*\*To be fixed in:\*\* (.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            tbfi_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Components:\*\* (.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            components_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Added:\*\* (.*) by"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            added_to_wiki_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Added:\*\* .* by \[\[(.*)>>"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            added_to_wiki_by_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Private fix external URL \(it IS accessible to customers!\):\*\* (.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            fix_link = matches.group(1).replace('\r', '')
    elif style == 'xmwiki_moved_space':
        regex = r"\*\*Bug ID: \*\*(.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            bug_id_func = matches.group(1).replace('\r', '')
        else:
            regex = r"Bug (.*) -"
            matches = re.search(regex, page_title)
            if matches:
                bug_id_func = matches.group(1).replace('\r', '')
                logger.debug('bug_id_func: ' + str(bug_id_func))
        regex = r"\*\*Product: \*\*(.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            product_func = matches.group(1).replace('\r', '')
        else:
            product_func = 'Undefined'
        regex = r"\*\*To be fixed in: \*\*(.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            tbfi_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Components: \*\*(.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            components_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Added: \*\*(.*) by"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            added_to_wiki_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Added: \*\*.* by \[\[(.*)>>"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            added_to_wiki_by_func = matches.group(1).replace('\r', '')
        regex = r"\*\*Private fix external URL \(it IS accessible to customers!\): \*\* (.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            fix_link = matches.group(1).replace('\r', '')
    elif style == 'mwiki':
        regex = r"bug\W*(\d*)\W*"
        matches = re.search(regex, page_title, re.IGNORECASE)
        if matches:
            bug_id_func = matches.group(1)
        else:
            bug_id_func = 'Undefined'
        product_func = 'Undefined'
        regex = r"'''To be fixed in: '''(.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            tbfi_func = matches.group(1).replace('\r', '')
        else:
            regex = r"'''Fixed in: '''(.*)"
            matches = re.search(regex, page_content_func, re.IGNORECASE)
            if matches:
                tbfi_func = matches.group(1).replace('\r', '')
            else:
                tbfi_func = 'Undefined'
        regex = r"'''Components: '''(.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            components_func = matches.group(1).replace('\r', '')
        regex = r"'''Added: '''(.*) by"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            added_to_wiki_func = matches.group(1).replace('\r', '')
        regex = r"'''Added: '''.* by \[\[User:(.*)\|"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            added_to_wiki_by_func = matches.group(1).replace('\r', '')
        regex = r"'''Private fix external URL \(it IS accessible to customers!\):'''(.*)"
        matches = re.search(regex, page_content_func, re.IGNORECASE)
        if matches:
            fix_link = matches.group(1).replace('\r', '')
    try:
        bug_id_func = int(bug_id_func)
    except ValueError as error:
        bug_id_func = 0
    if fix_link == 'n/a':
        fix_link = None
    return bug_id_func, product_func, tbfi_func, components_func, bug_title, added_to_wiki_func, added_to_wiki_by_func, fix_link


for title, platform in task_pages_dict.items():
    # Creating new page instance. Practically, page inst is everything what we need to get page index
    PageAnalysisStartTime = datetime.now()
    Logger.info(title + ': Task initialized.')
    if platform.lower() == 'xwiki':
        # title is not a valid term in case of xWIki. Pages there have 2 separate options:
        # page (used in api path) and title (unused).
        # So, first we have to find it's name to make sure that the provided page exists
        real_title = Mysql_Connector_inst.get_XWD_TITLE(title)
        if real_title is None or len(real_title) == 0:
            Logger.error('Unable to find title of page "' + title + '". Skipping.')
            continue
        try:
            CurrentPage = PageXWiki(page=title, page_title=real_title, client_instance=xWikiAPI_inst)
        except ValueError as error:
            Logger.error('Unable to initialize PageXWiki instance "' + title + '". Skipping.')
            Logger.error(error)
            continue
        if CurrentPage.page_id is None:
            Logger.warning(title + ' is redirect or unable to find ID, skipping')
            continue
    elif platform.lower() == 'mediawiki':
        try:
            CurrentPage = PageMediaWiki(page_title=title, client_instance=mWikiAPI_instance)
        except ValueError:
            Logger.warning(title + ' is redirect or unable to find ID, skipping')
            continue
        if CurrentPage.page_id is None:
            Logger.warning(title + ' is redirect or unable to find ID, skipping')
            continue
    elif platform.lower() == 'confluence':
        try:
            CurrentPage = PageConfluence(page_title=title, client_instance=ConfluenceAPI_inst)
        except ValueError:
            Logger.warning(title + ' is redirect or unable to find ID, skipping')
            continue
    else:
        Logger.warning('platform ' + platform + ' is not supported, skipping')
        continue
    # Now we check if this page has "no_karma" tag. This check works only for xWiki pages
    if isinstance(CurrentPage, PageXWiki):

        def check_if_system_page(page_object: PageXWiki) -> bool:
            tags = page_object.xWikiClient_inst.get_tags_of_page(space=page_object.space, page=page_object.page,
                                                                 nested_space=page_object.nested_spaces,
                                                                 is_terminal_page=page_object.is_terminal_page)
            for tag in tags['tags']:
                if tag['name'] == 'no_karma':
                    return True
            return False

        result = check_if_system_page(CurrentPage)
        if result is True:
            Logger.info('System page, indexing is not needed')
            CurrentPage.dbVersion = SQL_Connector_inst.select_version_from_dbo_knownpages(page_id=CurrentPage.page_id)
            if CurrentPage.dbVersion is not None:
                Logger.info('System page was indexed before, removing from DB')
                result = SQL_Connector_inst.exec_delete_page_by_page_id(CurrentPage.page_id)
                if result is True:
                    Logger.info('Page deleted from DB')
                else:
                    Logger.error('Failed to delete page from DB')
            exit(0)

    CurrentPage.dbVersion = SQL_Connector_inst.select_version_from_dbo_knownpages(page_id=CurrentPage.page_id)
    SQL_Connector_inst.update_dbo_webrequests_reindex_page_by_xwd_fullname(result=0, is_full='pass', token_id=token)

    # FULL MODE:
    if CurrentPage.dbVersion is None:
        SQL_Connector_inst.update_dbo_webrequests_reindex_page_by_xwd_fullname(result=0, is_full=1, token_id=token)
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
            Logger.debug(CurrentPage.contributors[VersionNum] + ' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
            if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) is None:
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
        CurrentPage.SQL_id = SQL_Connector_inst.insert_into_dbo_knownpages(page_object=CurrentPage)
        Logger.info(CurrentPage.page_title + ' was added to DB')
        SQL_Connector_inst.insert_into_dbo_knownpages_datagrams(page_object=CurrentPage)
        SQL_Connector_inst.insert_into_dbo_knownpages_contribution(page_object=CurrentPage)
        SQL_Connector_inst.insert_into_dbo_knownpages_userscontribution(page_object=CurrentPage)
    # INCREMENTAL MODE:
    elif CurrentPage.dbVersion < CurrentPage.page_versions:
        Logger.info('"' + CurrentPage.page_title + '" will be processed in INCREMENTAL mode')
        PageAnalysisEndTime = datetime.now()
        Logger.debug('Sources are loaded, collecting incremental data and calculating difference... ')
        SQL_Connector_inst.update_dbo_knownpages_is_uptodate(page_id=CurrentPage.page_id, up_to_date=False)
        # getting sources for all missing versions + latest in DB
        for VersionNumber in range(CurrentPage.dbVersion, CurrentPage.page_versions + 1):
            CurrentPage.add_new_page_version(CurrentPage.get_version_content_by_version(VersionNumber))
        PageAnalysisEndTime = datetime.now()
        Logger.info('Page "' + CurrentPage.page_title + '" with ID ' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found')
        Logger.debug('Sources are loaded, calculating difference... ')
        # loading old datagram
        CurrentPage.SQL_id = SQL_Connector_inst.select_id_from_dbo_knownpages(page_object=CurrentPage, page_id=CurrentPage.page_id)
        TempArray = SQL_Connector_inst.select_datagram_contributors_datagram_from_dbo_knownpages_datagrams(sql_id=CurrentPage.SQL_id)
        CurrentPage.VersionsGlobalArray = pickle.loads(TempArray[0])
        TempContributors = pickle.loads(TempArray[1])
        content_as_list = [x[0] for x in CurrentPage.VersionsGlobalArray]
        page_content = ''.join(content_as_list)
        Logger.debug(page_content)
        # comparing latest versions
        Contrib_Compare_inst.incremental_compare(CurrentPage)
        CurrentPage.TotalCharacters = len(CurrentPage.VersionsGlobalArray)
        for version, user in TempContributors.items():  # Warning! dict.update is used, which means that accidentally matching pairs version:user will be overwritten.
            CurrentPage.contributors.update({version: user})
        # recalculating contribution for all versions
        for VersionNum in range(1, CurrentPage.page_versions + 1):
            UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
            Logger.debug(CurrentPage.contributors[VersionNum] + ' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
            if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) is None:
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
                     str(PageCountingEndTime - PageAnalysisEndTime) + ' = ' + str(PageCountingEndTime - PageAnalysisStartTime))
        PageAnalysisStartTime = None
        PageAnalysisEndTime = None
        PageCountingEndTime = None
        content_as_list = [x[0] for x in CurrentPage.VersionsGlobalArray]
        page_content = ''.join(content_as_list)
        Logger.debug(page_content)
        # pushing updates to SQL
        SQL_Connector_inst.update_dbo_knownpages_last_check_last_modified(CurrentPage.SQL_id, CurrentPage.page_versions, CurrentPage.TotalCharacters)
        SQL_Connector_inst.update_dbo_knownpages_datagrams(page_object=CurrentPage)
        SQL_Connector_inst.insert_into_dbo_knownpages_contribution(page_object=CurrentPage)
        SQL_Connector_inst.insert_into_dbo_knownpages_userscontribution(page_object=CurrentPage)
        SQL_Connector_inst.update_dbo_knownpages_is_uptodate(page_id=CurrentPage.page_id, up_to_date=True)
    # IDLE MODE:
    elif CurrentPage.dbVersion == CurrentPage.page_versions:
        CurrentPage.SQL_id = SQL_Connector_inst.select_id_from_dbo_knownpages(page_object=CurrentPage,
                                                                              page_id=CurrentPage.page_id)
        Logger.info('Page "' + CurrentPage.page_title + '" is up-to-date')
        PageAnalysisEndTime = datetime.now()
        SQL_Connector_inst.update_dbo_knownpages_is_uptodate(page_id=CurrentPage.page_id, up_to_date=True)
    # ----------------BUG ADD TO DB----------------------------------------------------------
    # now we need to check, if it's a bug page to update [dbo].[KnownBugs] if needed
    page_is_a_bug = False
    if CurrentPage.page_id.lower().startswith('xwiki:main.bugs and fixes.found bugs'):
        page_is_a_bug = True
        fix_link = None
        Logger.info('Starting bug analyze sequence')
        # ---it's a bug, need to find it's product and other fields (migrated bugs have invalid paths)
        if len(CurrentPage.VersionsGlobalArray) == 0:
            CurrentPage.SQL_id = SQL_Connector_inst.select_id_from_dbo_knownpages(page_object=CurrentPage,
                                                                                  page_id=CurrentPage.page_id)
            TempArray = SQL_Connector_inst.select_datagram_contributors_datagram_from_dbo_knownpages_datagrams(sql_id=CurrentPage.SQL_id)
            if TempArray is None:
                Logger.error('Kernel panic: Page is indexed, but has no datagram in DB!')
                exit(1)
            else:
                CurrentPage.VersionsGlobalArray = pickle.loads(TempArray[0])
        content_as_list = [x[0] for x in CurrentPage.VersionsGlobalArray]
        page_content = ''.join(content_as_list)
        result = re_info_for_bug_page(page_content_func=page_content, page_title=CurrentPage.page_title)
        if result is not False:
            bug_id, product, tbfi, components, bug_title, added_to_wiki, added_to_wiki_by, fix_link = result
            if bug_id is not None and product is not None and tbfi is not None and components is not None:
                Logger.info('Bug info is parsed, pushing it to DB')
                # here we push the data into [dbo].[KnownBugs]
                components_as_list = components.split(',')
                xml = '<?xml version="1.0" encoding="UTF-8" ?><components>'
                for component in components_as_list:
                    if component.startswith(' '):
                        component = component[1:]
                    xml += '<component><name>' + component + '</name></component>'
                xml += '</components>'
                byte_xml = bytearray()
                byte_xml.extend(map(ord, xml))
                # prior to update a bug, we need to check if fix_link has changed for Elisa
                old_fix_link = SQL_Connector_inst.select_bug_fix_link(known_pages_id=CurrentPage.SQL_id)
                Logger.debug('old_fix_link: '+ str(old_fix_link))
                if old_fix_link == fix_link:
                    fix_link_has_changed = False
                else:
                    fix_link_has_changed = True
                result = SQL_Connector_inst.exec_update_or_add_bug_page(known_pages_id=CurrentPage.SQL_id, bug_id=bug_id,
                                                                        product=product, tbfi=tbfi, xml=byte_xml, bug_title=bug_title, added_to_wiki=added_to_wiki, added_to_wiki_by=added_to_wiki_by, fix_link=fix_link)
                if result is True:
                    Logger.info('Bug info updated')
                    Logger.info(
                        'Inserted into DB: known_pages_id:' + CurrentPage.SQL_id + ' bug_id: ' +  str(bug_id) + ' product: ' + product + ' tbfi: ' + tbfi + ' xml: ' + str(xml) + ' added_to_wiki: ' + str(added_to_wiki) + ' added_to_wiki_by: ' + str(added_to_wiki_by))

                else:
                    Logger.error(
                        'Unable to update bug info in SQL, query params: known_pages_id:' + CurrentPage.SQL_id + ' bug_id: ' +  str(bug_id) + ' product: ' + product + ' tbfi: ' + tbfi + ' xml: ' + str(xml) + ' added_to_wiki: ' + added_to_wiki + ' added_to_wiki_by: ' + added_to_wiki_by)
                # TFS => KARMA sync
                tfs_session = requests.session()
                try:
                    login_status = tfs_session.post(Search_Config.search_server_url + 'login', data=Search_Config.credentials)
                    search_api_check = tfs_session.get(Search_Config.search_server_url + 'api_check')
                    if search_api_check.status_code != 200 or login_status.status_code != 200:
                        raise requests.exceptions.ConnectionError
                    bug_info = tfs_session.get(Search_Config.search_server_url + 'api/bug_details/{0}'.format(bug_id))
                    bug_info_json = bug_info.json()
                    TFS_bug_created_date = bug_info_json['results']['Created Date']
                    TFS_bug_changed_date = bug_info_json['results']['Changed Date']
                    TFS_bug_state = bug_info_json['results']['State']
                    TFS_bug_status = bug_info_json['results']['Status']
                    TFS_bug_build = bug_info_json['results']['Build']
                    known_bug_id = SQL_Connector_inst.select_id_from_knownbugs(bug_id)
                    existence_check = SQL_Connector_inst.select_count_id_from_knownbugs_tfs_state(known_bug_id)
                    if existence_check is True:
                        SQL_Connector_inst.update_dbo_knownbugs_tfs_state(known_bug_id, TFS_bug_created_date, TFS_bug_changed_date, TFS_bug_state, TFS_bug_status, TFS_bug_build)
                    elif existence_check is False:
                        SQL_Connector_inst.insert_into_dbo_knownbugs_tfs_state(known_bug_id, TFS_bug_created_date, TFS_bug_changed_date, TFS_bug_state, TFS_bug_status, TFS_bug_build)
                    else:
                        Logger.error('known_bug_id is None, aborting TFS => KARMA sync')
                except (urllib3.exceptions.NewConnectionError, ConnectionRefusedError, urllib3.exceptions.MaxRetryError,
                        requests.exceptions.ConnectionError) as error:
                    Logger.error('Search API unreachable due to the following error: \n' + str(error))
                    Logger.error('Aborting TFS => KARMA sync')

                except Exception as error:
                    Logger.error('Aborting TFS => KARMA sync due to unknown error: ' + str(error))
                    try:
                        Logger.error('Result of request: ' + str(bug_info))
                        if bug_info.status_code == 403:
                            Logger.error('Seems to be a xwiki bug add procedure violation, adding this info to DB')
                            known_bug_id = SQL_Connector_inst.select_id_from_knownbugs(bug_id)
                            existence_check = SQL_Connector_inst.select_count_id_from_knownbugs_tfs_state(known_bug_id)
                            if existence_check is True:
                                SQL_Connector_inst.update_dbo_knownbugs_tfs_state(known_bug_id, 'NONE',
                                                                                  'NONE', 'NONE',
                                                                                  'bug add procedure violation!', 'NONE')
                            elif existence_check is False:
                                SQL_Connector_inst.insert_into_dbo_knownbugs_tfs_state(known_bug_id, 'NONE',
                                                                                  'NONE', 'NONE',
                                                                                  'bug add procedure violation!', 'NONE')
                            else:
                                Logger.error('known_bug_id is None, aborting TFS => KARMA sync')
                    except:
                        pass
            else:
                Logger.error('Failed to parse some of fields, aborting bug analyze')
        else:
            Logger.error('Unable to parse bug info style, aborting bug analyze')
    # ----------------CHECK, IF PAGE_TITLE WAS CHANGED AFTER THE LAST RUN------------------------
    current_sql_title = SQL_Connector_inst.select_page_title_from_dbo_knownpages(native_sql_id=CurrentPage.SQL_id)
    if current_sql_title is not None:
        if CurrentPage.page_title != current_sql_title:
            result = SQL_Connector_inst.update_dbo_knownpages(native_sql_id=CurrentPage.SQL_id, new_title=CurrentPage.page_title)
            if result is True:
                Logger.info('Page title was updated')
            elif result is False:
                Logger.error('Failed to update page title')
    if page_is_a_bug is True:
        SQL_Connector_inst.update_dbo_webrequests_reindex_page_by_xwd_fullname(result=1, is_full='pass', token_id=token,
                                                                               is_bug=True, fix_link=fix_link, fix_link_has_changed=fix_link_has_changed )
    else:
        SQL_Connector_inst.update_dbo_webrequests_reindex_page_by_xwd_fullname(result=1, is_full='pass', token_id=token)

TaskEndTime = datetime.now()
TotalElapsed = TaskEndTime - TaskStartTime
Logger.info('Task finished, total time wasted: ' + str(TotalElapsed))
