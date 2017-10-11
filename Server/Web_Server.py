import ctypes
import json
from urllib.parse import parse_qs

from gevent import monkey
from gevent import pywsgi

import Server.PostExeptions as WebExceptions
from Server.ServerLogic import WebPostRequest
import logging
from datetime import datetime
import Configuration


def logging_config(logging_mode: str= 'INFO') -> object:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger_inst = logging.getLogger()
    logger_inst.setLevel(logging_mode)
    integration_config = Configuration.Integration()
    log_name = integration_config.log_location + "Web_Server_v2.0_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S")) + '.log'
    fh = logging.FileHandler(log_name)
    fh.setLevel(logging_mode)
    fh.setFormatter(formatter)
    logger_inst.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging_mode)
    ch.setFormatter(formatter)
    logger_inst.addHandler(ch)
    return logger_inst

global Logger # TODO: find a better way to pass logger object into server_logic (WSGIServer docs: self.result = self.application(self.environ, self.start_response))
Logger = logging_config(logging_mode='DEBUG')

GlobalStartTime = datetime.now()

is_admin = ctypes.windll.shell32.IsUserAnAdmin()
if is_admin != 1:
    print('You\'r no admin here!')
    exit()

monkey.patch_all()  # makes many blocking calls asynchronous

mysql_config = Configuration.MySQLConfig()
sql_config = Configuration.SQLConfig()

WebPostRequest_instance = WebPostRequest(mysql_config=mysql_config, sql_config=sql_config)


def post_request_analyse(request_body: bytes, logger_handle: logging.RootLogger)->str:
    request_body = request_body.decode("utf-8")
    request = parse_qs(request_body)
    try:
        method = request['method'][0]
    except KeyError:
        return json.dumps({'Error': 'Bad request - no method specified'}, separators=(',', ':'))
    try:
        answer = WebPostRequest_instance.invoke(method=method, request=request)
        return answer
    except WebExceptions.MethodNotSupported as error:
        logger_handle.error(error)
        return WebPostRequest_instance.error_answer(str(error))

    except WebExceptions.BadRequestException as error:
        # logger_handle.error(error
        return WebPostRequest_instance.error_answer(str(error))

    except (WebExceptions.EmptyPage, WebExceptions.DeprecatedPage, WebExceptions.IndexingTimeOut, WebExceptions.IndexingFailure, WebExceptions.KarmaInvokeFailure, WebExceptions.NothingFound) as error:
        logger_handle.error(error)
        return WebPostRequest_instance.error_answer(str(error))

    except WebExceptions.PageDeleteFailure as error:
        logger_handle.error('Critical Exception:')
        logger_handle.error(error)
        return WebPostRequest_instance.error_answer(str(error))

    except Exception as error:
        logger_handle.error(error)
        return WebPostRequest_instance.error_answer(str(error))
        pass


def server_logic(environ, start_response):
    if environ["REQUEST_METHOD"] == "POST":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        request_body = environ["wsgi.input"].read()
        answer_body = post_request_analyse(request_body, logger_handle=Logger)
        try:
            request_body_decoded = request_body.decode("utf-8")
            request = parse_qs(request_body_decoded)
            Logger.debug('Requested by page: ' + environ['HTTP_REFERER'] + ', method: ' + str(request))
        except KeyError:
            try:
                if request['REMOTE_ADDR'][0] == '172.17.17.183': # xWiki ip addr
                    Logger.debug('Requested by http://xwiki.support2.veeam.local/, method: ' + str(request))
                else:
                    Logger.debug('Unknown requester, method: ' + request['method'][0])
                    Logger.debug('Environ: ' + str(environ))
            except KeyError:
                pass
            pass
        yield answer_body.encode()
    elif environ["REQUEST_METHOD"] == 'GET':
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        yield '<b>Server is operational</b>\n'.encode()
    else:
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        yield '<b>Such requests are not supported</b>\n'.encode()


address = "SUP-A1631.AMUST.LOCAL", 8080
server = pywsgi.WSGIServer(address, server_logic, log=Logger, error_log=Logger)
server.backlog = 256
Logger.info('Initialization finished, server started at ' + str(GlobalStartTime))
server.serve_forever()
