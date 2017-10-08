import pickle
import os
import subprocess
import uuid
import base64
os.supports_bytes_environ = True

dict_to_pickle = {'StagingWiki.Pending for community approval.d0d919912c80cc88ba3c7f36ac29be98.WebHome': 'xwiki'}


def start_core_as_subprocess(dict_to_pickle: dict):
    pickled_data = pickle.dumps(dict_to_pickle, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO True -b" + temp_id, shell=True)


start_core_as_subprocess(dict_to_pickle)
