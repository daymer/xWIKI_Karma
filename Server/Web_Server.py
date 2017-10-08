import ctypes
import json
import operator
import os
import pickle
import re
import subprocess
import uuid
from datetime import datetime, timedelta
from urllib.parse import parse_qs

from gevent import monkey
from gevent import pywsgi

import Configuration
from CustomModules.Mechanics import Page, CustomLogging, MysqlConnector
from CustomModules.SQL_Connector import SQLConnector

is_admin = ctypes.windll.shell32.IsUserAnAdmin()
if is_admin != 1:
    print('You\'r no admin here!')
    exit()

monkey.patch_all()  # makes many blocking calls asynchronous
SQLConfig = Configuration.SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
CustomLogging = CustomLogging('NOT_silent')


def start_core_as_subprocess(dict_to_pickle: dict):
    try:
        #print(dict_to_pickle)
        pickled_data = pickle.dumps(dict_to_pickle, 0)
        pickled_and_decoded_dict = pickled_data.decode('latin1')
        temp_id = str(uuid.uuid4())
        os.environ[temp_id] = pickled_and_decoded_dict
        print('---------sub process started-------------')
        subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO False -b" + temp_id, shell=True)
        return True
    except:
        return False


def post_request_analyse(request_body):
    request_body = request_body.decode("utf-8")
    request = parse_qs(request_body)
    print(request)
    try:
        method = request['method'][0]
    except:
        return json.dumps({'Error': 'Bad request - no method specified'}, separators=(',', ':'))
    try:
        if method == 'get_stat_by_title':
            page_id = None
            try:  # zero title exception
                platform = request['platform'][0]
                page_id = request['id'][0]
            except:
                return json.dumps({'Error': 'Bad request - no id or platform was provided'}, separators=(',', ':'))
            if page_id is not None:
                MySQLconfig_INSTANCE = Configuration.MySQLConfig()
                MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
                XWD_FULLNAME = MysqlConnector_INSTANCE.get_XWD_FULLNAME(XWD_ID=page_id)
                if XWD_FULLNAME is None:
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with id "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer
                temp_array = SQLConnector.select_id_characters_total_from_dbo_knownpages(
                    page_id=XWD_FULLNAME, platform=platform)
                if temp_array is None:  # page is unknown exception
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with ID "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer

            if temp_array is None:  # page is unknown exception
                page_unknown_answer = json.dumps({
                                                     'Error': 'Bad request - there is no known page with title "' + Current_Page.page_title + '" in the database'},
                                                 separators=(',', ':'))
                return page_unknown_answer

            SQL_id_of_requested_page = temp_array[0]
            total_characters_of_requested_page = int(temp_array[1])
            total_contribute_of_requested_page = pickle.loads(SQLConnector.select_datagram_contribution_from_dbo_knownpages_contribution(sql_id=SQL_id_of_requested_page))
            result = SQLConnector.exec_get_page_karma_and_votes(page_id=SQL_id_of_requested_page)
            up_votes = result[0]
            down_votes = result[1]
            karma_score = result[2]
            if total_characters_of_requested_page != 0:
                answer = {
                    'Error': 0,
                    'page_title': XWD_FULLNAME,
                    'page_DB_id': SQL_id_of_requested_page,
                    'up_votes': up_votes,
                    'down_votes': down_votes,
                    'page_karma_score': karma_score,
                    'contributors_percents': {}
                }
                for Contributor, Value in total_contribute_of_requested_page.items():
                    Percent = round(((Value / total_characters_of_requested_page) * 100), 2)
                    answer['contributors_percents'].update({Contributor: Percent})
                contributors_percents_sorted = sorted(answer['contributors_percents'].items(),
                                                     key=operator.itemgetter(1), reverse=True)
                answer['contributors_percents'] = {}
                for unit in contributors_percents_sorted[:3]:
                    answer['contributors_percents'].update({unit[0]: unit[1]})
            else:
                answer = {'Error': 'Page exists but has 0 characters'}

            return json.dumps(answer, separators=(',', ':'))
        if method == 'get_stat_by_user':
            try:  # zero title exception
                request['user'][0]
            except:
                return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
            username = request['user'][0]
            user_id = SQLConnector.select_id_from_dbo_knownpages_users(username=username)
            if user_id is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            karma_score = round(SQLConnector.exec_get_user_karma_raw_score(user_id=user_id), 2)
            table = SQLConnector.exec_get_user_karma_raw(user_id=user_id)
            answer = {
                        'Error': 0,
                      'user': username,
                      'user_id': user_id,
                      'karma_score': karma_score,
                      'raw_karma': {}
                      }
            for row in table:
                answer['raw_karma'].update({'"'+row.page_title+'"': row.percent})
            return json.dumps(answer, separators=(',', ':'))
        if method == 'vote_for_page_as_user':
            page_id = None
            page_title = None
            try:  # zero title exception
                user_name = request['user_name'][0]
                direction = request['direction'][0]
            except:
                return json.dumps({'Error': 'bad request - no user_name, platform or page_title was provided'}, separators=(',', ':'))
            try:  # zero title exception
                platform = request['platform'][0]
            except:
                return json.dumps({'Error': 'Bad request - no title or platform was provided'}, separators=(',', ':'))
            try:
                page_id = request['id'][0]
            except:
                try:
                    page_title = request['page_title'][0]
                except:
                    return json.dumps({'Error': 'Bad request - no title, id or platform was provided'},
                                      separators=(',', ':'))
            user_id = SQLConnector.select_id_from_dbo_knownpages_users(username=user_name)

            # old or new logic
            if user_id is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            if page_title is not None:
                temp_array = SQLConnector.select_id_characters_total_from_dbo_knownpages(
                   page_title=page_title, platform=platform)
                if temp_array is None:  # page is unknown exception
                   page_unknown_answer = json.dumps({
                       'Error': 'Bad request - there is no known page with title "' + Current_Page.page_title + '" in the database'},
                       separators=(',', ':'))
                   return page_unknown_answer
            if page_id is not None and page_title is None:
                MySQLconfig_INSTANCE = Configuration.MySQLConfig()
                MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
                XWD_FULLNAME = MysqlConnector_INSTANCE.get_XWD_FULLNAME(XWD_ID=page_id)
                if XWD_FULLNAME != None:
                    XWD_FULLNAME = XWD_FULLNAME
                else:
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with id "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer
                temp_array = SQLConnector.select_id_characters_total_from_dbo_knownpages(
                    page_id=XWD_FULLNAME, platform=platform)
                if temp_array is None:  # page is unknown exception
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with ID "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer
            result = SQLConnector.insert_into_dbo_page_karma_votes(sql_id=temp_array[0], user_id=user_id, direction=direction)
            if result.startswith('Error'):
                error = result
                result = 'Already voted'
            else:
                error = 0
            answer = {
                'Error': error,
                'result': result,
            }
            return json.dumps(answer, separators=(',', ':'))
        if method == 'get_karma_score_by_user':
            try:  # zero title exception
                request['user'][0]
            except:
                return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
            username = request['user'][0]
            user_id = SQLConnector.select_id_from_dbo_knownpages_users(username=username)
            if user_id is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            karma_score = round(SQLConnector.exec_get_user_karma_current_score(user_id), 2)
            answer = {
                        'Error': 0,
                      'user': username,
                      'user_id': user_id,
                      'karma_score': karma_score,
                      }
            return json.dumps(answer, separators=(',', ':'))
        if method == 'get_karma_score_global':
            answer = {
                'Error': 0,
                'result': {},
                'len' : 0
            }
            result = SQLConnector.GetGlobalCurrentKarma()
            if result is None:
                return json.dumps({'Error': 'Unable to get statistics'}, separators=(',', ':'))
            for user, score in result:
                karma_score = round(score, 2)
                answer['result'].update({user: karma_score})
            answer['len'] = len(result)
            return json.dumps(answer, separators=(',', ':'))
        if method == 'get_user_karma_current_score_detailed_by_user':
            try:  # zero title exception
                request['user'][0]
            except:
                return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
            username = request['user'][0]
            user_id = SQLConnector.select_id_from_dbo_knownpages_users(username=username)
            if user_id is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            karma_score = round(SQLConnector.exec_get_user_karma_current_score(user_id=user_id), 2)
            table = SQLConnector.exec_get_user_karma_current_score_detailed(user_id=user_id)
            answer = {
                'Error': 0,
                'user': username,
                'user_id': user_id,
                'karma_score': karma_score,
                'detailed_karma_score': {}
            }
            for row in table:
                vote_stat_dict = {
                    'result': row.result,
                    'up': row.up,
                    'down': row.down,
                    'gained_karma': round(row.added_to_karma,2),
                    'page_id':row.page_id
                 }
                answer['detailed_karma_score'].update({'"'+row.page_title+'"': vote_stat_dict})

            return json.dumps(answer, separators=(',', ':'))
        if method == 'make_new_karma_slice_by_user':
            try:  # zero title exception
                request['user'][0]
            except:
                return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
            username = request['user'][0]
            user_id = SQLConnector.select_id_from_dbo_knownpages_users(username=username)
            if user_id is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            result = SQLConnector.exec_make_new_karma_slice(user_id=user_id)
            if result == 'Karma wasn\'t changed':
                error = 406
                result == 'Karma wasn\'t changed since the last slice'
            else:
                error = 0
            answer = {
                'Error': error,
                'user': username,
                'user_id': user_id,
                'result': result
            }

            return json.dumps(answer, separators=(',', ':'))
        if method == 'get_karma_slices_by_user_and_dates':
            try:  # zero title exception
                request['user'][0]
                request['date_start'][0]
                request['date_end'][0]
            except:
                print(request)
                return json.dumps({'Error': 'bad request - not all arguments were provided'}, separators=(',', ':'))
            try:
                request['reverse_array'][0]
                DIRTY_HACK_FOR_Eugene = True
            except:
                DIRTY_HACK_FOR_Eugene = False
            username = request['user'][0]
            date_start = request['date_start'][0]
            date_end = request['date_end'][0]
            try:
                date_start = datetime.strptime(date_start, '%d-%m-%Y')
                date_end = datetime.strptime(date_end, '%d-%m-%Y')
            except:
                return json.dumps({'Error': 'bad request - date cannot be recognised. Please, use day-month-year format, like 31-01-1991'}, separators=(',', ':'))
            if date_start > date_end:
                return json.dumps({'Error': 'bad request: date_start > date_end'}, separators=(',', ':'))
            elif date_start == date_end:
                return json.dumps({'Error': 'bad request: date_start == date_end'}, separators=(',', ':'))
            user_id = SQLConnector.select_id_from_dbo_knownpages_users(username=username)
            if user_id is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            result = SQLConnector.select_karma_score_from_userkarma_slice(user_id, date_start, date_end)
            answer = {
                'Error': 0,
                'user': username,
                'user_id': user_id,
                'result': {}
            }
            if DIRTY_HACK_FOR_Eugene is False:
                for score, change_time_epoch in result:
                    answer['result'].update({score:change_time_epoch})
            else:
                for score, change_time_epoch in result:
                    answer['result'].update({change_time_epoch:score})
            return json.dumps(answer, separators=(',', ':'))
        if method == 'reindex_page_by_XWD_FULLNAME':
            global last_page
            timeout = 3
            allowed_tdelta = timedelta(seconds=timeout)
            if 'last_page' not in globals():
                last_page = [None, datetime.now()]
            try:
                platform = request['platform'][0]
                XWD_FULLNAME = request['XWD_FULLNAME'][0]
            except:
                return json.dumps({'Error': 'Bad request - no XWD_FULLNAME or platform was provided'},
                                  separators=(',', ':'))
            if XWD_FULLNAME is not None:
                if XWD_FULLNAME == 'XWiki.WebHome' or XWD_FULLNAME == 'Main.WebHome' or XWD_FULLNAME == 'StagingWiki.Personal Spaces%' or XWD_FULLNAME.endswith('.WebPreferences'):
                    answer = {'Error': 'XWD_FULLNAME is deprecated'}
                    return json.dumps(answer, separators=(',', ':'))
                if not str(XWD_FULLNAME).lower().startswith('main') and not str(XWD_FULLNAME).lower().startswith('staging'):
                    answer = {'Error': 'Indexing of non-main and non-staging pages using this request is not allowed'}
                    print(answer)
                    return json.dumps(answer, separators=(',', ':'))
                dict_to_pickle = {XWD_FULLNAME: platform}
                if last_page[0] == XWD_FULLNAME and (datetime.now()-last_page[1]) < allowed_tdelta:  # TODO: fix xWiki, for unclear the platform doubles page-update events
                    answer = {'Error': 'Doubled request from indexing of the same page before ' + str(timeout) + ' timeout'}
                    print('Doubled request from indexing of the same page, denied')
                    return json.dumps(answer, separators=(',', ':'))
                else:
                    last_page = [XWD_FULLNAME, datetime.now()]
                result = start_core_as_subprocess(dict_to_pickle)
                if result is True:
                    answer = {'Success': 'Added to processing'}
                else:
                    answer = {'Error': 'Failed to add to processing'}
                return json.dumps(answer, separators=(',', ':'))
        if method == 'delete_page_by_XWD_FULLNAME':
            platform = None
            XWD_FULLNAME = None
            try:  # zero title exception
                platform = request['platform'][0]
                XWD_FULLNAME = request['XWD_FULLNAME'][0]
            except:
                return json.dumps({'Error': 'Bad request - no XWD_FULLNAME or platform was provided'}, separators=(',', ':'))
            if XWD_FULLNAME == '[\'null\']':
                answer = {'Error': 'Failed to delete, Null XWD_FULLNAME was provided'}
                print('ERROR: XWD_FULLNAME = [\'null\']')
                return json.dumps(answer, separators=(',', ':'))
            if XWD_FULLNAME is not None:
                result = SQLConnector.DeletePageByPageID('xwiki:'+XWD_FULLNAME)
                if result is True:
                    answer = {'Success': 'Deleted'}
                else:
                    answer = {'Error': 'Failed to delete'}
                print(answer)
                return json.dumps(answer, separators=(',', ':'))
        if method == 'make_new_global_karma_slice':
            print('Attempting to make a new global Karma slice')
            try:
                result = SQLConnector.MakeNewGlobalKarmaSlice()
                if result is True:
                    return json.dumps({'Success': 'New global slice was created'}, separators=(',', ':'))
                else:
                    return json.dumps({'Error': 'Failed to invoke'}, separators=(',', ':'))
            except:
                return json.dumps({'Error': 'Failed to invoke'}, separators=(',', ':'))
        if method == 'get_bugs':
            try:  # zero title exception
                components_filer = request['component_filter[]']
            except:
                components_filer = []
            try:
                product_filter = request['product_filter[]']
            except:
                product_filter = []
            try:
                tbfi_filter = request['tbfi_filter[]']
            except:
                tbfi_filter = []
            try:
                start = request['start'][0]
                end = request['end'][0]
            except:
                return json.dumps({'Error': 'Bad request - start/end is incorrect'}, separators=(',', ':'))
            if int(start) > int(end):
                return json.dumps({'Error': 'Bad request - start > end'},
                                  separators=(',', ':'))
            result = SQLConnector.GetBugs(components_filer, product_filter, tbfi_filter, start, end)
            if len(result) != 0:
                answer = {
                    'error': 0,
                    'len': len(result),
                    'bugs': {}
                }
                for row in result:
                    regex = r"<component><name>(.[^<]*)</name></component>"
                    components = []
                    matches = re.finditer(regex, row.components, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            components.append(match.group(1))
                    answer['bugs'].update({row.page_title: {'bug_id': row.bug_id, 'product': row.product, 'tbfi': row.tbfi, 'components': components}})
                return json.dumps(answer, separators=(',', ':'))
            else:
                return json.dumps({'error': 'Nothing was found'}, separators=(',', ':'))

    except Exception as exception:
        print(exception)
        raise AssertionError(component="post_request_analyse",
                             message="Some error occurred, please, be nice and write some proper error handler :)".format(
                                 exception.message))


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


address = "SUP-A1631.AMUST.LOCAL", 8080
server = pywsgi.WSGIServer(address, server_logic)
server.backlog = 256
server.serve_forever()
