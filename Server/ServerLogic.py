import logging
import copy
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
        self.veeam_versions_inst = Configuration.VeeamVersions()
        self.versions_dict = self.veeam_versions_inst.versions_dict
        self.next_VBR_version = self.veeam_versions_inst.next_version
        self.logger = logging.getLogger()

    def log_request_to_db(self, method: str, request: dict):
        if method == 'vote_for_page_as_user':
            xwd_fullname = self.mysql_connector_instance.get_XWD_FULLNAME(XWD_ID=request['id'][0])
            direction = int(request['direction'][0])
            user_name = str(request['user_name'][0]).replace('XWiki.', '')
            link = xwd_fullname_to_link(xwd_fullname)
            token_id = self.sql_connector_instance.insert_into_dbo_webrequests_vote_for_page_as_user(xwd_fullname, direction, user_name, link)
            return token_id
        elif method == 'reindex_page_by_XWD_FULLNAME':
            xwd_fullname = request['XWD_FULLNAME'][0]
            link = xwd_fullname_to_link(xwd_fullname)
            token_id = self.sql_connector_instance.insert_into_dbo_webrequests_reindex_page_by_xwd_fullname(xwd_fullname, link)
            return token_id
        elif method == 'delete_page_by_XWD_FULLNAME':
            xwd_fullname = request['XWD_FULLNAME'][0]
            link = xwd_fullname_to_link(xwd_fullname)
            token_id = self.sql_connector_instance.insert_into_dbo_webrequests_delete_page_by_xwd_fullname(xwd_fullname, link)
            return token_id

    def invoke(self, method: str, request: dict, requested_by_url: str):
        """Invokes proper method depending on request"""
        if method == 'get_stat_by_title':
            return self.get_stat_by_title(request=request, requested_by_url=requested_by_url)

        elif method == 'get_stat_by_user':
            return self.get_stat_by_user(request=request)

        elif method == 'vote_for_page_as_user':
            return self.vote_for_page_as_user(request=request, token=self.log_request_to_db(method=method, request=request))

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
            return self.reindex_page_by_xwd_fullname(request=request, token=self.log_request_to_db(method=method, request=request))

        elif method == 'delete_page_by_XWD_FULLNAME':
            return self.delete_page_by_xwd_fullname(request=request, token=self.log_request_to_db(method=method, request=request))

        elif method == 'make_new_global_karma_slice':
            return self.make_new_global_karma_slice()

        elif method == 'get_bugs':
            return self.get_bugs(request=request)

        elif method == 'get_karma_slices_by_user_and_dates':
            return self.get_karma_slices_by_user_and_dates(request=request)

        elif method == 'get_bugs_form_content':
            return self.get_bugs_form_content()

        elif method == 'get_karma_diff_by_user_between_two_dates':
            return self.get_karma_diff_by_user_between_two_dates(request=request)

        elif method == 'check_if_bug_exists':
            return self.check_if_bug_exists(request=request)

        elif method == 'get_bugs_form_content_by_product':
            return self.get_bugs_form_content_by_product()

        elif method == 'get_bugs_form_content_dynamic':
            return self.get_bugs_form_content_dynamic()

        else:
            raise Exceptions.MethodNotSupported(message='WebPostRequest has no requested method', arguments={'requested method': method})

    def get_karma_slices_by_user_and_dates(self, request: dict)->str:
        try:
            username = request['user'][0]
            date_start = request['date_start'][0]
            date_end = request['date_end'][0]
        except KeyError as error:
            raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
        try:
            reverse_array = request['reverse_array'][0]
            d_i_r_t_y__h_a_c_k__f_o_r__eugene = True
        except KeyError as error:
            d_i_r_t_y__h_a_c_k__f_o_r__eugene = False
        try:
            date_start = datetime.strptime(date_start, '%d-%m-%Y')
            date_end = datetime.strptime(date_end, '%d-%m-%Y')
        except ValueError as error:
            raise Exceptions.BadRequestException('BadRequest',
                                                 {'Date cannot be recognised. Please, use day-month-year format, example: 31-01-1991'})
        if date_start > date_end:
            raise Exceptions.BadRequestException('BadRequest',
                                                 {'date_start > date_end'})
        elif date_start == date_end:
            raise Exceptions.BadRequestException('BadRequest',
                                                 {'date_start = date_end'})
        user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=username)
        if user_id is None:
            return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
        result = self.sql_connector_instance.select_karma_score_from_userkarma_slice(user_id, date_start, date_end)
        answer = {
            'Error': 0,
            'user': username,
            'user_id': user_id,
            'result': {}
        }
        if d_i_r_t_y__h_a_c_k__f_o_r__eugene is False:
            for score, change_time_epoch in result:
                answer['result'].update({score: change_time_epoch})
        else:
            for score, change_time_epoch in result:
                answer['result'].update({change_time_epoch: score})
        return self.valid_answer(answer)

    def get_karma_diff_by_user_between_two_dates(self, request: dict)->str:
        try:
            username = request['user'][0]
            date_start = request['date_start'][0]
            date_end = request['date_end'][0]
        except KeyError as error:
            raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
        try:
            date_start = datetime.strptime(date_start, '%d-%m-%Y')
            date_end = datetime.strptime(date_end, '%d-%m-%Y')
        except ValueError as error:
            raise Exceptions.BadRequestException('BadRequest',
                                                 {
                                                 'Date cannot be recognised. Please, use day-month-year format, example: 31-01-1991'})
        if date_start > date_end:
            raise Exceptions.BadRequestException('BadRequest',
                                                 {'date_start > date_end'})
        elif date_start == date_end:
            raise Exceptions.BadRequestException('BadRequest',
                                                 {'date_start = date_end'})
        user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=username)
        if user_id is None:
            return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
        result = self.sql_connector_instance.select_karma_diff_between_dates(user_id, date_start, date_end)
        if result is None:
            return self.error_answer('Only 1 Karma slice was found for the requested user, which isn\'t enough to calculate a diff')
        answer = {
            'Error': 0,
            'user': username,
            'user_id': user_id,
            'result': round(result[1], 2)
        }
        return self.valid_answer(answer)

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

    def vote_for_page_as_user(self, request: dict, token)->str:
            try:
                user_name = request['user_name'][0]
                direction = request['direction'][0]
                platform = request['platform'][0]
                page_id = request['id'][0]
            except KeyError as error:
                raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
            user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
            if user_id is None:
                # raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
                user_id = self.sql_connector_instance.insert_into_dbo_knownpages_users(user_name)
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
                self.sql_connector_instance.update_dbo_webrequests_vote_for_page_as_user(token_id=token, result=False)
            else:
                error = 0
                self.sql_connector_instance.update_dbo_webrequests_vote_for_page_as_user(token_id=token, result=True)
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
            logger.info('seed: ' + seed)
            seed = seed.replace('%22', '"')
            user_id = self.sql_connector_instance.select_id_from_dbo_knownpages_users(username=user_name)
            if user_id is None:
                # raise Exceptions.BadRequestException('BadRequest', {'Cannot find id of user': user_name})
                user_id = self.sql_connector_instance.insert_into_dbo_knownpages_users(user_name)
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
            seed = seed.replace('%22', '"')
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

    def reindex_page_by_xwd_fullname(self, request: dict, token)->str:
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
                raise Exceptions.DeprecatedPage('DeprecatedPage', {'Indexing of non-main/non-staging pages using this request is not allowed': xwd_fullname})
            if xwd_fullname.lower() == 'stagingwiki.webhome' or xwd_fullname.lower() == 'main.webhome' or xwd_fullname.lower().startswith('stagingwiki.personal spaces') or xwd_fullname.lower().endswith('.webpreferences'):
                raise Exceptions.DeprecatedPage('DeprecatedPage', {'Indexing of page you requested is deprecated': xwd_fullname})
            if xwd_fullname.lower().startswith('main.internal technical docs.veeam one.veeam-one\:-database'):
                raise Exceptions.DeprecatedPage('DeprecatedPage', {'Indexing of page "%veeam-one\:-database%" is deprecated': xwd_fullname})
            dict_to_pickle = {xwd_fullname: platform}
            if self.last_indexed_page[0] == xwd_fullname and (datetime.now()-self.last_indexed_page[1]) < allowed_tdelta:
                raise Exceptions.IndexingTimeOut('IndexingTimeOut', {'Indexing request for the same page before ' + str(self.re_index_timeout) + ' sec.'})
            else:
                self.last_indexed_page = [xwd_fullname, datetime.now()]
            result = start_core_as_subprocess(dict_to_pickle, token)
            if result is True:
                answer = {'Success': 'Added to processing'}
            else:
                raise Exceptions.IndexingFailure('IndexingFailure', {'Failed to add to processing': dict_to_pickle})
            return self.valid_answer(answer)

    def delete_page_by_xwd_fullname(self, request: dict, token: str)->str:
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
                    logger = logging.getLogger()
                    logger.debug('Deleting page, result is: ' + str(result))
                    self.sql_connector_instance.update_dbo_webrequests_delete_page_by_xwd_fullname(token_id=token,
                                                                                             result=True)
                    answer = {'Success': 'Deleted'}
                else:
                    self.sql_connector_instance.update_dbo_webrequests_delete_page_by_xwd_fullname(token_id=token,
                                                                                                   result=False)
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
            if tbfi_filter == [] and components_filer == [] and product_filter == []:
                raise Exceptions.BadRequestException('BadRequest',
                                                     {'Please specify at least 1 value'})

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
                    page_path = str(row.page_id)
                    if page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.VBR.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.VBR.', 'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/VBR/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI.', 'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Migrated%20from%20mediaWIKI/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam VBO.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam VBO.',
                                                      'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20VBO/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam ONE.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam ONE.',
                                                      'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20ONE/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Linux.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Linux.',
                                                      'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Agent%20for%20Linux/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.2\.1.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.2\.1.',
                                                      'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Agent%20for%20Microsoft%20Windows/2.1/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.2\.0.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.2\.0.',
                                                      'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Agent%20for%20Microsoft%20Windows/2.0/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.',
                                                      'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Agent%20for%20Microsoft%20Windows/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.VAW.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.VAW.',
                                                  'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/VAW/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.VMP.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.VMP.',
                                                  'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/VMP/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Backup for Office365.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Backup for Office365.',
                                                  'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Backup%20for%20Office365/')
                    elif page_path.startswith('xwiki:Main.Bugs and Fixes.Found Bugs.vac.'):
                        page_path = page_path.replace('xwiki:Main.Bugs and Fixes.Found Bugs.vac.',
                                                  'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/vac/')

                    if page_path.endswith('.WebHome'):
                        page_path = page_path.replace('.WebHome', '')

                    # adding TFS bug state
                    fixed_in_ga_build = None
                    # SQL_DB_ID = self.sql_connector_instance.select_id_from_knownbugs(row.bug_id)
                    sql_db_bug_record_id = row.id
                    if sql_db_bug_record_id is not None:
                        logging_inst = logging.getLogger()
                        logging_inst.debug('Searching for GA build....')
                        state, status = self.sql_connector_instance.select_state_status_from_knownbugs_fts_state(knownbug_id=sql_db_bug_record_id)
                        # suppressing states to true or false
                        if state is None:
                            state = 'INTERNAL ERROR'
                            status = 'INTERNAL ERROR'
                        elif state == 'Finished' or state == 'In Inspecting' or state == 'Fixed':
                            state = 'Fixed'
                            try:
                                if not page_path.startswith('http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Agent%20for%20Linux/'):
                                    logging_inst.debug('invoking find_ga_build, vars:' + str(sql_db_bug_record_id))
                                    fixed_in_ga_build = self.find_ga_build(self.sql_connector_instance.select_build_from_knownbugs_fts_state(knownbug_id=sql_db_bug_record_id))
                                else:
                                    fixed_in_ga_build = self.sql_connector_instance.select_build_from_knownbugs_fts_state(knownbug_id=sql_db_bug_record_id)
                            except Exception:
                                fixed_in_ga_build = 'INTERNAL ERROR'
                        else:
                            state = 'Not Fixed'
                    else:
                        state = 'INTERNAL ERROR'
                        status = 'INTERNAL ERROR'
                    answer['bugs'].update({row.RowNumber: {'bug_id': row.bug_id,
                                                           'title': row.page_title,
                                                           'product': row.product,
                                                           'tbfi': row.tbfi,
                                                           'components': components,
                                                           'path': page_path,
                                                           'state': state,
                                                           'fixed_in_build': fixed_in_ga_build,
                                                           'status': status,
                                                           'added_date': str(row.added_to_wiki),
                                                           'added_by': row.added_by}})
                return self.valid_answer(answer)
            else:
                # raise Exceptions.NothingFound('NothingFound', {'Query:': [components_filer, product_filter, tbfi_filter, start, end]})
                raise Exceptions.NothingFound('NothingFound', {'Reason': 'please, simplify your request'})  # previous fine desc was removed by MC request

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

    def get_bugs_form_content_by_product(self) -> str:
        try:
            products = self.sql_connector_instance.select_distinct_product_from_dbo_known_bugs()
            tbfis = self.sql_connector_instance.select_distinct_tbfi_from_dbo_known_bugs()
            components = self.sql_connector_instance.select_distinct_components_by_product_from_dbo_known_bugs()
            answer = {
                'error': 0,
                'products': products,
                'tbfi': tbfis,
                'components_by_products': components,
            }
            return self.valid_answer(answer)
        except Exception as error:
            raise Exceptions.NothingFound('Unable to get distincts from SQL',
                                          {'error:': error})

    def get_bugs_form_content_dynamic(self) -> str:
        try:
            products = self.sql_connector_instance.select_dynamic_dbo_known_bugs()
            answer = {
                'error': 0,
                'products': products,
            }
            return self.valid_answer(answer)
        except Exception as error:
            raise Exceptions.NothingFound('Unable to get distincts from SQL',
                                          {'error:': error})

    def check_if_bug_exists(self, request: dict)-> str:
        try:  # zero title exception
            bug_id = request['bug_id']
        except KeyError as error:
            raise Exceptions.BadRequestException('BadRequest', {'Missing 1 required positional argument': str(error)})
        result = self.sql_connector_instance.select_count_id_from_knownbugs(bug_id)
        if result is True:
            answer = {
                'error': 0,
                'exist': 1
            }
            return self.valid_answer(answer)
        elif result is False:
            answer = {
                'error': 0,
                'exist': 0
            }
            return self.valid_answer(answer)
        else:
            raise Exceptions.NothingFound('NothingFound', {
                'Reason': 'Please, contact admin'})

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

    def find_ga_build(self, build_to_compare: str) -> str:
        build_major = build_to_compare[:3]
        regex = r".*\.(.*)"
        matches = re.match(regex, build_to_compare)
        try:
            build_minor = int(matches.group(1))
        except ValueError:
            match_with_no_str = re.sub('[^0-9]', '', matches.group(1))
            build_minor = int(match_with_no_str)
        if int(build_major[:1]) > 1:
            try:
                selected_build_versions = self.versions_dict[build_major]
                selected_build_versions = filter(lambda x: int(x) >= int(build_minor), selected_build_versions)
                minor_build_prod = min(selected_build_versions, key=lambda x: (int(x) - build_minor))
                result = build_major + '.0.' + minor_build_prod
            except KeyError as error:
                # logically shown if submitted build is > current Veeam version
                #result = build_to_compare
                result = self.next_VBR_version
            except ValueError:
                result = self.next_VBR_version
            return result
        else:
            return build_to_compare


def start_core_as_subprocess(dict_to_pickle: dict, token: str):
    logger = logging.getLogger()
    #try:
    locality = Configuration.Integration()
    pickled_data = pickle.dumps(dict_to_pickle, 0)
    pickled_and_decoded_dict = pickled_data.decode('latin1')
    temp_id = str(uuid.uuid4())
    os.environ[temp_id] = pickled_and_decoded_dict
    logger.info('Subprocess started ' + str(locality.cc_path)+'CCv2_1.py on "' + str(list(dict_to_pickle)[0]) + '"')
    call_str = "python " + str(locality.cc_path)+"CCv2_1.py INFO True " + str(token) + " -b " + temp_id
    logger.info(call_str)
    subprocess.call(call_str, shell=True)
    return True
    #except Exception as error:
    #    logger.error('An Exception occured while starting of CC core: ' + str(error))
    #    return False


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


def xwd_fullname_to_link(xwd_fullname: str) -> str:
    xwd_fullname = xwd_fullname.replace('\\.', '$dot_hack$')
    xwd_fullname_array = xwd_fullname.split('.')
    xwd_fullname_array_copy = copy.deepcopy(xwd_fullname_array)
    for idx, val in enumerate(xwd_fullname_array_copy):
        if '$dot_hack$' in val:
            xwd_fullname_array[idx]=xwd_fullname_array[idx].replace('$dot_hack$', '.')
    try:
        xwd_fullname_array.remove('WebHome')
    except:
        pass
    url = 'http://xwiki.support2.veeam.local/bin/view'
    for val in xwd_fullname_array:
        url = url + '/' + val
    return url
