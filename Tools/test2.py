from datetime import datetime

time_now = str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S",))

log = open('Migration_log.txt', 'w')
print("hi there", file=log)

