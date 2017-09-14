import pickle
import os
import subprocess
import uuid
import base64
os.supports_bytes_environ = True

dict_to_pickle = {'Main.Bugs and Fixes.Fix Upload.WebHome': 'xWIKI'}
print('source dict:', dict_to_pickle, type(dict_to_pickle))
pickled_data = pickle.dumps(dict_to_pickle, 0)
print('pickled dict:', pickled_data, type(pickled_data))
pickled_and_decoded_dict = pickled_data.decode('latin1')
print('pickled + decoded dict goes to env:', pickled_and_decoded_dict, 'len', len(pickled_and_decoded_dict))
id = str(uuid.uuid4())

os.environ[id] = pickled_and_decoded_dict

# now we have environ
'''
# test encode:
print('env_name', id)
str_environ = os.environ[id]
print('pickled + decoded dict from env:', str_environ)
pickled_dict = str_environ.encode('latin1')
print('pickled + encoded dict from env:', pickled_dict, type(pickled_dict))
task_pages_dict = pickle.loads(pickled_dict)
print('source dict', task_pages_dict, type(task_pages_dict))
'''
print('---------sub process started-------------')
env = {
    **os.environ,
    id: pickled_and_decoded_dict,
}
subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO true -b" + id, shell=True)
