from gevent import pywsgi
from datetime import datetime
from gevent import monkey
import Configuration
from urllib.parse import parse_qs
from Mechanics import Page, SQLConnector, CustomLogging, MysqlConnector, PageCreator
import json
import pickle
import operator
import ctypes
import os
import subprocess
import uuid

is_admin = ctypes.windll.shell32.IsUserAnAdmin()
if is_admin != 1:
    print('You\'r no admin here!')
    exit()

monkey.patch_all()  # makes many blocking calls asynchronous
SQLConfig = Configuration.SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
CustomLogging = CustomLogging('NOT_silent')


def start_core_as_subprocess(dict_to_pickle: dict):
    print(dict_to_pickle)
    pickled_data = pickle.dumps(dict_to_pickle, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    print('---------sub process started-------------')
    subprocess.call("python C:/Projects/xWIKI_Karma/Comparer_core_v2_0.py INFO False -b" + temp_id, shell=True)


def post_request_analyse(request_body):
    request_body = request_body.decode("utf-8")
    request = parse_qs(request_body)
    try:
        method = request['method'][0]
    except:
        return json.dumps({'Error': 'Bad request - no method specified'}, separators=(',', ':'))
    try:
        if method == 'get_stat_by_title':
            page_id = None
            page_title = None
            try:  # zero title exception
                platform = request['platform'][0]
            except:
                return json.dumps({'Error': 'Bad request - no title or platform was provided'}, separators=(',', ':'))
            try:
                page_id = request['id'][0]
            except:
                print('may be it\'s an old logic?')
                print(request)
                try:
                    page_title = request['title'][0]
                except:
                    return json.dumps({'Error': 'Bad request - no title, id or platform was provided'},
                                      separators=(',', ':'))
            if page_title is not None:
               Current_Page = Page(request['title'][0], platform)
               temp_array = SQLConnector.GetPageSQLID_and_characters_total_by_title_and_platform(
                   Current_Page.page_title, Current_Page.page_platform)
            if page_id is not None and page_title is None:
                MySQLconfig_INSTANCE = Configuration.MySQLConfig()
                MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
                #print('page_title', page_title, 'page_id', page_id)
                XWD_FULLNAME = MysqlConnector_INSTANCE.get_XWD_FULLNAME(XWD_ID=page_id)
                if XWD_FULLNAME is None:
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with id "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer
                #print('XWD_FULLNAME', 'xwiki:'+XWD_FULLNAME, 'page_id', page_id, 'platform', platform)
                temp_array = SQLConnector.GetPageSQLID_and_characters_total_by_page_id_and_platform(
                    XWD_FULLNAME, platform)
                #print('temp_array', temp_array)
                if temp_array is None:  # page is unknown exception
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with ID "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer
                Current_Page = Page(XWD_FULLNAME, platform)

            if temp_array is None:  # page is unknown exception
                page_unknown_answer = json.dumps({
                                                     'Error': 'Bad request - there is no known page with title "' + Current_Page.page_title + '" in the database'},
                                                 separators=(',', ':'))
                return page_unknown_answer

            Current_Page.pageSQL_id = temp_array[0]
            Current_Page.TOTALCharacters = int(temp_array[1])
            Current_Page.TotalContribute = pickle.loads(SQLConnector.GetPagePageContribution(Current_Page))
            result = SQLConnector.GetPageKarmaAndVotes_byID(Current_Page.pageSQL_id)
            up_votes = result[0]
            down_votes = result[1]
            karma_score = result[2]
            if Current_Page.TOTALCharacters != 0:
                answer = {
                    'Error': 0,
                    'page_title': Current_Page.page_title,
                    'page_DB_id': Current_Page.pageSQL_id,
                    'up_votes': up_votes,
                    'down_votes': down_votes,
                    'page_karma_score': karma_score,
                    'contributors_percents': {}
                }
                for Contributor, Value in Current_Page.TotalContribute.items():
                    Percent = round(((Value / Current_Page.TOTALCharacters) * 100), 2)
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
            userID = SQLConnector.GetUserIDbyName(username)
            if userID is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            karma_score = round(SQLConnector.GetUserKarmaRawScore_byID(userID), 2)
            table = SQLConnector.GetUserRawKarmabyID(userID)
            answer = {
                        'Error': 0,
                      'user': username,
                      'userID': userID,
                      'karma_score': karma_score,
                      'raw_karma': {}
                      }
            for row in table:
                answer['raw_karma'].update({'"'+row.page_title+'"': row.percent})
            return json.dumps(answer, separators=(',', ':'))
        if method == 'vote_for_page_as_user': # need to re-write this function
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

            user_id = SQLConnector.GetUserIDbyName(user_name)
            #old or new logic
            if user_id is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            if page_title is not None:
               Current_Page = Page(page_title, platform)
               temp_array = SQLConnector.GetPageSQLID_and_characters_total_by_title_and_platform(
                   Current_Page.page_title, Current_Page.page_platform)
               if temp_array is None:  # page is unknown exception
                   page_unknown_answer = json.dumps({
                       'Error': 'Bad request - there is no known page with title "' + Current_Page.page_title + '" in the database'},
                       separators=(',', ':'))
                   return page_unknown_answer
            if page_id is not None and page_title is None:
                MySQLconfig_INSTANCE = Configuration.MySQLConfig()
                MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
                #print('page_title', page_title, 'page_id', page_id)
                XWD_FULLNAME = MysqlConnector_INSTANCE.get_XWD_FULLNAME(XWD_ID=page_id)
                if XWD_FULLNAME != None:
                    XWD_FULLNAME = XWD_FULLNAME#.decode('utf-8')
                else:
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with id "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer
                #print('XWD_FULLNAME', XWD_FULLNAME, 'page_id', page_id)
                temp_array = SQLConnector.GetPageSQLID_and_characters_total_by_page_id_and_platform(
                    XWD_FULLNAME, platform)
                #print('temp_array', temp_array)
                if temp_array is None:  # page is unknown exception
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with ID "' + page_id + '" in the database'},
                        separators=(',', ':'))
                    return page_unknown_answer
                Current_Page = Page(XWD_FULLNAME, platform)

            #print(temp_array[0], user_id, direction)
            result = SQLConnector.NewPageVote(temp_array[0], user_id, direction)
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
            userID = SQLConnector.GetUserIDbyName(username)
            if userID is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            karma_score = round(SQLConnector.GetUserKarmaScore_byID(userID), 2)
            answer = {
                        'Error': 0,
                      'user': username,
                      'userID': userID,
                      'karma_score': karma_score,
                      }
            return json.dumps(answer, separators=(',', ':'))
        if method == 'get_user_karma_current_score_detailed_by_user':
            try:  # zero title exception
                request['user'][0]
            except:
                return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
            username = request['user'][0]
            userID = SQLConnector.GetUserIDbyName(username)
            if userID is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            karma_score = round(SQLConnector.GetUserKarmaScore_byID(userID), 2)
            table = SQLConnector.GetUserKarmaDetailedScore_byID(userID)
            answer = {
                'Error': 0,
                'user': username,
                'userID': userID,
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
            userID = SQLConnector.GetUserIDbyName(username)
            if userID is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            result = SQLConnector.MakeNewKarmaSlice_byUserID(userID)
            if result == 'Karma wasn\'t changed':
                error = 406
                result == 'Karma wasn\'t changed since the last slice'
            else:
                error = 0
            answer = {
                'Error': error,
                'user': username,
                'userID': userID,
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
            userID = SQLConnector.GetUserIDbyName(username)
            if userID is None:
                return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
            result = SQLConnector.GetKarmaSlicesByUSERIDandDates(userID, date_start, date_end)
            answer = {
                'Error': 0,
                'user': username,
                'userID': userID,
                'result': {}
            }
            if DIRTY_HACK_FOR_Eugene is False:
                for score, change_time_epoch in result:
                    answer['result'].update({score:change_time_epoch})
            else:
                for score, change_time_epoch in result:
                    answer['result'].update({change_time_epoch:score})
            return json.dumps(answer, separators=(',', ':'))
        if method == 'reindex_page_by_title_or_id':
            page_id = None
            page_title = None
            try:  # zero title exception
                platform = request['platform'][0]
            except:
                return json.dumps({'Error': 'Bad request - no title or platform was provided'}, separators=(',', ':'))
            try:
                page_id = request['id'][0]
            except:
                print('may be it\'s an old logic?')
                print(request)
                try:
                    page_title = request['title'][0]
                except:
                    return json.dumps({'Error': 'Bad request - no title, id or platform was provided'},
                                      separators=(',', ':'))
            if page_title is not None:
                Current_Page = Page(request['title'][0], platform)
                temp_array = SQLConnector.GetPageSQLID_and_characters_total_by_title_and_platform(
                    Current_Page.page_title, Current_Page.page_platform)
            if page_id is not None and page_title is None:
                MySQLconfig_INSTANCE = Configuration.MySQLConfig()
                MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
                # print('page_title', page_title, 'page_id', page_id)
                XWD_FULLNAME = MysqlConnector_INSTANCE.get_XWD_FULLNAME(XWD_ID=page_id)
                if XWD_FULLNAME is None:
                    page_unknown_answer = json.dumps({
                        'Error': 'Bad request - there is no known page with id "' + page_id + '" in the xWiki database'},
                        separators=(',', ':'))
                    return page_unknown_answer
                # print('XWD_FULLNAME', 'xwiki:'+XWD_FULLNAME, 'page_id', page_id, 'platform', platform)
                dict_to_pickle = {XWD_FULLNAME: platform}
                start_core_as_subprocess(dict_to_pickle)
                answer = 'added to processing'
                return json.dumps(answer, separators=(',', ':'))

        else:
            return json.dumps({'Error': 'bad request - unknown method'}, separators=(',', ':'))


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
