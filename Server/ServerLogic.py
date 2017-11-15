import logging
import re
import json
import Configuration
import CustomModules.Mechanics as Mechanics
import CustomModules.SQL_Connector as SQL_Connector
import Server.PostExceptions as Exceptions
import pickle
import operator
from datetime import datetime, timedelta
import os
import subprocess
import uuid
from ldap3 import Server, Connection, ALL, NTLM, ObjectDef, Reader
import ldap3.core.exceptions as ldap3exceptions

class WebPostRequest:
    def __init__(self, mysql_config: Configuration.MySQLConfig, sql_config: Configuration.SQLConfig):
        self.mysql_connector_instance = Mechanics.MysqlConnector(mysql_config)
        self.sql_connector_instance = SQL_Connector.SQLConnector(sql_config)
        self.last_indexed_page = None
        self.re_index_timeout = 3  # sec

    def invoke(self, method: str, request: dict, requested_by_url: str):
        """Invokes proper method depending on request"""
        if method == 'get_stat_by_title':
            return self.get_stat_by_title(request=request, requested_by_url=requested_by_url)

        elif method == 'get_stat_by_user':
            return self.get_stat_by_user(request=request)

        elif method == 'vote_for_page_as_user':
            return self.vote_for_page_as_user(request=request)

        elif method == 'get_simple_votes':
            return self.get_simple_votes(request=request)

        elif method == 'simple_vote':
            return self.simple_vote(request=request)

        elif method == 'get_karma_score_global':
            return self.get_karma_score_global()

        elif method == 'get_karma_score_by_user':
            return self.get_karma_score_by_user(request=request)

        elif method == 'get_user_karma_current_score_detailed_by_user':
            return self.get_user_karma_current_score_detailed_by_user(request=request)

        elif method == 'make_new_karma_slice_by_user':
            return self.make_new_karma_slice_by_user(request=request)

        elif method == 'reindex_page_by_XWD_FULLNAME':
            return self.reindex_page_by_xwd_fullname(request=request)

        elif method == 'delete_page_by_XWD_FULLNAME':
            return self.delete_page_by_xwd_fullname(request=request)

        elif method == 'make_new_global_karma_slice':
            return self.make_new_global_karma_slice()

        elif method == 'get_bugs':
            return self.get_bugs(request=request)

        elif method == 'get_bugs_form_content':
            return self.get_bugs_form_content()
        else:
            raise Exceptions.MethodNotSupported(message='WebPostRequest has no requested method', arguments={'requested method': method})

    def get_stat_by_title(self, request: dict, requested_by_url: str)->str:
        logger = logging.getLogger()
        try:
            platform = request['platform'][0]
            page_id = request['id'][0]
            user = request['user'][0]
        except KeyError as error:
            raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
        xwd_fullname = self.mysql_connector_instance.get_XWD_FULLNAME(XWD_ID=page_id)
        if xwd_fullname is None:
            self.register_web_request('NULL', user, page_id, requested_by_url, 'Cannot find xwd_fullname of page by the requested XWD_ID')
            raise Exceptions.BadRequestException('BadRequest',
                                                 {'Cannot find xwd_fullname of page by the requested XWD_ID:': page_id})
        temp_array = self.sql_connector_instance.select_id_characters_total_from_dbo_knownpages(
            page_id=xwd_fullname, platform=platform)
        if temp_array is None:
            self.register_web_request('NULL', user, page_id, requested_by_url,
                                      'Cannot find a page in database with the requested page_id')
            raise Exceptions.BadRequestException('BadRequest',
                                                 {'Cannot find a page in database with the requested page_id:': xwd_fullname})
        sql_id_of_requested_page = temp_array[0]
        total_characters_of_requested_page = int(temp_array[1])
        total_contribute_of_requested_page = pickle.loads(
            self.sql_connector_instance.select_datagram_contribution_from_dbo_knownpages_contribution(
                sql_id=sql_id_of_requested_page))
        result = self.sql_connector_instance.exec_get_page_karma_and_votes(page_id=sql_id_of_requested_page)
        up_votes = result[0]
        down_votes = result[1]
        karma_score = result[2]
        if total_characters_of_requested_page != 0:
            answer = {
                'Error': 0,
                'page_title': xwd_fullname,
                'page_DB_id': sql_id_of_requested_page,
                'up_votes': up_votes,
                'down_votes': down_votes,
                'page_karma_score': karma_score,
                'contributors_percents': {}
            }
            for Contributor, Value in total_contribute_of_requested_page.items():
                percent = round(((Value / total_characters_of_requested_page) * 100), 2)
                answer['contributors_percents'].update({Contributor: percent})
            contributors_percents_sorted = sorted(answer['contributors_percents'].items(),
                                                  key=operator.itemgetter(1), reverse=True)
            answer['contributors_percents'] = {}
            for unit in contributors_percents_sorted[:3]:
                answer['contributors_percents'].update({unit[0]: unit[1]})
        else:
            self.register_web_request(sql_id_of_requested_page, user, page_id, requested_by_url,
                                      'Requested page has 0 length content')
            raise Exceptions.EmptyPage('EmptyPage',
                                                 {'Requested page has 0 length content': xwd_fullname})
        result = self.valid_answer(answer)
        self.register_web_request(sql_id_of_requested_page, user, page_id, requested_by_url,
                                  'OK')
        return result

    def get_stat_by_user(self, request: dict)->str:
        try:
            user_name = request['user'][0]
        except KeyError as error:
            raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
        user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
        if user_id is None:
            raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
        karma_score = round(self.sql_connector_instance.exec_get_user_karma_raw_score(user_id=user_id), 2)
        table = self.sql_connector_instance.exec_get_user_karma_raw(user_id=user_id)
        answer = {
            'error': 0,
            'user': user_name,
            'user_id': user_id,
            'karma_score': karma_score,
            'raw_karma': {}
        }
        for row in table:
            answer['raw_karma'].update({'"' + row.page_title + '"': row.percent})
        return self.valid_answer(answer)

    def vote_for_page_as_user(self, request: dict)->str:
            try:
                user_name = request['user_name'][0]
                direction = request['direction'][0]
                platform = request['platform'][0]
                page_id = request['id'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
            user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
            if user_id is None:
                raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
            xwd_fullname = self.mysql_connector_instance.get_XWD_FULLNAME(XWD_ID=page_id)
            if xwd_fullname is None:
                raise Exceptions.BadRequestException('BadRequest', {'Cannot find xwd_fullname of page by the requested XWD_ID:': page_id})
            temp_array = self.sql_connector_instance.select_id_characters_total_from_dbo_knownpages(
                page_id=xwd_fullname, platform=platform)
            if temp_array is None:  # page is unknown exception
                raise Exceptions.BadRequestException('BadRequest',
                                                     {'Cannot find page in database with the requested page_id:': page_id})
            result = self.sql_connector_instance.insert_into_dbo_page_karma_votes(sql_id=temp_array[0], user_id=user_id, direction=direction)
            if result.startswith('Error'):
                error = result
                result = 'Already voted'
            else:
                error = 0
            answer = {
                'Error': error,
                'result': result,
            }
            return self.valid_answer(answer)

    def simple_vote(self, request: dict)->str:
            logger = logging.getLogger()
            try:
                user_name = request['user_name'][0]
                direction = request['direction'][0]
                seed = request['seed'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
            logger.debug('seed: ' + seed)
            user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
            if user_id is None:
                raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
            result = self.sql_connector_instance.simple_vote(seed=seed, user_id=user_id, direction=direction)
            if result.startswith('Error'):
                error = result
                result = 'Already voted'
            else:
                error = 0
            answer = {
                'Error': error,
                'result': result,
            }
            return self.valid_answer(answer)

    def get_simple_votes(self, request: dict)->str:
            try:
                seed = request['seed'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
            result = self.sql_connector_instance.exec_get_simple_votes(seed=seed)
            if result is None:
                error = result
                result = 'Please, contact xWiki admin.'
            else:
                error = 0
            answer = {
                'Error': error,
                'result': result,
            }
            return self.valid_answer(answer)

    def get_karma_score_by_user(self, request: dict)->str:
            try:
                user_name = request['user'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
            user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
            if user_id is None:
                raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
            karma_score = round(self.sql_connector_instance.exec_get_user_karma_current_score(user_id), 2)
            answer = {
                      'Error': 0,
                      'user': user_name,
                      'user_id': user_id,
                      'karma_score': karma_score,
                      }
            return self.valid_answer(answer)

    def get_karma_score_global(self)->str:
        answer = {
            'Error': 0,
            'result': {},
            'len': 0
        }
        result = self.sql_connector_instance.exec_get_user_karma_current_score_global()
        if result is None:
            raise Exceptions.KarmaInvokeFailure('InvokeFailed', {'exec_get_user_karma_current_score_global': 'with no arguments'})
        for user, score in result:
            karma_score = round(score, 2)
            answer['result'].update({user: karma_score})
        answer['len'] = len(result)
        return self.valid_answer(answer)

    def get_user_karma_current_score_detailed_by_user(self, request: dict)->str:
            try:
                user_name = request['user'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest',
                                                     {'Missing 1 required positional argument': str(error)})
            user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
            if user_id is None:
                raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
            karma_score = round(self.sql_connector_instance.exec_get_user_karma_current_score(user_id=user_id), 2)
            table = self.sql_connector_instance.exec_get_user_karma_current_score_detailed(user_id=user_id)
            answer = {
                'error': 0,
                'user': user_name,
                'user_id': user_id,
                'karma_score': karma_score,
                'detailed_karma_score': {}
            }
            for row in table:
                vote_stat_dict = {
                    'result': row.result,
                    'up': row.up,
                    'down': row.down,
                    'gained_karma': round(row.added_to_karma, 2),
                    'page_id': row.page_id
                 }
                answer['detailed_karma_score'].update({'"'+row.page_title+'"': vote_stat_dict})
            return self.valid_answer(answer)

    def make_new_karma_slice_by_user(self, request: dict)->str:
            try:
                user_name = request['user'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest',
                                                     {'Missing 1 required positional argument': str(error)})
            user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
            if user_id is None:
                raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
            result = self.sql_connector_instance.exec_make_new_karma_slice(user_id=user_id)
            if result == 'Karma wasn\'t changed':
                error = 406
            elif result == 'Karma wasn\'t changed since the last slice':
                error = 401
            else:
                error = 0
            answer = {
                'error': error,
                'user': user_name,
                'user_id': user_id,
                'result': result
            }
            return self.valid_answer(answer)

    def reindex_page_by_xwd_fullname(self, request: dict)->str:
            allowed_tdelta = timedelta(seconds=self.re_index_timeout)
            if self.last_indexed_page is None:
                self.last_indexed_page = [None, datetime.now()]
            try:
                platform = request['platform'][0]
                xwd_fullname = request['XWD_FULLNAME'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest',
                                                     {'Missing 1 required positional argument': str(error)})
            # Analyze of xwd_fullname
            if not str(xwd_fullname).lower().startswith('main') and not str(xwd_fullname).lower().startswith('staging'):
                raise Exceptions.DeprecatedPage('DeprecatedPage', {'Indexing of non-main and non-staging pages using this request is not allowed': xwd_fullname})
            if xwd_fullname.lower() == 'stagingwiki.webhome' or xwd_fullname.lower() == 'main.webhome' or xwd_fullname.lower() == 'stagingwiki.personal spaces%' or xwd_fullname.lower().endswith('.webpreferences'):
                raise Exceptions.DeprecatedPage('DeprecatedPage', {'Indexing of page you requested is deprecated': xwd_fullname})
            dict_to_pickle = {xwd_fullname: platform}
            if self.last_indexed_page[0] == xwd_fullname and (datetime.now()-self.last_indexed_page[1]) < allowed_tdelta:
                raise Exceptions.IndexingTimeOut('IndexingTimeOut', {'Indexing request for the same page before ' + str(self.re_index_timeout) + ' sec. Sec to wait: ': datetime.now()-self.last_indexed_page[1]})
            else:
                self.last_indexed_page = [xwd_fullname, datetime.now()]
            result = start_core_as_subprocess(dict_to_pickle)
            if result is True:
                answer = {'Success': 'Added to processing'}
            else:
                raise Exceptions.IndexingFailure('IndexingFailure', {'Failed to add to processing': dict_to_pickle})
            return self.valid_answer(answer)

    def delete_page_by_xwd_fullname(self, request: dict)->str:
            try:
                xwd_fullname = request['XWD_FULLNAME'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest',
                                                     {'Missing 1 required positional argument': str(error)})
            if xwd_fullname == '[\'null\']':
                raise Exceptions.BadRequestException('BadRequest',
                                                     {'xwd_fullname is Null': xwd_fullname})
            if xwd_fullname is not None:
                result = self.sql_connector_instance.exec_delete_page_by_page_id('xwiki:' + xwd_fullname)
                if result is True:
                    answer = {'Success': 'Deleted'}
                else:
                    raise Exceptions.PageDeleteFailure('PageDeleteFailure',
                                                     {'Unable to delete page from DB': xwd_fullname})
                return self.valid_answer(answer)

    def make_new_global_karma_slice(self)->str:
            result = self.sql_connector_instance.exec_make_new_global_karma_slice()
            if result is True:
                answer = {'Success': 'New global slice was created'}
                return self.valid_answer(answer)
            else:
                raise Exceptions.KarmaInvokeFailure('InvokeFailed', {'exec_make_new_global_karma_slice': 'with no arguments'})

    def get_bugs(self, request: dict)->str:
            try:  # zero title exception
                components_filer = request['component_filter[]']
            except KeyError:
                components_filer = []
            try:
                product_filter = request['product_filter[]']
            except KeyError:
                product_filter = []
            try:
                tbfi_filter = request['tbfi_filter[]']
            except KeyError:
                tbfi_filter = []
            try:
                start = request['start'][0]
                end = request['end'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
            if int(start) > int(end):
                raise Exceptions.BadRequestException('BadRequest', {'start > end': str(start) + '>' + str(end)})
            result = self.sql_connector_instance.select_from_known_bugs_by_filter(components_filer, product_filter, tbfi_filter, start, end)
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
                    answer['bugs'].update({row.RowNumber: {'bug_id': row.bug_id, 'title': row.page_title, 'product': row.product, 'tbfi': row.tbfi, 'components': components, 'path': row.page_id}})
                return self.valid_answer(answer)
            else:
                raise Exceptions.NothingFound('NothingFound', {'Query:': [components_filer, product_filter, tbfi_filter, start, end]})

    def get_bugs_form_content(self) -> str:
        try:
            products = self.sql_connector_instance.select_distinct_product_from_dbo_known_bugs()
            tbfis = self.sql_connector_instance.select_distinct_tbfi_from_dbo_known_bugs()
            components = self.sql_connector_instance.select_distinct_components_from_dbo_known_bugs()
            answer = {
                'error': 0,
                'products': products,
                'tbfi': tbfis,
                'components': components,
            }
            return self.valid_answer(answer)
        except Exception as error:
            raise Exceptions.NothingFound('Unable to get distincts from SQL',
                                          {'error:': error})

    def error_answer(self, description: str)->str:
        content = {
            'error': 1,
            'description': description
        }
        return json.dumps(content)

    def valid_answer(self, content: dict)->str:
        return json.dumps(content)

    def register_web_request(self, known_page_id: str, user_id: str, source_platform_id: str, requested_url: str, result: str):
        # logging the request in sql
        logger = logging.getLogger()
        try:
            register_web_request = self.sql_connector_instance.insert_into_dbo_web_requests(
                known_page_id=known_page_id, user_id=user_id, source_platform_id=source_platform_id,
                requested_url=requested_url, result=result)
            if register_web_request is False:
                logger.error(
                    'Unable to register a request: ' + 'known_page_id=' + known_page_id + ' user_id=' + user_id + ' source_platform_id=' + source_platform_id + ' requested_url=' + requested_url + ' result=' + result)
            else:
                logger.debug('New web request was added into DB')
        except Exception as error:
            logger.error(
                'Unable to register a request, insert failed with the following error:' + error)
            pass


def start_core_as_subprocess(dict_to_pickle: dict):
    try:
        locality = Configuration.Integration()
        pickled_data = pickle.dumps(dict_to_pickle, 0)
        pickled_and_decoded_dict = pickled_data.decode('latin1')
        temp_id = str(uuid.uuid4())
        os.environ[temp_id] = pickled_and_decoded_dict
        print('---------sub process started-------------')
        subprocess.call("python " + str(locality.cc_path)+"CCv2.1.py INFO True -b" + temp_id, shell=True)
        return True
    except:
        return False


def get_ad_host_description(connection_to_ldap,  requested_hostname: str) -> str:
    logger = logging.getLogger('root')
    try:
        # print('Connected to', connection_to_ldap, 'as', connection_to_ldap.extend.standard.who_am_i())
        obj_computer = ObjectDef('computer', connection_to_ldap)
        r = Reader(connection_to_ldap, obj_computer, 'OU=User Computers,DC=amust,DC=local',
                   '(&(objectCategory=computer)(name=' + requested_hostname + '))')
        r.search()
        comp_description = r[0].Description
        return str(comp_description)
    except Exception as error:
        logger.error('An error occurred:' + error)
        return 'unknown'

