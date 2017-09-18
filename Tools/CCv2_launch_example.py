import pickle
import os
import subprocess
import uuid
import base64
os.supports_bytes_environ = True

dict_to_pickle = {'Main.Support Team.Support Official Procedures.Case Handling.85a1d076c26ba01e58d2e828595e402e': 'xwiki'}


def start_core_as_subprocess(dict_to_pickle: dict):
    pickled_data = pickle.dumps(dict_to_pickle, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    id = str(uuid.uuid4())
    os.environ[id] = pickled_and_decoded_dict
    print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO False -b" + id, shell=True)


start_core_as_subprocess(dict_to_pickle)
