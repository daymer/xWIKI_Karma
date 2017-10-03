import pickle
import os
import subprocess
import uuid
import base64
os.supports_bytes_environ = True

dict_to_pickle = {'Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI.88b849695a11b03c05c5aff1a6sdfdd8efd': 'xwiki'}


def start_core_as_subprocess(dict_to_pickle: dict):
    pickled_data = pickle.dumps(dict_to_pickle, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO True -b" + temp_id, shell=True)


start_core_as_subprocess(dict_to_pickle)
