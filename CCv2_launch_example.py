import os
import Configuration
import CustomModules.SQL_Connector
from Server.ServerLogic import xwd_fullname_to_link as xwd_fullname_to_link
from Server.ServerLogic import start_core_as_subprocess as start_core_as_subprocess
import logging
from sys import platform
from datetime import datetime


os.supports_bytes_environ = True


def logging_config(logging_mode: str= 'DEBUG', log_to_file: bool=False) -> object:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger_inst = logging.getLogger()
    logger_inst.setLevel(logging_mode)
    integration_config = Configuration.Integration()
    if log_to_file is True:
        log_name = integration_config.log_location + "Web_Server_v2.0_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S")) + '.log'
        try:
            previous_log_location = os.environ['karma_log'].encode('latin1')
        except:
            previous_log_location = 'none'
        if platform == "linux" or platform == "linux2":
            with open(os.path.expanduser("~/.bashrc"), "a") as outfile:
                # 'a' stands for "append"
                outfile.write("export karma_log_old="+previous_log_location)
                outfile.write("export karma_log=" + log_name)
        elif platform == "win32":
            # do nothing :)
            pass
        fh = logging.FileHandler(log_name)
        fh.setLevel(logging_mode)
        fh.setFormatter(formatter)
        logger_inst.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging_mode)
    ch.setFormatter(formatter)
    logger_inst.addHandler(ch)
    return logger_inst

Logger = logging_config(logging_mode='DEBUG', log_to_file=False)
Logger.info('Test started')

dict_to_pickle = {'Main.Bugs and Fixes.Found Bugs.Veeam ONE.Bug-110451': 'xwiki'}
#dict_to_pickle = {'StagingWiki.New_articles.Notepad Basics and Useful Hints and Tips.WebHome': 'xwiki'}
#Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI.2e4e87d48d264d80ecbf8a2a5831fa3e
# dict_to_pickle = {'Patch 1 cannot be installed with "This Veeam Backup & Replication installation cannot be updated automatically"': 'mediawiki'}
# dict_to_pickle = {'Resolving "Unable to delete host... is used by the following jobs..." in Veeam v9.0 and v9.5': 'confluence'}


sql_config = Configuration.SQLConfig()
sql_connector_instance = CustomModules.SQL_Connector.SQLConnector(sql_config)
xwd_fullname = list(dict_to_pickle)[0]
link = xwd_fullname_to_link(xwd_fullname)
token_id = sql_connector_instance.insert_into_dbo_webrequests_reindex_page_by_xwd_fullname(xwd_fullname, link)
Logger.info('Starting CC_core')
start_core_as_subprocess(dict_to_pickle, token_id, 'DEBUG')

