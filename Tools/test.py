from PythonConfluenceAPI import ConfluenceAPI
import Configuration
import pickle
from Mechanics import SQLConnector, ContributionComparator, MysqlConnector, PageCreator, xWikiClient
from Page_mechanics import PageXWiki, PageGlobal
import logging
from datetime import datetime
import argparse
import os
import re

GlobalStartTime = datetime.now()

log_level = None
task_pages_dict = None
log_to_file = None


UseTestVarsSwitch = True
TestVars = {
    'log_level': 'DEBUG',
    'log_to_file': False,
    'task_pages_dict': {'Main.Official Lectures.WebHome': 'xWIKI'}
}
#                                                            #
##############################################################

if UseTestVarsSwitch is True:
    log_level = TestVars['log_level']
    log_to_file = TestVars['log_to_file']
    task_pages_dict = TestVars['task_pages_dict']


def initialize(task_pages_dict: dict, logging_mode: str = 'INFO', log_to_file_var: bool = False):
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
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger_inst = logging.getLogger()
    logger_inst.setLevel(logging_mode)
    Integration_config = Configuration.Integration()
    if log_to_file is True:
        if len(task_pages_dict) == 1:
            task_pages_dict_temp = task_pages_dict.copy()
            log_title, log_platform = task_pages_dict_temp.popitem()
            log_name = Integration_config.log_location + "Core_v2.0_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S")) + '_' + log_title + '_' + log_platform + '.log'
        else:
            log_name = Integration_config.log_location + "Core_v2.0_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S")) + '.log'
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

Contrib_Compare_inst, Mysql_Connector_inst, ConfluenceAPI_inst, SQL_Connector_inst, Page_Creator_inst, Logger, xWikiClient_inst = initialize(task_pages_dict, logging_mode=log_level, log_to_file_var=log_to_file)
Logger.info('Initialization finished, job started at ' + str(GlobalStartTime))

TaskStartTime = datetime.now()

def check_if_system_page(current_page: PageXWiki) -> bool:
    tags = current_page.xWikiClient_inst.get_tags_of_page(space=current_page.space, page=current_page.page, nested_space=current_page.nested_spaces, is_terminal_page=current_page.is_terminal_page)
    for tag in tags['tags']:
        if tag['name'] == 'no_karma':
            return True
    return False



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
        CurrentPage = PageXWiki(page=title, page_title=real_title, client_instance=xWikiClient_inst)
        if CurrentPage is None:
            Logger.error('Unable to initialize PageXWiki instance "' + title + '". Skipping.')
            continue
        if CurrentPage.page_id is None:
            Logger.warning(title + ' is redirect or unable to find ID, skipping')
            continue
        result = check_if_system_page(CurrentPage)
        if result is True:
            Logger.info('System page, indexing is not needed')
            exit(0)

