import pickle
import os
import subprocess
import uuid


dict_to_pickle = {'Main.Bugs and Fixes.Fix Upload.WebHome': 'xWIKI'}
pickled_dict_str = pickle.dumps(dict_to_pickle).decode('ascii')
print(pickled_dict_str)

exit()
id = str(uuid.uuid4())

os.environ[id] = pickled_dict_str
str_dict = os.environ.pop(id)
print(bytes(str_dict, encoding="UTF-8"))
task_pages_dict = pickle.loads(str_dict.encode())
#subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO true -b" + id, shell=True)
