import pickle
import os
import subprocess
import uuid
os.supports_bytes_environ = True

dict_to_pickle = {'Main.Internal Technical Docs.Veeam Backup and Replication.VeeamBackupDatabase.[dbo]\.[Backup\.Model\.Storages].WebHome': 'xwiki'}
# dict_to_pickle = {'Patch 1 cannot be installed with "This Veeam Backup & Replication installation cannot be updated automatically"': 'mediawiki'}
# dict_to_pickle = {'Resolving "Unable to delete host... is used by the following jobs..." in Veeam v9.0 and v9.5': 'confluence'}


def start_core_as_subprocess(dict_to_pickle_func: dict):
    pickled_data = pickle.dumps(dict_to_pickle_func, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/CCv2.1.py DEBUG True -b" + temp_id, shell=True)


start_core_as_subprocess(dict_to_pickle)
