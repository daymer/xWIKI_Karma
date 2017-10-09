import pickle
import os
import subprocess
import uuid
os.supports_bytes_environ = True

dict_to_pickle = {'Main.Team.Support Official Procedures.Case Handling.85a1d076c26ba01e58d2e828595e402e': 'xwiki'}

def start_core_as_subprocess(dict_to_pickle_func: dict):
    pickled_data = pickle.dumps(dict_to_pickle_func, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO True -b" + temp_id, shell=True)


start_core_as_subprocess(dict_to_pickle)
