from datetime import datetime,timedelta
from time import sleep

first_time = datetime.now()

sleep(1)
second_time = datetime.now()

tdelta = second_time - first_time
allowed_tdelta = timedelta(seconds=3)
if tdelta < allowed_tdelta:
    print(tdelta)