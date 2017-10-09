import ctypes
import json
from urllib.parse import parse_qs

from gevent import monkey
from gevent import pywsgi

import Server.PostExeptions as WebExceptions
from Server.ServerLogic import WebPostRequest

import Configuration

is_admin = ctypes.windll.shell32.IsUserAnAdmin()
if is_admin != 1:
    print('You\'r no admin here!')
    exit()

monkey.patch_all()  # makes many blocking calls asynchronous

mysql_config = Configuration.MySQLConfig()
sql_config = Configuration.SQLConfig()

WebPostRequest_instance = WebPostRequest(mysql_config=mysql_config, sql_config=sql_config)


def post_request_analyse(request_body):
    request_body = request_body.decode("utf-8")
    request = parse_qs(request_body)
    try:
        method = request['method'][0]
    except KeyError:
        return json.dumps({'Error': 'Bad request - no method specified'}, separators=(',', ':'))
    try:
        WebPostRequest_instance.invoke(method=method, request=request)

    except WebExceptions.MethodNotSupported as error:
        return WebPostRequest_instance.error_answer(str(error))

    except Exception as error:
        return WebPostRequest_instance.error_answer(str(error))
        pass


def server_logic(environ, start_response):
    if environ["REQUEST_METHOD"] == "POST":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        request_body = environ["wsgi.input"].read()
        answer_body = post_request_analyse(request_body)
        yield answer_body.encode()
    elif environ["REQUEST_METHOD"] == 'GET':
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        yield '<b>Server is operational</b>\n'.encode()
    else:
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        yield '<b>Such requests are not supported</b>\n'.encode()


address = "SUP-A1631.AMUST.LOCAL", 8081
server = pywsgi.WSGIServer(address, server_logic)
server.backlog = 256
server.serve_forever()
