from PythonConfluenceAPI import ConfluenceAPI
import Configuration
import pickle
from Mechanics import PageCreator, SQLConnector, ContributionComparator, ExclusionsDict, MysqlConnector
import logging
from datetime import datetime
import uuid
import os
import subprocess
import sys
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
     # 'ALL mWIKI': 'MediaWIKI'
     'Main': 'xWIKI',
    # 'Sandbox': 'xWIKI',
    # 'Migration pool': 'xWIKI',
    # 'Migrated bugs': 'xWIKI'
     'StagingWiki': 'xWIKI'
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

def start_core_as_subprocess(dict_to_pickle: dict):
    pickled_data = pickle.dumps(dict_to_pickle, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    # print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO True -b" + temp_id, shell=True)

task_pages_dict, TaskStartTime = build_task_array(task_dict=Task, task_exclusions_dict=TaskExclusions, Logger=Logger)

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
