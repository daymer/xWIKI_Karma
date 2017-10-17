import logging
import copy
import difflib
import hashlib
import re
import sys
import traceback
from datetime import datetime

import mysql.connector
import requests
from PythonConfluenceAPI import \
    ConfluenceAPI  # http://htmlpreview.github.io/?https://github.com/pushrodtechnology/PythonConfluenceAPI/blob/master/doc/html/index.html
from mwclient import Site

import Configuration


sys.setrecursionlimit(10 ** 6)


class PageCreator:
    def __init__(self, ConfluenceConfig, MediaWIKIConfig, xWikiConfig):
        self.confluenceAPI = ConfluenceAPI(ConfluenceConfig.USER, ConfluenceConfig.PASS, ConfluenceConfig.ULR)
        self.MediaWikiAPI_instance = Site((MediaWIKIConfig.Protocol, MediaWIKIConfig.URL), path=MediaWIKIConfig.APIPath,
                                          clients_useragent=MediaWIKIConfig.UserAgent)
        self.xWikiSpaces = xWikiConfig.spaces
        self.xWikiAPI = XWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
        self.current_mediaWiki_page = None
        self.current_version_to_versionID = []
        self.current_xWiki_page = None
        self.current_version_to_xWikiVersion = {}
        self.TotalExcluded = 0

    def create_new_page_by_title_and_platform(self, title, platform):
        if platform == 'Confluence':
            new_created_page = Page(title, platform)
            return new_created_page
        elif platform == 'MediaWIKI':
            current_page = self.MediaWikiAPI_instance.Pages[title]
            if current_page.redirect:
                # print('redirect, skipping...')
                return None
            else:
                all_page_text = current_page.text()
                if not all_page_text:
                    # print('ERROR: Page has no text or not exists, skipping.')
                    return None
                else:
                    new_created_page = Page(title, platform)
                    return new_created_page
        elif platform.lower() == 'xwiki':
            if title.endswith('.WebHome'):
                replaced_title = title.replace('.WebHome', '')
                replaced_title = replaced_title.replace('\\.', '<dirtyhack>')
            else:
                replaced_title = title.replace('\\.', '<dirtyhack>')
            array = replaced_title.split('.')
            path_array = []
            for each in array:
                path_array.append(each.replace('<dirtyhack>', '\\.'))
            page = path_array.pop(-1)
            space = path_array.pop(0)
            current_page = self.xWikiAPI.page(space=space, page=page, nested_space=path_array)
            if current_page is not None:
                self.current_xWiki_page = current_page
                try:
                    title = self.current_xWiki_page['title']
                except:
                    title = self.current_xWiki_page['pageSummaries'][0]['title']
                try:
                    self.current_xWiki_page['content']
                except:
                    print('no content was found')
                    return None
                new_created_page = Page(title, platform, page_xWIKI_nested_space=path_array, page_xWIKI_page=page,
                                        page_xWIKI_space=space)
                return new_created_page
            elif current_page is None:
                return None

    def collect_page_id(self, page):
        # print(page.page_platform)
        if page.page_platform == 'Confluence':
            page_content = self.confluenceAPI.get_content(content_type='page', title=page.page_title)
            try:
                page_id = page_content['results'][0]['id']
                return page_id
            except IndexError:
                print('404 - page with such name wasn\'t found')
                return None
        elif page.page_platform == 'MediaWIKI':
            self.current_mediaWiki_page = self.MediaWikiAPI_instance.Pages[page.page_title]
            return self.current_mediaWiki_page.pageid
        elif page.page_platform.lower() == 'xwiki':
            # print(self.current_xWiki_page)
            return self.current_xWiki_page['id']

    def collect_page_history(self, page):
        if page.page_platform == 'Confluence':
            page_history = self.confluenceAPI.get_content_history_by_id(page.page_id)
            page_versions = page_history['lastUpdated']['number']
            return page_versions
        elif page.page_platform == 'MediaWIKI':
            # dirty hack, but mwclient.listings.List has no methods to calc versions
            # also here we compare version number with version ID
            self.current_version_to_versionID[:] = []
            for revision in self.current_mediaWiki_page.revisions():
                self.current_version_to_versionID.append([revision['revid'], revision['parentid']])
            self.current_version_to_versionID = sorted(self.current_version_to_versionID)
            return len(self.current_version_to_versionID)
        elif page.page_platform == 'xWIKI':
            # response = self.xWikiAPI.get_page_history(self.current_xWiki_page['space'], self.current_xWiki_page['name'])
            # print(response)
            # self.current_version_to_versionID
            return self.current_xWiki_page['majorVersion']

    def collect_page_author(self, page):
        if page.page_platform == 'Confluence':
            page_history = self.confluenceAPI.get_content_history_by_id(page.page_id)
            page_creator = page_history['createdBy']['displayName']
            return page_creator
        elif page.page_platform == 'MediaWIKI':
            current_mediaWiki_revisions = self.current_mediaWiki_page.revisions(prop='ids|user|content')
            for revision in current_mediaWiki_revisions:
                if revision['parentid'] == 0:
                    PageCreator = revision['user']
                    return PageCreator
        elif page.page_platform == 'xWIKI':
            return self.current_xWiki_page['creator']

    def get_version_content_by_version(self, VersionNumber, page):
        if page.page_platform == 'Confluence':
            try:
                PageVersion = self.confluenceAPI.get_content_by_id(page.page_id, 'historical', VersionNumber)
                Contributor = PageVersion['version']['by']['displayName']
                PageVersion = self.confluenceAPI.get_content_by_id(page.page_id, 'historical', VersionNumber,
                                                                   'body.storage')
            except:
                print('Unable to get version: ' + str(VersionNumber) + 'of page ID' + str(page.page_id))
                return None
            return VersionNumber, PageVersion, Contributor
        elif page.page_platform == 'MediaWIKI':  # needs improvement, too slow
            PageVersion = None
            Contributor = None
            # get version ID
            versionID = self.current_version_to_versionID[VersionNumber - 1]
            current_mediaWiki_revisions = self.current_mediaWiki_page.revisions(prop='ids|user|content')
            for revision in current_mediaWiki_revisions:
                if revision['revid'] == versionID[0]:
                    Contributor = revision['user']
                    PageVersion = revision['*']
            if PageVersion is None or Contributor is None:
                for revision in current_mediaWiki_revisions:
                    print('In search:', versionID[0])
                    print(revision)
                    print(revision['revid'])
                    exit()
            return VersionNumber, PageVersion, Contributor
        elif page.page_platform == 'xWIKI':
            nested_space = None
            nested_space = page.page_xWIKI_nested_space
            # first, we need to find the latest minor version for the major version which were provided to method
            # +str(self.current_xWiki_page['wiki'])+ is temporally removed, since it looks more logical to use only 1 wiki
            response = self.xWikiAPI.get_page_version_content_and_author(page.page_xWIKI_space,
                                                                         page.page_xWIKI_page,
                                                                         str(VersionNumber) + '.1', nested_space)
            PageVersion = response[0]
            Contributor = response[1]
            return VersionNumber, PageVersion, Contributor

    def check_exclusions(self, page, platform, TaskExclusions):
        excluded = True
        try:
            TaskExclusions[platform].index(page)
        except ValueError:
            excluded = False

        for exclusion in TaskExclusions[platform]:
            if exclusion is not None:
                if exclusion.endswith('%'):
                    if page.startswith(exclusion[:-1]):
                        excluded = True
        if excluded == True:
            self.TotalExcluded += 1
            return False
        else:
            return True


class Page:
    def __init__(self, page_title, current_platform, page_xWIKI_nested_space=None, page_xWIKI_page=None,
                 page_xWIKI_space=None):
        if current_platform == 'xWIKI':
            self.page_title = page_title
            self.page_xWIKI_page = page_xWIKI_page
            self.page_xWIKI_nested_space = page_xWIKI_nested_space
            self.page_xWIKI_space = page_xWIKI_space
        else:
            self.page_title = page_title
        self.page_id = ''
        self.page_versions = ''
        self.page_author = ''
        self.contributors = {}
        self.page_creation_date = ''
        self.PageVersionsDict = []
        self.VersionsGlobalArray = []
        self.TotalContribute = {}
        self.TotalCharacters = 0
        self.page_platform = current_platform
        self.dbVersion = ''
        self.pageSQL_id = ''

    def add_new_page_version(self, VersionNumberContentContributor):
        if VersionNumberContentContributor is None:
            print('Kernel panic!')
            exit()
        if self.page_platform == 'Confluence':
            try:
                self.PageVersionsDict.append([VersionNumberContentContributor[0],
                                              VersionNumberContentContributor[1]['body']['storage']['value']])
                self.contributors[VersionNumberContentContributor[0]] = VersionNumberContentContributor[2]
            except:
                print('Unable to add new Version into PageVersionsDict', VersionNumberContentContributor)
        elif self.page_platform == 'MediaWIKI':
            try:
                self.PageVersionsDict.append([VersionNumberContentContributor[0], VersionNumberContentContributor[1]])
                self.contributors[VersionNumberContentContributor[0]] = VersionNumberContentContributor[2]
            except:
                print('Unable to add new Version into PageVersionsDict', VersionNumberContentContributor)
                exit()
        elif self.page_platform == 'xWIKI':
            try:
                self.PageVersionsDict.append([VersionNumberContentContributor[0], VersionNumberContentContributor[1]])
                self.contributors[VersionNumberContentContributor[0]] = VersionNumberContentContributor[2]
            except:
                print('Unable to add new Version into PageVersionsDict', VersionNumberContentContributor)
                exit()


class ContributionComparator:
    def __init__(self, logging_mode='silent'):
        self.temp_array = []
        self.some_other_array = []
        self.logging_mode = logging_mode

    def initial_compare(self, current_page_instance):  # compares all existing versions
        for index, version_content in enumerate(current_page_instance.PageVersionsDict):
            # print('Iteration number', index)
            try:
                stage_next = version_content
                if index == 0:
                    stage_first = [-1, '']
                else:
                    stage_first = current_page_instance.PageVersionsDict[index - 1]
                # print('{} => {}'.format(stage_first, stage_next))
                for i, s in enumerate(difflib.ndiff(stage_first[1], stage_next[1])):
                    if s[0] == '+':
                        # print(u'Add "{}" to position {}'.format(s[-1], i))
                        current_page_instance.VersionsGlobalArray.insert(i, [s[-1], stage_next[0]])
                    elif s[0] == '-':
                        # print(u'Delete "{}" from position {}'.format(s[-1], i))
                        current_page_instance.VersionsGlobalArray[i] = None
                self.temp_array = []
                self.some_other_array = []
                self.temp_array[:] = []
                self.some_other_array[:] = []
                self.temp_array = copy.deepcopy(current_page_instance.VersionsGlobalArray)
                current_page_instance.VersionsGlobalArray[:] = []
                self.some_other_array = [x for x in self.temp_array if x is not None]
                current_page_instance.VersionsGlobalArray = copy.deepcopy(self.some_other_array)
                self.temp_array[:] = []
                self.some_other_array[:] = []
            except Exception as error:
                print('initial compare of page was failed with error:', error)
                for each in current_page_instance.VersionsGlobalArray:
                    if each is None:
                        print(each, 'is none, but WTF?')
                print('CurrentPage.VersionsGlobalArray', current_page_instance.VersionsGlobalArray)
                exit()

    def incremental_compare(self, current_page_instance):
        # compares all existing version from current_page_instance.dbVersion to the current_page_instance.versions
        for index, VersionContent in enumerate(current_page_instance.PageVersionsDict):
            if self.logging_mode != 'silent': print('Iteration number', index)
            if index == len(current_page_instance.PageVersionsDict) - 1:
                break
            stage_first = VersionContent
            stage_next = current_page_instance.PageVersionsDict[index + 1]
            try:
                if self.logging_mode != 'silent':
                    print(stage_first)
                    print(stage_next)
                array_to_compare = difflib.ndiff(stage_first[1], stage_next[1])
                for i, s in enumerate(
                        array_to_compare):  # TODO: each s[0] == ' ' extends loop. Need to find a way to ignore them
                    if s[0] == '+':
                        if self.logging_mode != 'silent': print(u'Add "{}" to position {}'.format(s[-1], i))
                        current_page_instance.VersionsGlobalArray.insert(i, [s[-1], stage_next[0]])
                    elif s[0] == '-':
                        if self.logging_mode != 'silent': print(u'Delete "{}" from position {}'.format(s[-1], i))
                        current_page_instance.VersionsGlobalArray[i] = None
                if self.logging_mode != 'silent':
                    print('Done with compare, removing deleted characters...')
                self.temp_array[:] = []
                self.some_other_array[:] = []
                self.temp_array = copy.deepcopy(current_page_instance.VersionsGlobalArray)
                current_page_instance.VersionsGlobalArray[:] = []
                self.some_other_array = [x for x in self.temp_array if x is not None]
                current_page_instance.VersionsGlobalArray = copy.deepcopy(self.some_other_array)
            except Exception as error:
                print('Incremental compare of page was failed with error:', error)
                for each in current_page_instance.VersionsGlobalArray:
                    if each is None:
                        print(each, 'is none, but WTF?')
                        break
                print('current_page_instance.VersionsGlobalArray', current_page_instance.VersionsGlobalArray)
                print('Len of array', len(current_page_instance.VersionsGlobalArray))
                exit()


class CustomLogging:
    def __init__(self, log_level='silent'):
        self.GlobalStartTime = datetime.now()
        self.LogLevel = log_level
        self.GlobalStartTime = None
        self.TaskStartTime = None
        self.TaskEndTime = None
        self.PageAnalysisStartTime = None
        self.PageAnalysisEndTime = None
        self.PageCountingEndTime = None

    def log_task_start(self, pages_found, excluded):
        self.TaskStartTime = datetime.now()
        if self.LogLevel != 'silent':
            print(self.TaskStartTime, pages_found, 'pages were found in all spaces, excluded:', excluded)
        else:
            print(self.TaskStartTime, pages_found, 'pages were found in all spaces, excluded:', excluded)

    def page_analysis_started(self, title):
        self.PageAnalysisStartTime = datetime.now()
        if self.LogLevel != 'silent':
            print(self.PageAnalysisStartTime, title + ': Task initialized, getting sources...')

    def page_processing_started(self, CurrentPage):
        if CurrentPage.dbVersion == None:
            if self.LogLevel != 'silent':
                print('"' + CurrentPage.page_title + '" will be processed in FULL mode')
        elif CurrentPage.dbVersion < CurrentPage.page_versions:
            if self.LogLevel != 'silent':
                print('"' + CurrentPage.page_title + '" will be processed in INCREMENTAL mode')
        elif CurrentPage.dbVersion == CurrentPage.page_versions:
            if self.LogLevel != 'silent':
                print('"' + CurrentPage.page_title + '" is up-to-date')

    def page_processing_target(self, CurrentPage):
        self.PageAnalysisEndTime = datetime.now()
        if self.LogLevel != 'silent':
            print(self.PageAnalysisEndTime, 'Page "' + CurrentPage.page_title + '" with ID ' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found', '\n',
                  'Sources are collected, calculating difference... ')

    def page_counting_finished(self, CurrentPage):
        self.PageCountingEndTime = datetime.now()
        if self.LogLevel != 'silent':
            print(self.PageCountingEndTime, '... Done')

    def page_summary(self, CurrentPage):
        if self.LogLevel != 'silent':
            print('Characters in TOTAL: ', CurrentPage.TOTALCharacters)
            if CurrentPage.TOTALCharacters != 0:
                for Contributor, Value in CurrentPage.TotalContribute.items():
                    Percent = (Value / CurrentPage.TOTALCharacters) * 100
                    print('Contribution of ' + Contributor + ' = ' + str(Percent) + '%' + ' (' + str(
                        Value) + ') characters')
            print('Time elapsed: Analysis:', self.PageAnalysisEndTime - self.PageAnalysisStartTime, '+ Diff calc:',
                  self.PageCountingEndTime - self.PageAnalysisEndTime, '=',
                  self.PageCountingEndTime - self.PageAnalysisStartTime)
        self.PageAnalysisStartTime = None
        self.PageAnalysisEndTime = None
        self.PageCountingEndTime = None

    def log_task_ended(self):
        self.TaskEndTime = datetime.now()
        TotalElapsed = self.TaskEndTime - self.TaskStartTime
        print(self.TaskEndTime, 'Total time wasted', TotalElapsed)

    def skip_some_page(self, title):
        print(datetime.now(), title, 'is redirect or unable to find ID, skipping')


class MysqlConnector(object):
    def __init__(self, config: Configuration.MySQLConfig):
        self.cnx = mysql.connector.connect(user=config.user, password=config.password,
                                           host=config.host,
                                           port=config.port,
                                           database=config.database)
        self.cursor = self.cnx.cursor(buffered=True)
        self.xWikiConfig_instance = Configuration.xWikiConfig('Sandbox')
        self.xWikiClient_instance = XWikiClient(self.xWikiConfig_instance.api_root, self.xWikiConfig_instance.auth_user,
                                                self.xWikiConfig_instance.auth_pass)

    def get_XWD_ID(self, XWD_WEB):
        query = ("select XWD_ID from xwikidoc where XWD_FULLNAME= %(XWD_FULLNAME)s")
        data = {
            'XWD_FULLNAME': XWD_WEB
        }
        self.cursor.execute(query, data)
        if self.cursor.rowcount != 0:
            for row in self.cursor:
                XWD_ID = str(row[0])
            return XWD_ID
        else:
            return None

    def get_XWD_TITLE(self, XWD_FULLNAME):
        query = ("select XWD_TITLE from xwikidoc where XWD_FULLNAME= %(XWD_FULLNAME)s")
        data = {
            'XWD_FULLNAME': XWD_FULLNAME
        }
        self.cursor.execute(query, data)
        XWD_TITLE = None
        if self.cursor.rowcount != 0:
            for row in self.cursor:
                XWD_TITLE = row[0].decode("utf-8")
            return XWD_TITLE
        else:
            return None

    def get_XWD_FULLNAME(self, XWD_ID: str):
        logger = logging.getLogger()
        query = ("select XWD_FULLNAME from xwikidoc where XWD_ID = %(XWD_ID)s")
        logger.debug('XWD_ID:' + str(XWD_ID))
        data = {
            'XWD_ID': XWD_ID
        }
        self.cursor.execute(query, data)
        logger.debug('rowcount:' + str(self.cursor.rowcount))
        XWD_FULLNAME = None
        if self.cursor.rowcount != 0:
            for row in self.cursor:
                logger.debug('row:' + str(row))
                XWD_FULLNAME = row[0].decode("utf-8")
            return XWD_FULLNAME
        elif self.cursor.rowcount == 0:
            for row in self.cursor:
                logger.debug('row:' + str(row))
                return XWD_FULLNAME
        else:
            return XWD_FULLNAME

    def add_new_tag(self, space, parent, title, page, tag, test=False):
        result = self.xWikiClient_instance.add_tag_to_page(space=space, page=page, title=title, parent=parent, tag=tag)
        if result == 202:
            print('Tag', tag, 'was added')
        else:
            print('Tag', tag, 'wasn\'t added')

    def add_new_version(self, space, parent, title, page, content, author, version, syntax='xwiki/2.1', test=False,
                        only_update=False, last_run=False):
        space = space[1]
        author = author[1]
        title = title[1]
        page = page[1]
        content = content[1]
        parent = parent[1]
        syntax = syntax[1]
        version = version[1]
        test = test[1]
        only_update = only_update[1]
        last_run = last_run[1]

        if last_run is True:
            print('============================================================Finalizing on', version,
                  'version=============================================================')
        else:
            print('============================================================Sequence', version,
                  'started=============================================================')
        if only_update is not True:
            if version == 1:
                try:
                    result = self.xWikiClient_instance.delete_page(space=space, page=page, title=title, parent=parent)
                    print('Page deleted with result:', result)
                except requests.exceptions.HTTPError:
                    print('No such page found, deletion isn\'t needed')
                result = self.xWikiClient_instance.submit_page(space=space, page=page, content='', syntax=syntax,
                                                               title=title, parent=parent)
                print('Page created with syntax:', syntax, 'and result:', result)
        version += 1
        if only_update is not True:
            if parent != space:
                result = self.xWikiClient_instance.submit_page_as_plane(space=space, page=page, content=content,
                                                                        syntax=syntax, title=title, parent=parent)
            else:
                result = self.xWikiClient_instance.submit_page_as_plane(space=space, page=page, content=content,
                                                                        syntax=syntax, title=title, parent=None)
        print('Page', result)

        if version == 1 and result != 'Created':
            print('Result != Created while 1st run. Kernel panic!')
            exit()
        elif result == 'Unmodified':
            print('Result: Unmodified. Kernel panic!')
            exit()
        if content == '':
            print('Content length == ''. Kernel panic!')
            exit()
        if parent == space:
            XWD_WEB = space + '.' + page
        else:
            XWD_WEB = space + '.' + parent + '.' + page
        XWD_ID = self.get_XWD_ID(XWD_WEB)
        query = (
            "update xwikircs set XWR_AUTHOR = %(XWR_AUTHOR)s where XWR_DOCID = %(XWR_DOCID)s and XWR_VERSION1 = %(XWR_VERSION1)s")
        data = {
            'XWR_VERSION1': version,
            'XWR_AUTHOR': author,
            'XWR_DOCID': XWD_ID
        }
        self.cursor.execute(query, data)
        print('update xwikircs done, affected rows = {}'.format(self.cursor.rowcount))
        if test is True:
            self.cnx.rollback()
            print(query, data)
        else:
            self.cnx.commit()
        if syntax != 'xwiki/2.1':
            query = (
                'update xwikidoc set XWD_SYNTAX_ID = %(XWD_SYNTAX_ID)s, XWD_AUTHOR = %(XWD_AUTHOR)s, XWD_CONTENT_AUTHOR = %(XWD_CONTENT_AUTHOR)s where XWD_FULLNAME = %(XWD_NAME)s')
            data = {
                'XWD_NAME': XWD_WEB,
                'XWD_SYNTAX_ID': syntax,
                'XWD_AUTHOR': author,
                'XWD_CONTENT_AUTHOR': author,
            }
            self.cursor.execute(query, data)
            print('update XWD_SYNTAX_ID in xwikidoc done, affected rows = {}'.format(self.cursor.rowcount))
            if test is True:
                self.cnx.rollback()
                print(query, data)
            else:
                self.cnx.commit()
            query = (
                'UPDATE xwikircs SET XWR_Patch = UpdateXML(XWR_Patch,"xwikidoc/syntaxId", "<syntaxId>' + syntax + '</syntaxId>"),'
                                                                                                                  'XWR_Patch = UpdateXML(XWR_Patch,"xwikidoc/contentAuthor", "<contentAuthor>' + author + '</contentAuthor>"),'
                                                                                                                                                                                                          'XWR_Patch = UpdateXML(XWR_Patch,"xwikidoc/author", "<author>' + author + '</author>") '
                                                                                                                                                                                                                                                                                    'WHERE XWR_DOCID=%(XWR_DOCID)s and XWR_ISDIFF = 0')
            data = {
                'XWR_DOCID': XWD_ID,
                'XWD_SYNTAX_ID': syntax
            }
            self.cursor.execute(query, data)
            print('update XWD_SYNTAX_ID in xwikircs done, affected rows = {}'.format(self.cursor.rowcount))
            if test is True:
                self.cnx.rollback()
                print(query, data)
            else:
                self.cnx.commit()
        return True

    def get_XWD_FULLNAMEs(self, space: str):
        query = (
            "select XWD_FULLNAME from xwikidoc where XWD_FULLNAME like %(poolname)s and XWD_CREATOR != 'XWiki.root' and XWD_HIDDEN != 1")
        data = {
            'poolname': space + '%'
        }
        self.cursor.execute(query, data)
        if self.cursor.rowcount != 0:
            space_subtitles_XWD_FULLNAMEs = []
            for row in self.cursor:
                space_subtitles_XWD_FULLNAMEs.append(row[0].decode("utf-8"))
            return space_subtitles_XWD_FULLNAMEs
        else:
            return None


class XWikiClient(object):
    def __init__(self, api_root, auth_user=None, auth_pass=None):
        self.api_root = api_root
        self.auth_user = auth_user
        self.auth_pass = auth_pass

    def _build_url(self, path):
        # print(path)
        for idx, val in enumerate(path):
            path[idx] = val.replace('/', '%2F').replace('\\.', '.')
        url = self.api_root + "/".join(path)
        if url.endswith('.'):
            url = url[:-1]
        # print(url)
        return url

    def _make_request(self, path, data):
        url = self._build_url(path)
        data['media'] = 'json'
        auth = None
        if self.auth_user and self.auth_pass:
            auth = self.auth_user, self.auth_pass
        response = requests.get(url, params=data, auth=auth)
        response.raise_for_status()
        return response.json()

    def _make_put_with_no_header(self, path, data):
        url = self._build_url(path)
        # print(url)
        # data['media'] = 'json'

        auth = None
        if self.auth_user and self.auth_pass:
            auth = self.auth_user, self.auth_pass

        response = requests.put(url, data=data, auth=auth)
        response.raise_for_status()
        return response.status_code

    def _make_put(self, path, data, headers):
        url = self._build_url(path)
        auth = None
        if self.auth_user and self.auth_pass:
            auth = self.auth_user, self.auth_pass
        if type(data) == bytes:
            response = requests.put(url, data=data, auth=auth, headers=headers)
        else:
            response = requests.put(url, data=data.encode('utf-8'), auth=auth, headers=headers)
        response.raise_for_status()
        return response.status_code

    def _make_delete(self, path, data, headers):
        url = self._build_url(path)
        # data['media'] = 'json'

        auth = None
        if self.auth_user and self.auth_pass:
            auth = self.auth_user, self.auth_pass
        response = requests.delete(url, data=data.encode('utf-8'), auth=auth, headers=headers)
        response.raise_for_status()
        return response.status_code

    def _make_post(self, path, data, headers):
        url = self._build_url(path)
        # data['media'] = 'json'

        auth = None
        if self.auth_user and self.auth_pass:
            auth = self.auth_user, self.auth_pass
        # print(url)
        response = requests.post(url, data=data.encode('utf-8'), auth=auth, headers=headers)
        response.raise_for_status()
        return response.status_code

    def spaces(self):
        path = ['spaces']
        data = {}
        content = self._make_request(path, data)
        return content['spaces']

    def space_names(self):
        spaces = []
        result = self.spaces()
        for details in result:
            spaces.append(details['name'])
        return spaces

    def pages(self, space):
        path = ['spaces', space, 'pages']
        data = {}
        content = self._make_request(path, data)
        return content['pageSummaries']

    def page_names(self, space):
        pages = []
        result = self.pages(space)
        for details in result:
            pages.append(details['title'])
        return pages

    def page(self, space: str, page: str, nested_space: list = None, is_terminal_page: bool = False):
        if nested_space is None:
            if is_terminal_page is True:
                path = ['spaces', space, 'pages', page]
            else:
                path = ['spaces', space, 'spaces', page, 'pages', 'WebHome']
        else:
            path = ['spaces', space]
            for space in nested_space:
                l = ['spaces', space]
                path.extend(l)
            l = ['spaces', page, 'pages', 'WebHome']
            path.extend(l)
        data = {}
        try:
            content = self._make_request(path, data)
            return content
        except requests.exceptions.HTTPError:
            try:
                # print('It\'s a terminal page')
                l = ['pages', page]
                terminal_path = path[:-3]
                terminal_path.extend(l)
                content = self._make_request(terminal_path, data)
                return content
            except:
                return None

    def get_tags_of_page(self, space: str, page: str, nested_space: list = None, is_terminal_page: bool = False):
        if nested_space is None:
            if is_terminal_page is True:
                path = ['spaces', space, 'pages', page, 'tags']
            else:
                path = ['spaces', space, 'spaces', page, 'pages', 'WebHome', 'tags']
        else:
            if is_terminal_page is True:
                path = ['spaces', space]
                for space in nested_space:
                    l = ['spaces', space]
                    path.extend(l)
                l = ['pages', page, 'tags']
                path.extend(l)
            elif is_terminal_page is False:
                path = ['spaces', space]
                for space in nested_space:
                    l = ['spaces', space]
                    path.extend(l)
                l = ['spaces', page, 'pages', 'WebHome', 'tags']
                path.extend(l)
        data = {}
        try:
            content = self._make_request(path, data)
            return content
        except requests.exceptions.HTTPError:
            try:
                # print('It\'s a terminal page')
                l = ['pages', page]
                terminal_path = path[:-3]
                terminal_path.extend(l)
                content = self._make_request(terminal_path, data)
                return content
            except:
                return None

    def get_pages_by_space(self, space):
        MySQLconfig_INSTANCE = Configuration.MySQLConfig()
        little_mysql_client = MysqlConnector(MySQLconfig_INSTANCE)
        result = little_mysql_client.get_XWD_FULLNAME(space)
        if result != None:
            return result
        else:
            return None

    def tags(self):
        path = ['tags']
        data = {}
        content = self._make_request(path, data)
        return content['tags']

    def tag_names(self):
        tags = []
        result = self.tags()
        for details in result:
            tags.append(details['name'])
        return tags

    def pages_by_tags(self, tags):
        taglist = ",".join(tags)
        path = ['tags', taglist]
        data = {}
        content = self._make_request(path, data)
        return content['pageSummaries']

    def submit_page(self, space, page, content, syntax, title=None, parent=None):
        # print('page (aka title) in submit', page)

        path = ['spaces', space, 'pages', page]
        if title is not None:
            xml_title = title
        else:
            xml_title = page
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
              '<page xmlns="http://www.xwiki.org">' \
              '<title>' + xml_title + '</title>' \
                                      '<syntax>' + syntax + '</syntax>' \
                                                            '<content>' + content + '</content>' \
                                                                                    '</page>'
        headers = {'Content-Type': 'application/xml'}
        status = self._make_put(path, xml, headers)
        if status == 201:
            return "Created"
        elif status == 202:
            return "Updated"
        elif status == 304:
            return "Unmodified"

    def submit_page_as_plane(self, space, page, content, syntax, title=None, parent=None, nested_spacet=None):

        path = ['spaces', space, 'pages', page]
        data = {'content': content}
        if title:
            data['title'] = title
        else:
            data['title'] = page

        if parent:
            data['parent'] = parent
        status = self._make_put_with_no_header(path, data)
        if status == 201:
            return "Created"
        elif status == 202:
            return "Updated"
        elif status == 304:
            return "Unmodified"

    def add_tag_to_page(self, space, page, tags=list, title=None, parent=None):
        path = ['spaces', space, 'pages', page, 'tags']
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        xml += '<tags xmlns="http://www.xwiki.org">'
        for tag in tags:
            xml += '<tag name="' + tag + '"></tag>'
        xml += '</tags>'
        headers = {'Content-Type': 'application/xml'}
        status = self._make_put(path, xml, headers)
        if status == 202:
            return "Created"
        elif status == 401:
            return "Failed"

    def add_tag_to_page_as_plane(self, space, page, tag, title=None, parent=None):
        path = ['spaces', space, 'pages', page, 'tags']
        data = tag
        status = self._make_put_with_no_header(path, data)
        if status == 202:
            return "Added"
        elif status == 401:
            return "Failed"

    def delete_page(self, space, page, title=None, parent=None):
        path = ['spaces', space, 'pages', page]
        if title is None:
            title = page
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
              '<page xmlns="http://www.xwiki.org">' \
              '<title>' + title + '</title>' \
                                  '</page>'
        headers = {'Content-Type': 'application/xml'}
        status = self._make_delete(path, xml, headers)
        if status == 204:
            return "Successful"
        elif status == 401:
            return "Not authorized"

    def get_page_history(self, space, page_name):
        path = ['spaces', space, 'pages', page_name, 'history']
        data = {}
        content = self._make_request(path, data)
        return content

    def get_page_version_content_and_author(self, space, page, version, nested_space=None,
                                            is_terminal_page: bool = False):
        if nested_space is None:
            if is_terminal_page is True:
                path = ['spaces', space, 'pages', page, 'history', version]
            else:
                path = ['spaces', space, 'spaces', page, 'pages', 'WebHome', 'history', version]
        else:
            # print('It\'s not a terminal page')
            path = ['spaces', space]
            for space in nested_space:
                l = ['spaces', space]
                path.extend(l)
            l = ['spaces', page, 'pages', 'WebHome', 'history', version]
            path.extend(l)
        data = {}
        try:
            content = self._make_request(path, data)
            return content['content'], content['author']
        except requests.exceptions.HTTPError:
            try:
                # print('It\'s a terminal page')
                l = ['pages', page, 'history', version]
                terminal_path = path[:-6]
                terminal_path.extend(l)
                content = self._make_request(terminal_path, data)
                return content['content'], content['author']
            except:
                return None

    def add_new_attach_as_plane(self, space, page, attach_name, path_to_attach):
        # http://lists.xwiki.org/pipermail/users/2010-February/015251.html
        path = ['spaces', space, 'pages', page, 'attachments', attach_name]
        data = path_to_attach
        status = self._make_put_with_no_header(path, data)
        if status == 201:
            return "Created"
        elif status == 202:
            return "Updated"
        elif status == 401:
            return "Not authorized"

    def add_new_attach_application(self, space, page, attach_name, attach_content):
        path = ['spaces', space, 'pages', page, 'attachments', attach_name]
        data = attach_content
        headers = {'Content-Type': 'application/octet-stream',
                   'Content-Disposition': 'attachment; filename=%attach_name' % attach_name}
        # Application/octet-stream means that the sender of the data (probably an HTTP server) had no idea what the data is. It's just an arbitrary data dump.
        status = self._make_put(path, data, headers)
        if status == 201:
            return "Created"
        elif status == 202:
            return "Updated"
        elif status == 401:
            return "Not authorized"


class ExclusionsDict(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(ExclusionsDict, self).__setitem__(key, [])
        self[key].append(value)


class Migrator(object):
    def __init__(self, ConfluenceConfig: Configuration.ConfluenceConfig, MediaWIKIConfig: Configuration.MediaWIKIConfig,
                 xWikiConfig: Configuration.xWikiConfig):
        self.confluenceAPI = ConfluenceAPI(ConfluenceConfig.USER, ConfluenceConfig.PASS, ConfluenceConfig.ULR)
        self.ConfluenceConfig = ConfluenceConfig
        self.MediaWIKIConfig_instance = MediaWIKIConfig
        self.xWikiConfig = xWikiConfig
        self.xWikiClient = XWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
        self.tag_list = []
        self.file_list = []
        self.current_page_id = None

    def get_tags(self, platform: str, id: str = None, test_str: str = None):
        self.tag_list = []
        if test_str is None and id is None: return False
        if platform == 'Confluence':
            self.current_page_id = id
            result = self.confluenceAPI.get_content_labels(id, prefix=None, start=None, limit=None, callback=None)
            for each in result['results']:
                self.tag_list.append(each['name'])
            return self.tag_list
        elif platform == 'MediaWIKI':
            regex = r"\[\[Category:(.[^\]]*)\]\]"
            matches = re.finditer(regex, test_str, re.IGNORECASE)
            for matchNum, match in enumerate(matches):
                matchNum = matchNum + 1
                match = match.group(1)
                self.tag_list.append(match)
            return self.tag_list

    def get_files(self, platform: str, id: str = None, test_str: str = None):
        self.file_list = []
        if test_str is None and id is None: return False
        if platform.lower() == 'confluence':
            self.current_page_id = id
            regex = r"\<ri\:attachment ri\:filename=\"(.[^\"]*)\" \/\>"
            matches = re.finditer(regex, test_str)
            for matchNum, match in enumerate(matches):
                matchNum = matchNum + 1
                match = match.group(1)
                self.file_list.append(match)
            self.file_list = list(set(self.file_list))
            print(self.file_list)
            return self.file_list
        elif platform.lower() == 'mediawiki':
            regex = r"\[\[File:((\w|\d|-| |\.[^\|])*).*"
            matches = re.finditer(regex, test_str, re.IGNORECASE)  # added ignore case option
            # print('test_str', test_str)
            for matchNum, match in enumerate(matches):
                matchNum = matchNum + 1
                match = match.group(1)
                self.file_list.append(match)
            return self.file_list

    def make_and_attach(self, platform: str, file_name: str, page: str, space):
        source_url = None
        if platform.lower() == 'confluence':
            if self.current_page_id is None:
                print('current_page_id is still None')
                return False
            attachment = self.confluenceAPI.get_content_attachments(self.current_page_id, expand=None, start=None,
                                                                    limit=None, filename=file_name, media_type=None,
                                                                    callback=None)
            source_url = self.ConfluenceConfig.ULR + attachment['results'][0]['_links']['download']
        elif platform.lower() == 'mediawiki':
            # so, now we need to locate the attachment
            request_url = self.MediaWIKIConfig_instance.APIPath_long + 'action=query&titles=File:' + file_name + '&prop=imageinfo&iiprop=url&format=json'
            r = requests.get(request_url, stream=True)
            if r.status_code == 200:
                respond = r.json()
                answer = str(respond['query']['pages'])
                regex = r"'url': '(.[^']*)'"
                matches = matches = re.finditer(regex, answer)
                for matchNum, match in enumerate(matches):
                    matchNum = matchNum + 1
                    match = match.group(1)
                    source_url = match
                    break  # using only the fist link
            else:
                print('ERROR: unable to find the source link for', file_name, request_url)
                return False
        if source_url is None:
            return None
        r = requests.get(source_url, stream=True)
        file_content = None
        if r.status_code == 200:
            file_content = r.content
        if file_content is not None:
            print(file_content)
            result = self.xWikiClient.add_new_attach_application(space=space, page=page, attach_name=file_name,
                                                                 attach_content=file_content)
            return result


def Migrate_page(title, platform, target_pool, parent, MySQLconfig_INSTANCE, MysqlConnector_INSTANCE, SQLConfig,
                 SQLConnector, ConfluenceConfig, MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList):
    # Initializing agent
    # Starting migration process
    my_str_as_bytes = str.encode(title)
    m = hashlib.md5(my_str_as_bytes)
    page_hash = m.hexdigest()
    print('~~~~~~~~~~~~STATE: Starting migration process of', '"' + title + '"', 'from platform', platform,
          '~~~~~~~~~~~~')
    SQLQuery = SQLConnector.select_datagrams_from_dbo_knownpages_datagrams(page_title=title, platform=platform)
    if SQLQuery is None:
        result = 'ERROR: Page', title, 'on platform', platform, 'isn\'t indexed yet'
        return False, result
    datagram = SQLQuery[0]
    contributors_datagram = SQLQuery[1]
    if len(datagram) == 0 or len(contributors_datagram) == '':
        result = 'ERROR: Page', '"' + title + '" from platform', platform, 'has no text'
        return False, result
    UniqueUsers = set(contributors_datagram.values())
    # print(UniqueUsers)
    # print(contributors_datagram)
    for idx, user in enumerate(UniqueUsers):
        for version, author in contributors_datagram.items():
            if author == user:
                for symbol in datagram:
                    if symbol[1] == version:
                        symbol[1] = idx
    global_counter_of_symbols = 0
    version = 0
    latest_text = None
    last_version = None
    title = title.replace('&', '%26')  # dosn't work :(
    for idx, author in enumerate(UniqueUsers):
        version += 1
        text = ''
        counter_of_symbols = 0
        for symbol in datagram:
            if symbol[1] <= idx:
                text += symbol[0]
                if symbol[1] == idx:
                    counter_of_symbols += 1
        global_counter_of_symbols += counter_of_symbols
        # print(author, 'with id:', idx, 'has contributed:', counter_of_symbols)
        if counter_of_symbols == 0:
            version -= 1
            continue
        try:
            author = UserList.users[author]
        except KeyError:
            author = None
        if author is None:
            author = "XWiki.bot"
        if platform.lower() == 'confluence':
            syntax = 'confluence+xhtml/1.0'
        elif platform.lower() == 'mediawiki':
            syntax = 'mediawiki/1.6'
        else:
            syntax = 'xwiki/2.1'
        text = text.replace('’', '\'')
        text = text.replace('”', '"')
        text = text.replace('“', '"')
        DataTuple = (
            ('space', target_pool),
            ('parent', parent),
            ('title', title),
            ('page', page_hash),
            ('content', text),
            ('author', author),
            ('version', version),
            ('syntax', syntax),  # 'confluence/1.0' 'xwiki/2.1' 'MediaWiki/1.6'
            ('test', False),
            ('only_update', False),
            ('last_run', False),
        )

        MysqlConnector_INSTANCE.add_new_version(*DataTuple)
        latest_text = text
        last_version = version + 1
    if latest_text is not None and last_version is not None:
        content = latest_text + ' '
        DataTuple = (
            ('space', target_pool),
            ('parent', parent),
            ('title', title),
            ('page', page_hash),
            ('content', content),
            ('author', "XWiki.bot"),
            ('version', last_version),
            ('syntax', syntax),  # 'confluence/1.0' 'xwiki/2.1' 'MediaWiki/1.6'
            ('test', False),
            ('only_update', False),
            ('last_run', True),
        )
        MysqlConnector_INSTANCE.add_new_version(*DataTuple)
        tags = None
        files = None
        if platform.lower() == 'confluence':
            page_id = SQLConnector.select_page_id_from_dbo_knownpages(title, platform)
            tags = Migrator.get_tags(platform=platform, id=page_id, test_str=None)
            files = Migrator.get_files(platform=platform, id=page_id, test_str=latest_text)
            print('files', files, 'tags', tags)
        elif platform.lower() == 'mediawiki':
            tags = Migrator.get_tags(platform=platform, id=None, test_str=latest_text)
            files = Migrator.get_files(platform=platform, id=None, test_str=latest_text)
            # print(files)
        if bool(re.match('bug', title, re.I)):
            match = False
            for i in set(tags):
                if bool(re.match('bug', i, re.I)):
                    match = True
            if match is False:
                tags.append('bug')
        # print('files:', files)
        # Doing tags
        if tags is not None:
            result = xWikiClient.add_tag_to_page(space=target_pool, page=page_hash, tags=tags, title=title,
                                                 parent=parent)
            print(result, len(tags), 'tags:', tags)
        else:
            a = 1
            print('No tags were found')
        # Doing attachments
        if files is not None and len(files) != 0:
            print('Following files will be attached', files)
            for file in files:
                try:
                    result = Migrator.make_and_attach(platform, file_name=file, page=page_hash,
                                                      space=target_pool)
                    print(result, 'file:', file)
                except Exception as e:
                    print('Failed on file:', file)
                    print(traceback.format_exc())
                    print('Failed on file:', file)
            print('Total proceed:', len(files))
        else:
            a = 1
            print('No files were found')
        result = 'SUCCESS: Page', '"' + title + '" from platform', platform, 'is migrated'
        return True, result
