from Configuration import MySQLConfig
from Mechanics import MysqlConnector, xWIKIDB_data_handler
import datetime

MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)

DataTuple = (
    ('xWIki_space', 'Sandbox'),
    ('parent_page', 'ololo_page'), # should exist
    ('title', '1st_attempt_to_insert'),
    ('creation_time', str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
    ('XWD_AUTHOR', 'XWiki.drozhdestvenskiy'),
    ('XWD_CONTENT_AUTHOR', 'XWiki.drozhdestvenskiy'),
    ('XWD_CREATOR', 'XWiki.drozhdestvenskiy'),
    ('content', 'it works!'),
    ('version', '1.1'),
    ('syntax', 'xwiki/2.1'),
    ('XWD_ID', MysqlConnector_INSTANCE.generate_new_uniqe_xwikilike_id()),
    ('XWS_ID', MysqlConnector_INSTANCE.generate_new_uniqe_xwikilike_id()),
)

xWIKIDB_instance = xWIKIDB_data_handler(*DataTuple)
result = MysqlConnector_INSTANCE.insert_into_xwikilistitems(xWIKIDB_instance)
print(result)

'''
result = MysqlConnector_INSTANCE.insert_into_xwikidoc(*DataTuple)
print(result)

result = MysqlConnector_INSTANCE.insert_into_xwikispace(*DataTuple[:8], MysqlConnector_INSTANCE.generate_new_uniqe_xwikilike_id())
print(result)

result = MysqlConnector_INSTANCE.update_xwikircs(*DataTuple)
print(result)
'''