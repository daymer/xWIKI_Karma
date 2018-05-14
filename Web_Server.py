import ctypes
import json
from urllib.parse import parse_qs

from gevent import monkey
from gevent import pywsgi

import Server.PostExceptions as WebExceptions
from Server.ServerLogic import WebPostRequest
import Server.ServerLogic as ServerFunctions
import logging
from datetime import datetime
import Configuration
import socket
from ldap3 import Server, Connection, ALL, NTLM, ObjectDef, Reader
import os
import copy
from sys import platform


def logging_config(logging_mode: str= 'INFO', log_to_file: bool=False) -> object:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger_inst = logging.getLogger()
    logger_inst.setLevel(logging_mode)
    integration_config = Configuration.Integration()
    if log_to_file is True:
        log_name = integration_config.log_location + "Web_Server_v2.0_" + str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S")) + '.log'
        try:
            previous_log_location = os.environ['karma_log'].encode('latin1')
        except:
            previous_log_location = 'none'
        if platform == "linux" or platform == "linux2":
            with open(os.path.expanduser("~/.bashrc"), "a") as outfile:
                # 'a' stands for "append"
                outfile.write("export karma_log_old="+previous_log_location)
                outfile.write("export karma_log=" + log_name)
        elif platform == "win32":
            # do nothing :)
            pass
        fh = logging.FileHandler(log_name)
        fh.setLevel(logging_mode)
        fh.setFormatter(formatter)
        logger_inst.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging_mode)
    ch.setFormatter(formatter)
    logger_inst.addHandler(ch)
    return logger_inst

Logger = logging_config(logging_mode='INFO', log_to_file=True)

GlobalStartTime = datetime.now()
if os.name == 'nt':
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    if is_admin != 1:
        print('You\'r no admin here!')
        exit()

monkey.patch_all()  # makes many blocking calls asynchronous

mysql_config = Configuration.MySQLConfig()
sql_config = Configuration.SQLConfig()
'''
# It was an idea to resolve user nave by LDAP, but xWIki lacks DNS to make it real. 
So, we have an IP of page requester's pc, but nobody wants to spend 1-3 secs waiting for an answer from DNS. 
ldap_server = Server(ldap_conf.ad_server, get_info=ALL)
CONN_TO_LDAP = Connection(ldap_server, user=ldap_conf.username, password=ldap_conf.password, authentication=NTLM,
                  auto_bind=True)
'''
WebPostRequest_instance = WebPostRequest(mysql_config=mysql_config, sql_config=sql_config)


def post_request_analyse(request_body: bytes, logger_handle: logging.RootLogger, environ: dict)->str:
    # logger_handle.debug(str(environ))
    try:
        requested_by_url = environ['HTTP_REFERER']
    except Exception as error:
        requested_by_url = 'Undefined'
    request_body = request_body.decode("utf-8")
    request = parse_qs(request_body)
    try:
        method = request['method'][0]
    except KeyError:
        return json.dumps({'Error': 'Bad request - no method specified'}, separators=(',', ':'))
    try:
        test_dict = copy.deepcopy(request)
        for key, value in test_dict.items():
            if value[0].find('"') != -1:
                    #print(value[0], key)
                    new_value = value[0]
                    #request[key] = new_value.replace('"', '%22')
                    #print(request[key])
        answer = WebPostRequest_instance.invoke(method=method, request=request, requested_by_url=requested_by_url)
        logger_handle.debug(answer)
        return answer
    except WebExceptions.MethodNotSupported as error:
        logger_handle.error(error)
        return WebPostRequest_instance.error_answer(str(error))

    except WebExceptions.BadRequestException as error:
        logger_handle.error(error)
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


def get_request_analyse(logger_handle: logging.RootLogger, environ: dict)->str:
    #logger_handle.debug(str(environ))
    try:
        requested_by_url = environ['HTTP_REFERER']
    except Exception as error:
        requested_by_url = 'Undefined'
    request = parse_qs(environ['QUERY_STRING'])
    try:
        method = request['method'][0]
    except KeyError:
        return json.dumps({'Error': 'Bad request - no method specified'}, separators=(',', ':'))
    try:
        test_dict = copy.deepcopy(request)
        for key, value in test_dict.items():
            if value[0].find('"') != -1:
                request[key] = value.replace('"', '%22')
        if str(method).startswith('get'):
            answer = WebPostRequest_instance.invoke(method=method, request=request, requested_by_url=requested_by_url)
            logger_handle.debug(answer)
            return answer
        else:
            logger_handle.error('Get instead of post, environ:' + str(environ))
            return WebPostRequest_instance.error_answer('Are you Mikhail Shmakov?')
    except WebExceptions.MethodNotSupported as error:
        logger_handle.error(error)
        return WebPostRequest_instance.error_answer(str(error))

    except WebExceptions.BadRequestException as error:
        logger_handle.error(error)
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
        start_response("200 OK", [("Content-Type", "application/json; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        request_body = environ["wsgi.input"].read()
        logger = logging.getLogger('root')
        try:
            request_body_decoded = request_body.decode("utf-8")
            request = parse_qs(request_body_decoded)
            requested_hostname = str(environ['HTTP_HOST']).replace('.amust.local:8080', '')
            # user = ServerFunctions.get_ad_host_description(connection_to_ldap=CONN_TO_LDAP, requested_hostname=requested_hostname)
            ADuser = 'Unknown'
            logger.info('Requested by page: ' + environ['HTTP_REFERER'] + ' , AD_user: ' + ADuser + ', method: ' + str(request))
        except KeyError:
            Logger.debug('Unknown requester, method: ' + request['method'][0])
            Logger.debug('Environ: ' + str(environ))
            pass
        answer_body = post_request_analyse(request_body, logger_handle=logger, environ=environ)
        yield answer_body.encode()
    elif environ["REQUEST_METHOD"] == 'GET':
        start_response("200 OK", [("Content-Type", "application/json; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        request_body = environ["wsgi.input"].read()
        logger = logging.getLogger('root')
        try:
            request_body_decoded = request_body.decode("utf-8")
            request = parse_qs(request_body_decoded)
            requested_hostname = str(environ['HTTP_HOST']).replace('.amust.local:8080', '')
            # user = ServerFunctions.get_ad_host_description(connection_to_ldap=CONN_TO_LDAP, requested_hostname=requested_hostname)
            #ADuser = 'Unknown'
            #logger.info('Requested by page: ' + environ['HTTP_REFERER'] + ' , AD_user: ' + ADuser + ', method: ' + str(request))
        except KeyError:
            #Logger.debug('Unknown requester, method: ' + request['method'][0])
            #Logger.debug('Environ: ' + str(environ))
            pass
        answer_body = get_request_analyse(logger_handle=logger, environ=environ)
        yield answer_body.encode()
        #yield '<b>Server is operational</b>\n'.encode()
    else:
        start_response("200 OK", [("Content-Type", "application/json; charset=utf-8"), ("Access-Control-Allow-Origin", "*")])
        yield '<b>Such requests are not supported</b>\n'.encode()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
local_ip_address = s.getsockname()[0]

address = local_ip_address, 8081
server = pywsgi.WSGIServer(address, server_logic, log=Logger, error_log=Logger)
server.backlog = 256
Logger.info('Initialization finished, server started at ' + str(GlobalStartTime))
server.serve_forever()
