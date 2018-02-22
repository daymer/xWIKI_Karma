import logging
import os
import pickle
import subprocess
import sys
import uuid
from datetime import datetime
from mwclient import Site
from PythonConfluenceAPI import ConfluenceAPI

import Configuration
from CustomModules.Mechanics import ContributionComparator, ExclusionsDict, MysqlConnector
from CustomModules.SQL_Connector import SQLConnector
import CustomModules.Mechanics as Mechanics

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
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger_inst = logging.getLogger()
    logger_inst.setLevel(logging_mode)
    Integration_config = Configuration.Integration()
    if log_to_file is True:
        log_name = Integration_config.log_location + "Comparer_task_builder_v1.0_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S", )) + '.log'
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
    media_w_i_k_i__config_inst = Configuration.MediaWIKIConfig()
    media_wiki_api_inst = Site((media_w_i_k_i__config_inst.Protocol, media_w_i_k_i__config_inst.URL), path=media_w_i_k_i__config_inst.APIPath, clients_useragent=media_w_i_k_i__config_inst.UserAgent)
    xWiki_Config_inst = Configuration.XWikiConfig(['Migration pool', 'Sandbox', 'Main', 'StagingWiki'])
    MySQL_Config_inst = Configuration.MySQLConfig()
    Mysql_connector_inst = MysqlConnector(MySQL_Config_inst)
    SQL_connector_inst = SQLConnector(SQL_config_inst)
    # getting all pages in Confluence:
    confluenceAPI_inst = ConfluenceAPI(confluence_config_inst.USER, confluence_config_inst.PASS,
                                       confluence_config_inst.ULR)
    return contrib_compare_inst, Mysql_connector_inst, confluenceAPI_inst, SQL_connector_inst, logger_inst, media_wiki_api_inst

Contrib_Compare_inst, Mysql_Connector_inst, ConfluenceAPI_inst, SQL_Connector_inst, Logger, MediaWIKI_api_inst = initialize('INFO')
Logger.info('Initialization finished, job started at ' + str(GlobalStartTime))
# Task:
#    Confluence: VB (Veeam B&R Basic knowledge), WB (Veeam Support Hints and Tricks), GZ (Ground Zero)
#    MediaWIKI: just all
#    xWIKI: ['Blog', 'Main', 'Sandbox', 'XWiki']
Task = {
     # 'VB': 'Confluence',
     # 'WB': 'Confluence',
     # 'GZ': 'Confluence',
     # 'ALL mWIKI': 'MediaWIKI'
     #'Main': 'xWIKI',
     'Main.Bugs and Fixes.Found Bugs': 'xWIKI',
    # 'Migration pool': 'xWIKI',
    # 'Migrated bugs': 'xWIKI'
    #  'StagingWiki': 'xWIKI'
    # 'StagingWiki': 'xWIKI'
}



TaskExclusions = ExclusionsDict()
TaskExclusions['Confluence'] = 'List of all KBs'
TaskExclusions['MediaWIKI'] = 'Found Bugs'
TaskExclusions['MediaWIKI'] = 'Registry values B&R'
TaskExclusions['MediaWIKI'] = 'Veeam ONE Registry Keys'
TaskExclusions['MediaWIKI'] = 'Patches and fixes for B&R'
TaskExclusions['MediaWIKI'] = 'Bug%'
TaskExclusions['MediaWIKI'] = 'BUG%'
TaskExclusions['MediaWIKI'] = 'bug%'
TaskExclusions['MediaWIKI'] = 'Case Handling'
TaskExclusions['MediaWIKI'] = 'Team Members'
TaskExclusions['xWIKI'] = 'Main.WebHome'
TaskExclusions['xWIKI'] = 'StagingWiki.WebHome'
TaskExclusions['xWIKI'] = 'StagingWiki.Personal Spaces%'

select = None
#select = "select page_id from [dbo].[KnownPages] inner join [dbo].[KnownBugs] on [dbo].[KnownPages].id =[dbo].[KnownBugs].KnownPages_id where [dbo].[KnownPages].id in(select KnownPages_id from [dbo].[KnownBugs] where id not in (select [KnownBug_ID] FROM [Karma].[dbo].[KnownBugs_TFS_state]) and bug_id != '0')"


def build_task_array(task_dict: dict, task_exclusions_dict: Mechanics.ExclusionsDict, logger):
    global task_pages_dict, platform
    task_pages_dict = {}
    total_size = 0
    for space, platform in task_dict.items():
        if platform.lower() == 'confluence':
            respond = ConfluenceAPI_inst.get_content('page', space, None, 'current', None, None, 0, 500)
            size = respond['size']
            total_size += size
            logger.info(str(size) + ' Confluence pages were found in space ' + space)
            try:
                confluence_pages_from_api = respond['results']
            except Exception:
                logger.error('Unable to get Confluence pages from API, aborting this space')
                continue
            for page in confluence_pages_from_api:
                if task_exclusions_dict[platform] is not None:
                    if not Mechanics.check_exclusions(page['title'], platform, task_exclusions_dict):
                        continue
                    else:
                        task_pages_dict.update({page['title']: platform})
                        size += 1
                else:
                    task_pages_dict.update({page['title']: platform})
                    size += 1
        if platform.lower() == 'mediawiki':
            size = 0
            for page in MediaWIKI_api_inst.allpages():
                if task_exclusions_dict[platform] is not None:
                    if not Mechanics.check_exclusions(page.name, platform, task_exclusions_dict):
                        logger.debug(page.name + ' was excluded')
                        continue
                    else:
                        task_pages_dict.update({page.name: platform})
                        size += 1
                else:
                    task_pages_dict.update({page.name: platform})
                    size += 1
            logger.info(str(size) + ' MediaWIKI pages were found in space "' + space + '"')
            total_size += size
        if platform.lower() == 'xwiki':
            size = 0
            logger.debug('Looking for pages in the following xWIKI space: "' + space + '"')
            for page in Mysql_Connector_inst.get_XWD_FULLNAMEs(space):
                if task_exclusions_dict[platform] is not None:
                    if not Mechanics.check_exclusions(page, platform, task_exclusions_dict):
                        logger.debug(page + ' was excluded')
                        continue
                    else:
                        task_pages_dict.update({page: platform})
                        size += 1
                else:
                    task_pages_dict.update({page: platform})
                    size += 1
            logger.info(str(size) + ' xWIKI pages were found in space "' + space + '"')
            total_size += size
    TaskStartTime = datetime.now()
    logger.info(str(total_size) + ' pages were found in all spaces')
    return task_pages_dict, TaskStartTime

def build_task_array_by_sql_select(select: str, logger, SQL_Connector_inst):
    task_pages_dict = {}
    TaskStartTime = datetime.now()
    pages = SQL_Connector_inst.select_custom_select(select)
    for page in pages:
        page = page[0]
        if str(page).startswith('xwiki:'):
            page = str(page).replace('xwiki:', '')
        task_pages_dict.update({page: 'xwiki'})
    total_size = len(task_pages_dict)
    logger.info(str(total_size) + ' pages were found in all spaces')
    return task_pages_dict, TaskStartTime

def start_core_as_subprocess(dict_to_pickle: dict):
    pickled_data = pickle.dumps(dict_to_pickle, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    # print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/CCv2_1.py INFO True -b" + temp_id, shell=True)

if select is None:
    task_pages_dict, TaskStartTime = build_task_array(task_dict=Task, task_exclusions_dict=TaskExclusions, logger=Logger)
else:
    task_pages_dict, TaskStartTime = build_task_array_by_sql_select(select=select, logger=Logger, SQL_Connector_inst=SQL_Connector_inst)
# starting main process
Logger.info('Re-indexing started')

for title, platform in task_pages_dict.items():
    try:
        dict_to_pickle = {
            title: platform
        }
        Logger.info('Re-indexing of "' + title + '" platform: ' + platform + ' started')
        start_core_as_subprocess(dict_to_pickle)
    except:  # all unhandled exceptions
        error = sys.exc_info()[0]
        Logger.error('Re-indexing unexpectedly failed with: ' + str(error))

Logger.info('Re-indexing finished')
