import pickle
import os
import subprocess
import uuid
import Configuration
os.supports_bytes_environ = True

dict_to_pickle = {'Main.Bugs and Fixes.Found Bugs.Veeam ONE.Bug 123644': 'xwiki'}
#dict_to_pickle = {'StagingWiki.New_articles.Notepad Basics and Useful Hints and Tips.WebHome': 'xwiki'}
#Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI.2e4e87d48d264d80ecbf8a2a5831fa3e
# dict_to_pickle = {'Patch 1 cannot be installed with "This Veeam Backup & Replication installation cannot be updated automatically"': 'mediawiki'}
# dict_to_pickle = {'Resolving "Unable to delete host... is used by the following jobs..." in Veeam v9.0 and v9.5': 'confluence'}


def start_core_as_subprocess(dict_to_pickle: dict):
    try:
        locality = Configuration.Integration()
        pickled_data = pickle.dumps(dict_to_pickle, 0)
        pickled_and_decoded_dict = pickled_data.decode('latin1')
        temp_id = str(uuid.uuid4())
        os.environ[temp_id] = pickled_and_decoded_dict
        print('---------sub process started-------------')
        subprocess.call("python " + str(locality.cc_path)+"CCv2_1.py DEBUG True -b" + temp_id, shell=True)
        return True
    except Exception:
        return False


start_core_as_subprocess(dict_to_pickle)
