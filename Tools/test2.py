from datetime import datetime
import codecs

log_name = "Migration_log_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S", )) + '.txt'
print(log_name)

log_statement = ''
with codecs.open(log_name, "a", "utf-8") as stream:  # or utf-8
    stream.write(str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S", )) + str(log_statement) + u"\n")