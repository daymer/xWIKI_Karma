import Server.ServerLogic as ServerLogic
from Configuration import MySQLConfig
import json

request = {'platform': 'shit',
            'id': 'shit'}

mysql_conf_inst = MySQLConfig()
WebPostRequest_inst = ServerLogic.WebPostRequest(mysql_conf_inst)

