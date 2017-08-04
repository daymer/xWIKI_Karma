from PythonConfluenceAPI import ConfluenceAPI
from mwclient import Site
import difflib
import pyodbc
import traceback
import pickle
from datetime import datetime
import time
import requests
import copy
import sys
import mysql.connector
import random
import Configuration
sys.setrecursionlimit(10**6)


class xWIKIDB_data_handler(object):
    def __init__(self, xWIki_space, parent_page,title,creation_time,XWD_AUTHOR,XWD_CONTENT_AUTHOR,XWD_CREATOR,content,version,syntax,XWD_ID,XWS_ID):
        self.XWD_FULLNAME = xWIki_space[1] + '.' + parent_page[1] + '.' + title[1] + '.WebHome'
        self.XWD_NAME = 'WebHome'
        self.XWD_TITLE = title[1]
        self.XWD_LANGUAGE = 'NULL'
        self.XWD_DEFAULT_LANGUAGE = 'en'
        self.XWD_TRANSLATION = '0'
        self.XWD_DATE = creation_time[1],
        self.XWD_CONTENT_UPDATE_DATE = creation_time[1]
        self.XWD_CREATION_DATE = creation_time[1]
        self.XWD_AUTHOR = str(XWD_AUTHOR[1])
        self.XWD_CONTENT_AUTHOR = XWD_CONTENT_AUTHOR[1],
        self.XWD_CREATOR = XWD_CREATOR[1]
        self.XWD_WEB = xWIki_space[1] + '.' + parent_page[1] + '.' + title[1]
        self.XWD_CONTENT = content[1]
        self.XWD_VERSION = version[1]
        self.XWD_CUSTOM_CLASS = 'NULL'
        self.XWD_PARENT = xWIki_space[1] + '.' + parent_page[1] + '.WebHome'
        self.XWD_CLASS_XML = 'NULL'
        self.XWD_ELEMENTS = '0'
        self.XWD_DEFAULT_TEMPLATE = 'NULL'
        self.XWD_VALIDATION_SCRIPT = 'NULL'
        self.XWD_COMMENT = 'NULL'
        self.XWD_MINOREDIT = 'FALSE'
        self.XWD_SYNTAX_ID = syntax[1]
        self.XWD_HIDDEN = 'FALSE'
        self.XWD_ID = XWD_ID[1]
        self.XWS_REFERENCE = xWIki_space[1] + '.' + parent_page[1] + '.' + title[1]
        self.XWS_NAME = title[1]
        self.XWS_PARENT = xWIki_space[1] + '.' + parent_page[1]
        self.XWS_HIDDEN = 'FALSE'
        self.XWS_ID = XWS_ID[1]
        self.XWL_ID = None
class PageCreator:
    def __init__(self, ConfluenceConfig, MediaWIKIConfig, xWikiConfig):
        self.confluenceAPI = ConfluenceAPI(ConfluenceConfig.USER, ConfluenceConfig.PASS, ConfluenceConfig.ULR)
        self.MediaWikiAPI = Site((MediaWIKIConfig.Protocol, MediaWIKIConfig.URL), path=MediaWIKIConfig.APIPath,
                                 clients_useragent=MediaWIKIConfig.UserAgent)
        self.xWikiSpaces = xWikiConfig.spaces
        self.xWikiAPI = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
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
            current_page = self.MediaWikiAPI.Pages[title]
            if current_page.redirect:
                #print('redirect, skipping...')
                return None
            else:
                all_page_text = current_page.text()
                if not all_page_text:
                    #print('ERROR: Page has no text or not exists, skipping.')
                    return None
                else:
                    new_created_page = Page(title, platform)
                    return new_created_page
        elif platform == 'xWIKI':
            self.current_xWiki_page = None
            for space in self.xWikiSpaces:
                current_page = self.xWikiAPI.page(space, title)
                #print('current_page is ',current_page)
                if current_page is not None:
                    self.current_xWiki_page = current_page
                    if not self.current_xWiki_page['content']:
                        print('no content was found')
                        return None
                    current_page = Page(title, platform)
                    return current_page
            if self.current_xWiki_page is None:
                print('current_xWiki_page is None')
                return None
    def collect_page_id(self, page):
        if page.page_platform == 'Confluence':
            page_content = self.confluenceAPI.get_content(content_type='page', title=page.page_title)
            try:
                page_id = page_content['results'][0]['id']
                return page_id
            except IndexError:
                print('404 - page with such name wasn\'t found')
                return None
        elif page.page_platform == 'MediaWIKI':
            self.current_mediaWiki_page = self.MediaWikiAPI.Pages[page.page_title]
            return self.current_mediaWiki_page.pageid
        elif page.page_platform == 'xWIKI':
            return self.current_xWiki_page['id']
    def collect_page_history(self, page):
        if page.page_platform == 'Confluence':
            page_history = self.confluenceAPI.get_content_history_by_id(page.page_id)
            page_versions = page_history['lastUpdated']['number']
            return page_versions
        elif page.page_platform == 'MediaWIKI':
            #dirty hack, but mwclient.listings.List has no methods to calc versions
            #also here we compare version number with version ID
            self.current_version_to_versionID[:] = []
            for revision in self.current_mediaWiki_page.revisions():
                self.current_version_to_versionID.append([revision['revid'], revision['parentid']])
            self.current_version_to_versionID = sorted(self.current_version_to_versionID)
            return len(self.current_version_to_versionID)
        elif page.page_platform == 'xWIKI':
            #response = self.xWikiAPI.get_page_history(self.current_xWiki_page['space'], self.current_xWiki_page['name'])
            #print(response)
            #self.current_version_to_versionID
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
        if page.page_platform  == 'Confluence':
            try:
                PageVersion = self.confluenceAPI.get_content_by_id(page.page_id, 'historical', VersionNumber)
                Contributor = PageVersion['version']['by']['displayName']
                PageVersion = self.confluenceAPI.get_content_by_id(page.page_id, 'historical', VersionNumber, 'body.storage')
            except:
                print('Unable to get version: ' + str(VersionNumber) + 'of page ID' + str(page.page_id))
                return None
            return VersionNumber, PageVersion, Contributor
        elif page.page_platform  == 'MediaWIKI': #needs improvement, too slow
            PageVersion = None
            Contributor = None
            #get version ID
            versionID = self.current_version_to_versionID[VersionNumber-1]
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
        elif page.page_platform  == 'xWIKI':
            # first, we need to find the latest minor version for the major version which were provided to method
            # +str(self.current_xWiki_page['wiki'])+ is temporally removed, since it looks more logical to use only 1 wiki
            response = self.xWikiAPI.get_page_version_content_and_author(self.current_xWiki_page['space'], self.current_xWiki_page['name'], str(VersionNumber)+'.1')
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
                        self.TotalExcluded +=1
        if excluded == True:
            return False
        else:
            return True
class Page:
    def __init__(self, page_title, current_platform):
        self.page_title = page_title
        self.page_id = ''
        self.page_versions = ''
        self.page_author = ''
        self.contributors = {}
        self.page_creation_date = ''
        self.PageVersionsDict = []
        self.VersionsGlobalArray = []
        self.TotalContribute = {}
        self.TOTALCharacters = 0
        self.page_platform = current_platform
        self.dbVersion = ''
        self.pageSQL_id = ''

    def add_new_page_version(self, VersionNumberContentContributor):
        if VersionNumberContentContributor is None:
            print('Kernel panic!')
            exit()
        if self.page_platform == 'Confluence':
            try:
                self.PageVersionsDict.append([VersionNumberContentContributor[0], VersionNumberContentContributor[1]['body']['storage']['value']])
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
        elif self.page_platform  == 'xWIKI':
            try:
                self.PageVersionsDict.append([VersionNumberContentContributor[0], VersionNumberContentContributor[1]])
                self.contributors[VersionNumberContentContributor[0]] = VersionNumberContentContributor[2]
            except:
                print('Unable to add new Version into PageVersionsDict', VersionNumberContentContributor)
                exit()
class SQLConnector:
    def __init__(self, SQLConfig):
        self.connection = pyodbc.connect(
            'DRIVER=' + SQLConfig.Driver + ';PORT=1433;SERVER=' + SQLConfig.Server + ';PORT=1443;DATABASE='
            + SQLConfig.Database + ';UID=' + SQLConfig.Username + ';PWD=' + SQLConfig.Password)
        self.cursor = self.connection.cursor()
    def GetPageSQLID(self, CurrentPage):
        self.cursor.execute(
            "select [id] from [dbo].[KnownPages] where [page_id] = '" + str(CurrentPage.page_id) + "'")
        raw = self.cursor.fetchone()
        return raw[0]
    def GetPageSQLID_and_characters_total_by_title(self, title):
        self.cursor.execute(
            "select [id],[characters_total]  from [dbo].[KnownPages] where [page_title] = ?",title)
        raw = self.cursor.fetchone()
        #if raw is None:
        #    return None
        return raw
    def GetPageSQLID_and_characters_total_by_title_and_platform(self, title,platform):
        self.cursor.execute(
            "select [id],[characters_total]  from [dbo].[KnownPages] where [page_title] = ? and platform=?", title,platform)
        raw = self.cursor.fetchone()
        # if raw is None:
        #    return None
        return raw
    def GetUserIDbyName(self, username):
        self.cursor.execute(
            "select [id] from [dbo].[KnownPages_Users] where [user_name] = ?", username)
        raw = self.cursor.fetchone()
        if raw is not None:
            return raw[0]
        else:
            return None
    def GetUserKarmaRawScore_byID(self, id):
        self.cursor.execute(
            "EXEC get_user_karma_raw_score @id = ?", id)
        raw = self.cursor.fetchone()
        if raw is not None:
            return raw[0]
        else:
            return None
    def GetPageKarmaAndVotes_byID(self, page_id):
        self.cursor.execute(
            "EXEC dbo.[get_page_karma_and_votes] @page_id = ?", page_id)
        raw = self.cursor.fetchone()
        if raw is not None:
            return raw
        else:
            return None
    def GetUserKarmaDetailedScore_byID(self, id):
        self.cursor.execute(
            "EXEC [dbo].[get_user_karma_current_score_detailed] @user_id = ?", id)
        while self.cursor.nextset():  # NB: This always skips the first resultset
            try:
                raw = self.cursor.fetchall()
                break
            except pyodbc.ProgrammingError:
                continue
        if raw is not None:
            return raw
        else:
            return None
    def GetUserKarmaScore_byID(self, id):
        self.cursor.execute(
            "EXEC get_user_karma_current_score @user_id = ?", id)
        raw = self.cursor.fetchone()
        if raw is not None:
            return raw[0]
        else:
            return None
    def MakeNewKarmaSlice_byUserID(self, id):
        self.cursor.execute(
            "exec [dbo].[make_new_karma_slice] @user_id = ?", id)
        raw = self.cursor.fetchone()
        if raw is not None:
            self.cursor.connection.commit()
            return raw[0]
        else:
            return None
    def GetKarmaSlicesByUSERIDandDates(self, user_id,date_start,date_end):
        date_end_year = '%02d' % date_end.year
        date_end_month = '%02d' % date_end.month
        date_end_day = '%02d' % date_end.day
        date_start_year = '%02d' % date_start.year
        date_start_month = '%02d' % date_start.month
        date_start_day = '%02d' % date_start.day
        try:
            self.cursor.execute(
                "select [karma_score], CONVERT(varchar(max), DATEDIFF(second,{d '1970-01-01'},[change_time])) as [change_time] FROM [Karma].[dbo].[UserKarma_slice] where [user_id] = ? and change_time between CONVERT(datetime, ?+?+?) and CONVERT(datetime, ?+?+?)", user_id, date_start_year, date_start_month,date_start_day,date_end_year, date_end_month,date_end_day )
            raw = self.cursor.fetchall()
            if raw is not None:
                return raw
            else:
                return None
        except:
            print("Sad story, but your query is shit")
            print(
                "select [karma_score], [change_time] FROM [Karma].[dbo].[UserKarma_slice] where [user_id] = " + user_id + " and change_time between CONVERT(datetime, " + str(date_start.year) + str(date_start.month) + str(date_start.day) + ") and CONVERT(datetime, " + str(date_end.year) + str(date_end.month) + str(date_end.day) + ")")
    def GetUserRawKarmabyID(self, id):
        self.cursor.execute(
            "EXEC get_user_karma_raw @id = ?", id)
        raw = self.cursor.fetchall()
        if raw is not None:
            return raw
        else:
            return None
    def GetPagePageContribution(self, CurrentPage):
        self.cursor.execute(
            "select [datagram_contribution] from [dbo].[KnownPages_contribution] where [KnownPageID] = '" + CurrentPage.pageSQL_id + "'")
        raw = self.cursor.fetchone()
        if raw:
            return raw[0]
        else:
            return None
    def GetDatagrams(self, CurrentPage):
        self.cursor.execute(
            "select [datagram], [contributors_datagram] from [dbo].[KnownPages_datagrams] where [KnownPageID] = ?", CurrentPage.pageSQL_id)
        raw = self.cursor.fetchone()
        return raw
    def PushNewPage(self, CurrentPage):
        try:
            self.cursor.execute(
                "insert into [dbo].[KnownPages] ([ID],[page_title],[page_id],[author],[author_ID],[added],"
                "[last_modified],[version],[last_check],[is_uptodate], [characters_total], [platform]) values (NEWID(),?,?,?,?,getdate(),getdate(),?,getdate(),'1',?,?)",
                CurrentPage.page_title, CurrentPage.page_id, CurrentPage.page_author, 'Null', CurrentPage.page_versions, CurrentPage.TOTALCharacters, CurrentPage.page_platform)
            self.connection.commit()
            print(datetime.now(),CurrentPage.page_title + ' was added to DB')
            pageID = self.GetPageSQLID(CurrentPage)
            return pageID
        except pyodbc.DataError:
            self.connection.rollback()
            error_handler = traceback.format_exc()
            print(datetime.now(),'Initial add of ' + CurrentPage.page_title + ' rolled back due to the following error:\n' + error_handler)
            print("insert into [dbo].[KnownPages] ([ID],[page_title],[page_id],[author],[author_ID],[added],"
                "[last_modified],[version],[last_check],[is_uptodate], [characters_total], [platform]) values (NEWID(),'"+CurrentPage.page_title+"','"+CurrentPage.page_id+"','"+CurrentPage.page_author+"','Null',getdate(),getdate(),"+str(CurrentPage.page_versions)+",getdate(),'1','"+str(CurrentPage.TOTALCharacters)+"','"+CurrentPage.page_platform+"')")
            self.connection.rollback()
            error_handler = traceback.format_exc()
            print(datetime.now(),
                  'Initial add of ' + CurrentPage.page_title + ' rolled back due to the following error: page with this [page_id] already exists, need to make incremental run')
    def PushNewDatagram(self, CurrentPage):
        binaryGlobalArray = pickle.dumps(CurrentPage.VersionsGlobalArray, 4)
        binaryContributors = pickle.dumps(CurrentPage.contributors, 4)
        try:
            self.cursor.execute(
                "insert into [dbo].[KnownPages_datagrams] ([ID],[KnownPageID],[datagram], [contributors_datagram]) values (NEWID(),?,?,?)",
                CurrentPage.pageSQL_id,binaryGlobalArray,binaryContributors)
            self.connection.commit()
        except:
            self.connection.rollback()
            self.cursor.execute(
                "delete [dbo].[KnownPages] where ID =?",
                CurrentPage.pageSQL_id)
            self.connection.commit()
            error_handler = traceback.format_exc()
            print(datetime.now(),'Initial add of ' + CurrentPage.page_title + ' rolled back due to the following error while adding its datagram:\n' + error_handler)
    def PushContributionDatagramByID(self, CurrentPage):
        binaryTotalContribute = pickle.dumps(CurrentPage.TotalContribute, 4)
        #is already added?
        SQLContribution =  self.GetPagePageContribution(CurrentPage)
        if SQLContribution == None:
            self.cursor.execute(
                "insert into [dbo].[KnownPages_contribution] ([KnownPageID],[datagram_contribution]) values (?,?)",
                CurrentPage.pageSQL_id, binaryTotalContribute)
            self.connection.commit()
        else:
            self.cursor.execute(
                "update [dbo].[KnownPages_contribution] set [datagram_contribution] = ? where KnownPageID=?",
                binaryTotalContribute,CurrentPage.pageSQL_id)
            self.connection.commit()
    def PushContributionByUser(self, CurrentPage):
        for user, value in CurrentPage.TotalContribute.items():
            self.cursor.execute(
                "select [ID] from [dbo].[KnownPages_Users] where [user_name] = ?",
                user)
            raw = self.cursor.fetchone()
            if raw:
                UserID = raw[0]
            else:
                self.cursor.execute(
                    "insert into [dbo].[KnownPages_Users] ([ID],[user_name]) values (NEWID(),?)",
                    user)
                self.connection.commit()
                self.cursor.execute(
                    "select [ID] from [dbo].[KnownPages_Users] where [user_name] = ?",
                    user)
                raw = self.cursor.fetchone()
                UserID = raw[0]
            self.cursor.execute(
                "insert into [dbo].[KnownPages_UsersContribution] ([UserID],[KnownPageID],[contribution]) values (?,?,?)",
                UserID, CurrentPage.pageSQL_id, value)
            self.connection.commit()
            if user == CurrentPage.page_author:
                self.cursor.execute(
                    "update [dbo].[KnownPages] set author_ID = ? where ID = ?",
                    UserID, CurrentPage.pageSQL_id)
                self.connection.commit()
    def CheckExistencebyID(self, CurrentPage):
        self.cursor.execute(
            "select [version] from [dbo].[KnownPages] where [page_id] = '" + str(CurrentPage.page_id)+ "'")
        row = self.cursor.fetchone()
        if row:
            return int(row[0])
        else:
            return None
    def UpdateKnownPagesLast_check(self, CurrentPage):
        if CurrentPage.page_versions == CurrentPage.dbVersion:
            try:
                self.cursor.execute(
                    "update [dbo].[KnownPages] set [is_uptodate]=1, [last_check]=? where [page_id]=?",
                    str(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")[:-3]), str(CurrentPage.page_id))
                self.connection.commit()
            except:
                self.connection.rollback()
                error_handler = traceback.format_exc()
                print(datetime.now(),
                      'Update of last_check status of ' + CurrentPage.page_title + ' rolled back due to the following error:\n' + error_handler)
                print('query:', "update [dbo].[KnownPages] set [is_uptodate]=1, [last_check]="+str(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")[:-3])+" where [page_id] ="+str(CurrentPage.page_id))
        else:
            try:
                self.cursor.execute(
                    "update [dbo].[KnownPages] set [is_uptodate]=0, [last_check]=? where [page_id]=?",
                    str(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")[:-3]), CurrentPage.page_id)
                self.connection.commit()
            except:
                self.connection.rollback()
                error_handler = traceback.format_exc()
                print(datetime.now(),
                      'Update of last_check status of ' + CurrentPage.page_title + ' rolled back due to the following error:\n' + error_handler)
                print('query:',
                      "update [dbo].[KnownPages] set [is_uptodate]=0, [last_check]="+str(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")[:-3])+" where [page_id] =" + str(
                          CurrentPage.page_id))
    def UpdatePagebyID(self, CurrentPage):
        self.cursor.execute(
            "update [dbo].[KnownPages] set [is_uptodate]='1', [last_check]=getdate(),[last_modified]=getdate(), version = ?, characters_total = ? where [id] =?",
            CurrentPage.page_versions, CurrentPage.TOTALCharacters, CurrentPage.pageSQL_id)
        self.connection.commit()
    def UpdateDatagramByID(self, CurrentPage):
        binaryGlobalArray = pickle.dumps(CurrentPage.VersionsGlobalArray, 4)
        binaryContributors = pickle.dumps(CurrentPage.contributors, 4)
        self.cursor.execute(
            "update [dbo].[KnownPages_datagrams] set datagram=?,contributors_datagram=? where [KnownPageID] =?",
            binaryGlobalArray, binaryContributors, CurrentPage.pageSQL_id)
        self.connection.commit()
    def NewPageVote(self, page_SQL_id, user_id, direction):
        # checking if this user has already voted for this page
        direction = bool(int(direction))
        try:
            self.cursor.execute(
                "select id, [direction] from [dbo].[Page_Karma_votes] where page_id=? and user_id =?",
                page_SQL_id, user_id)
            raw = self.cursor.fetchone()
        except Exception as exception:
            print('select id from [dbo].[Page_Karma_votes] where page_id='+page_SQL_id+' and user_id ='+user_id+' was aborted due to the following error:')
            print(exception)
        if raw is not None:
            current_direction = raw[1]
            if current_direction is True and direction is True or current_direction is False and direction is False:
                return 'Error: Already voted'
            if current_direction is False and direction is True or current_direction is True and direction is False:
                self.cursor.execute(
                    "delete from [dbo].[Page_Karma_votes] where id =?",
                    raw[0])
                self.connection.commit()
                return 'Vote deleted'
        else:
            self.cursor.execute(
                "insert into [dbo].[Page_Karma_votes] values(NEWID(), ?, ?, ?, GETDATE())",
                page_SQL_id, user_id, direction)
            self.connection.commit()
            return 'Vote committed'
    def GetDatagramsByPageTitleandPlatform(self, page_title,platform):
        self.cursor.execute(
            "select [id] from [dbo].[KnownPages] where [page_title] like ? and platform = ?", page_title, platform)
        raw = self.cursor.fetchone()
        if raw:
            page_id = raw[0]
        else:
            return None
        self.cursor.execute(
            "select [datagram], [contributors_datagram] from [dbo].[KnownPages_datagrams] where [KnownPageID] = ?", page_id)
        raw = self.cursor.fetchone()
        if raw:
            datagram = pickle.loads(raw[0])
            contributors_datagram = pickle.loads(raw[1])
            return datagram, contributors_datagram
class ContribBuilder:
    def __init__(self, logging_mode='silent'):
        self.temp_array = []
        self.some_other_array = []
        self.logging_mode = logging_mode
    def Initialcompare(self, CurrentPage): #compares all existing version from 1st to the last
        for index, VersionContent in enumerate(CurrentPage.PageVersionsDict):
            #print('Iteration number', index)
            try:
                StageNEXT = VersionContent
                if index == 0:
                    StageFIRST = [-1, '']
                else:
                    StageFIRST = CurrentPage.PageVersionsDict[index - 1]
                #print('{} => {}'.format(StageFIRST, StageNEXT))
                for i, s in enumerate(difflib.ndiff(StageFIRST[1], StageNEXT[1])):
                    if s[0] == '+':
                        #print(u'Add "{}" to position {}'.format(s[-1], i))
                        CurrentPage.VersionsGlobalArray.insert(i, [s[-1], StageNEXT[0]])
                    elif s[0] == '-':
                        #print(u'Delete "{}" from position {}'.format(s[-1], i))
                        CurrentPage.VersionsGlobalArray[i] = None
                self.temp_array = []
                self.some_other_array = []
                self.temp_array[:] = []
                self.some_other_array[:] = []
                self.temp_array = copy.deepcopy(CurrentPage.VersionsGlobalArray)
                CurrentPage.VersionsGlobalArray[:] = []
                self.some_other_array = [x for x in self.temp_array if x is not None]
                CurrentPage.VersionsGlobalArray = copy.deepcopy(self.some_other_array)
                self.temp_array[:] = []
                self.some_other_array[:] = []
            except Exception as error:
                print('initial compare of page was failed with error:', error)
                for each in CurrentPage.VersionsGlobalArray:
                    if each is None:
                        print(each, 'is none, but WTF?')
                print('CurrentPage.VersionsGlobalArray', CurrentPage.VersionsGlobalArray)
                exit()
    def Incrementalcompare(self, CurrentPage):  # compares all existing version from CurrentPage.dbVersion to the CurrentPage.versions
        for index, VersionContent in enumerate(CurrentPage.PageVersionsDict):
            if self.logging_mode != 'silent': print('Iteration number', index)
            if index == len(CurrentPage.PageVersionsDict)-1: break
            StageFIRST = VersionContent
            StageNEXT = CurrentPage.PageVersionsDict[index + 1]
            try:
                if self.logging_mode != 'silent':
                    print(StageFIRST)
                    print(StageNEXT)
                array_to_compare = difflib.ndiff(StageFIRST[1], StageNEXT[1])
                for i, s in enumerate(array_to_compare): # problem: each s[0] == ' ' extends loop. Need to find a way to ignore them
                    if s[0] == '+':
                        if self.logging_mode != 'silent': print(u'Add "{}" to position {}'.format(s[-1], i))
                        CurrentPage.VersionsGlobalArray.insert(i, [s[-1], StageNEXT[0]])
                    elif s[0] == '-':
                        if self.logging_mode != 'silent': print(u'Delete "{}" from position {}'.format(s[-1], i))
                        CurrentPage.VersionsGlobalArray[i] = None
                if self.logging_mode != 'silent': print('Done with compare, removing deleted characters...')
                self.temp_array[:] = []
                self.some_other_array[:] = []
                self.temp_array = copy.deepcopy(CurrentPage.VersionsGlobalArray)
                CurrentPage.VersionsGlobalArray[:] = []
                self.some_other_array = [x for x in self.temp_array if x is not None]
                CurrentPage.VersionsGlobalArray = copy.deepcopy(self.some_other_array)
            except Exception as error:
                print('Incremental compare of page was failed with error:', error)
                for each in CurrentPage.VersionsGlobalArray:
                    if each is None:
                        print(each, 'is none, but WTF?')
                        break
                print('CurrentPage.VersionsGlobalArray', CurrentPage.VersionsGlobalArray)
                print('Len of array', len(CurrentPage.VersionsGlobalArray))
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
            print(self.TaskStartTime, pages_found, 'pages were found in all spaces, excluded:',excluded)
        else:
            print(self.TaskStartTime, pages_found, 'pages were found in all spaces, excluded:',excluded)
    def page_analysis_started(self,title):
        self.PageAnalysisStartTime = datetime.now()
        if self.LogLevel != 'silent':
            print(self.PageAnalysisStartTime, title + ': Task initialized, getting sources...')
    def page_processing_started(self, CurrentPage):
        if CurrentPage.dbVersion == None:
            if self.LogLevel != 'silent':
                print('"'+CurrentPage.page_title+'" will be processed in FULL mode')
        elif CurrentPage.dbVersion < CurrentPage.page_versions:
            if self.LogLevel != 'silent':
                print('"' + CurrentPage.page_title + '" will be processed in INCREMENTAL mode')
        elif CurrentPage.dbVersion == CurrentPage.page_versions:
            if self.LogLevel != 'silent':
                print('"' + CurrentPage.page_title + '" is up-to-date')
    def page_processing_target(self, CurrentPage):
        self.PageAnalysisEndTime = datetime.now()
        if self.LogLevel != 'silent':
            print(self.PageAnalysisEndTime,'Page "' + CurrentPage.page_title + '" with ID' + str(
                CurrentPage.page_id) + ', created by ' + CurrentPage.page_author + ' was parsed, ' + str(
                CurrentPage.page_versions) + ' versions were found', '\n', 'Sources are collected, calculating difference... ')
    def page_counting_finished(self, CurrentPage):
        self.PageCountingEndTime = datetime.now()
        if self.LogLevel != 'silent':
            print(self.PageCountingEndTime,'... Done')
    def page_summary(self, CurrentPage):
        if self.LogLevel != 'silent':
            print('Characters in TOTAL: ', CurrentPage.TOTALCharacters)
            if CurrentPage.TOTALCharacters != 0:
                for Contributor, Value in CurrentPage.TotalContribute.items():
                    Percent = (Value / CurrentPage.TOTALCharacters) * 100
                    print('Contribution of ' + Contributor + ' = ' + str(Percent) + '%' + ' (' + str(Value) + ') characters')
            print('Time elapsed: Analysis:', self.PageAnalysisEndTime - self.PageAnalysisStartTime, '+ Diff calc:', self.PageCountingEndTime -  self.PageAnalysisEndTime, '=', self.PageCountingEndTime - self.PageAnalysisStartTime)
        self.PageAnalysisStartTime = None
        self.PageAnalysisEndTime = None
        self.PageCountingEndTime = None
    def log_task_ended(self):
        self.TaskEndTime = datetime.now()
        TotalElapsed = self.TaskEndTime - self.TaskStartTime
        print(self.TaskEndTime, 'Total time wasted', TotalElapsed)
    def skip_some_page(self, title):
        print(datetime.now(), title,'is redirect or unable to find ID, skipping')
class xWikiClient:
    def __init__(self, api_root, auth_user=None, auth_pass=None):
        self.api_root = api_root
        self.auth_user = auth_user
        self.auth_pass = auth_pass

    def _build_url(self, path):
        url = self.api_root + "/".join(path)
        return url

    def _make_request(self, path, data):
        url = self._build_url(path)
        data['media'] = 'json'

        auth = None
        if self.auth_user and self.auth_pass:
            auth = self.auth_user,self.auth_pass

        response = requests.get(url, params=data, auth=auth)
        response.raise_for_status()
        return response.json()

    def _make_put(self, path, data):
        url = self._build_url(path)
        data['media'] = 'json'

        auth = None
        if self.auth_user and self.auth_pass:
            auth = self.auth_user,self.auth_pass

        response = requests.put(url, data=data, auth=auth)
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
            pages.append(details['name'])
        return pages

    def page(self, space, page):
        path = ['spaces', space, 'pages', page]
        data = {}
        try:
            content = self._make_request(path, data)
            return content
        except:
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

    def submit_page(self, space, page, content, title=None, parent=None):
        path = ['spaces', space, 'pages', page]
        data = {'content': content}
        if title:
            data['title'] = title
        else:
            data['title'] = page

        if parent:
            data['parent'] = parent

        status = self._make_put(path, data)

        if status == 201:
            return "Created"
        elif status == 202:
            return "Updated"
        elif status == 304:
            return "Unmodified"

    def get_page_history(self, space, page_name):
        path = ['spaces',space, 'pages', page_name, 'history']
        data = {}
        content = self._make_request(path, data)
        return content

    def get_page_version_content_and_author(self, space, page_name, version):
        path = ['spaces',space, 'pages', page_name, 'history', version]
        data = {}
        content = self._make_request(path, data)
        return content['content'], content['author']
class ExclusionsDict(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(ExclusionsDict, self).__setitem__(key, [])
        self[key].append(value)

class MysqlConnector:
    def __init__(self, Config: Configuration.MySQLConfig):
        self.cnx = mysql.connector.connect(user=Config.user, password=Config.password,
                              host=Config.host,
                              port=Config.port,
                              database=Config.database)
        self.cursor = self.cnx.cursor(buffered=True)
    def generate_new_uniqe_xwikilike_id(self) -> str:
        while 1:
            test_id = str(random.randrange(3311023617254460905, 9178059011723785643, 1)) # see xwiki database to realise,  f** why I use such range here
            result = self.check_if_page_exists(test_id)
            if result is False:
                return test_id
    def check_if_page_exists(self, ID: str):
        query = ("SELECT XWD_TITLE FROM xwikidoc "
                 "WHERE XWD_ID = %(ID)s")
        data = {
            'ID': ID
        }
        self.cursor.execute(query, data)
        if self.cursor.rowcount == 0:
            return False
        else:
            return True
    def insert_into_xwikidoc(self, data_handler: xWIKIDB_data_handler):
        """
        # original way to post a query, doesn't work :(
        add_page_into_xwikidoc = ("insert into xwikidoc"
                                  "(XWD_FULLNAME, XWD_NAME, XWD_TITLE, XWD_LANGUAGE, XWD_DEFAULT_LANGUAGE, XWD_TRANSLATION, XWD_DATE, XWD_CONTENT_UPDATE_DATE, XWD_CREATION_DATE, XWD_AUTHOR, XWD_CONTENT_AUTHOR, XWD_CREATOR, XWD_WEB, XWD_CONTENT, XWD_VERSION, XWD_CUSTOM_CLASS, XWD_PARENT, XWD_CLASS_XML, XWD_ELEMENTS, XWD_DEFAULT_TEMPLATE, XWD_VALIDATION_SCRIPT, XWD_COMMENT, XWD_MINOREDIT, XWD_SYNTAX_ID, XWD_HIDDEN, XWD_ID) "
                                  "values (%(XWD_FULLNAME)s, %(XWD_NAME)s, %(XWD_TITLE)s, %(XWD_LANGUAGE)s, %(XWD_DEFAULT_LANGUAGE)s, %(XWD_TRANSLATION)s, %(XWD_DATE)s, %(XWD_CONTENT_UPDATE_DATE)s, %(XWD_CREATION_DATE)s, %(XWD_AUTHOR)s, %(XWD_CONTENT_AUTHOR)s, %(XWD_CREATOR)s, %(XWD_WEB)s, %(XWD_CONTENT)s, %(XWD_VERSION)s, %(XWD_CUSTOM_CLASS)s, %(XWD_PARENT)s, %(XWD_CLASS_XML)s, %(XWD_ELEMENTS)s, %(XWD_DEFAULT_TEMPLATE)s, %(XWD_VALIDATION_SCRIPT)s, %(XWD_COMMENT)s, %(XWD_MINOREDIT)s, %(XWD_SYNTAX_ID)s, %(XWD_HIDDEN)s, %(XWD_ID)s")
        # hardcoded variant:
        """
        query = ('insert into xwikidoc'
                 '(XWD_FULLNAME, XWD_NAME, XWD_TITLE, XWD_LANGUAGE, XWD_DEFAULT_LANGUAGE, XWD_TRANSLATION, XWD_DATE, XWD_CONTENT_UPDATE_DATE, XWD_CREATION_DATE, XWD_AUTHOR, XWD_CONTENT_AUTHOR, XWD_CREATOR, XWD_WEB, XWD_CONTENT, XWD_VERSION, XWD_CUSTOM_CLASS, XWD_PARENT, XWD_CLASS_XML, XWD_ELEMENTS, XWD_DEFAULT_TEMPLATE, XWD_VALIDATION_SCRIPT, XWD_COMMENT, XWD_MINOREDIT, XWD_SYNTAX_ID, XWD_HIDDEN, XWD_ID) '
                 'values ('
                         '\'' + data_handler.XWD_FULLNAME + '\','
                         '\'' + data_handler.XWD_NAME + '\','
                         '\'' + data_handler.XWD_TITLE + '\','
                         '\'' + data_handler.XWD_LANGUAGE + '\','
                         '\'' + data_handler.XWD_DEFAULT_LANGUAGE + '\','
                         '\'' + data_handler.XWD_TRANSLATION + '\','
                         '\'' + data_handler.XWD_DATE + '\','
                         '\'' + data_handler.XWD_CONTENT_UPDATE_DATE + '\','
                         '\'' + data_handler.XWD_CREATION_DATE + '\','
                         '\'' + data_handler.XWD_AUTHOR + '\','
                         '\'' + data_handler.XWD_CONTENT_AUTHOR + '\','
                         '\'' + data_handler.XWD_CREATOR + '\','
                         '\'' + data_handler.XWD_WEB + '\','
                         '\'' + data_handler.XWD_CONTENT + '\','
                         '\'' + data_handler.XWD_VERSION + '\','
                         '\'' + data_handler.XWD_CUSTOM_CLASS + '\','
                         '\'' + data_handler.XWD_PARENT + '\','
                         '\'' + data_handler.XWD_CLASS_XML + '\','
                         '\'' + data_handler.XWD_ELEMENTS + '\','
                         '\'' + data_handler.XWD_DEFAULT_TEMPLATE + '\','
                         '\'' + data_handler.XWD_VALIDATION_SCRIPT + '\','
                         '\'' + data_handler.XWD_COMMENT + '\','
                         ''  + data_handler.XWD_MINOREDIT + ','
                         '\'' + data_handler.XWD_SYNTAX_ID + '\''
                         ',' + data_handler.XWD_HIDDEN + ','
                         '\'' + data_handler.XWD_ID + '\''
                         ')'
                 )
        self.cursor.execute(query)
        self.cnx.rollback()
        # self.cnx.commit()
        return True
    def insert_into_xwikispace(self, data_handler: xWIKIDB_data_handler):
        #query = ('insert into xwikispace (XWS_REFERENCE, XWS_NAME, XWS_PARENT, XWS_HIDDEN, XWS_ID) '
        #         'values ('Sandbox.ololo_page.test_lol.new_test_lol', 'new_test_lol', 'Sandbox.ololo_page.test_lol', 0, 6712117962662618003)')
        query = ('insert into xwikispace (XWS_REFERENCE, XWS_NAME, XWS_PARENT, XWS_HIDDEN, XWS_ID) '
                 'values ('
                 '\'' + data_handler.XWS_REFERENCE +'\','
                 '\'' + data_handler.XWS_NAME + '\','
                 '\'' + data_handler.XWS_PARENT + '\','
                 '' + data_handler.XWS_HIDDEN + ','
                 '\'' + data_handler.XWS_ID + '\''
                 ')'
                 )
        self.cursor.execute(query)
        self.cnx.rollback()
        #self.cnx.commit()
        return True
    def update_xwikircs(self, data_handler: xWIKIDB_data_handler):
        xml = '<?xml version="1.0" encoding="UTF-8"?>' \
              '\\n<xwikidoc reference="' + data_handler.XWD_FULLNAME + '" locale="">' \
                  '\\n<web>' +  data_handler.XWS_REFERENCE+ '</web>' \
                  '\\n<name>WebHome</name>' \
                  '\\n<language></language>' \
                  '\\n<defaultLanguage>en</defaultLanguage>' \
                  '\\n<translation>0</translation>' \
                  '\\n<parent>' +  data_handler.XWS_PARENT + '.WebHome</parent>' \
                  '\\n<creator>' +  data_handler.XWD_CREATOR + '</creator>' \
                  '\\n<author>' +  data_handler.XWD_AUTHOR + '</author>' \
                  '\\n<customClass></customClass>' \
                  '\\n<contentAuthor>' + data_handler.XWD_CONTENT_AUTHOR + '</contentAuthor>' \
                  '\\n<creationDate>'+ str(int(time.mktime(time.strptime( data_handler.XWD_CREATION_DATE, '%Y-%m-%d %H:%M:%S')))) + '</creationDate>' \
                  '\\n<date>'  + str(int(time.mktime(time.strptime( data_handler.XWD_DATE, '%Y-%m-%d %H:%M:%S')))) + '</date>' \
                  '\\n<contentUpdateDate>'  + str(int(time.mktime(time.strptime( data_handler.XWD_CONTENT_UPDATE_DATE, '%Y-%m-%d %H:%M:%S')))) + '</contentUpdateDate>' \
                  '\\n<version>' + data_handler.XWD_VERSION + '</version>' \
                  '\\n<title>' + data_handler.XWS_NAME + '</title>' \
                  '\\n<defaultTemplate></defaultTemplate>' \
                  '\\n<validationScript></validationScript>' \
                  '\\n<comment></comment>' \
                  '\\n<minorEdit>false</minorEdit>' \
                  '\\n<syntaxId>' + data_handler.XWD_SYNTAX_ID + '</syntaxId>' \
                  '\\n<hidden>false</hidden>' \
                  '\\n<content>' +  data_handler.XWD_CONTENT + '</content>' \
              '</xwikidoc>\\n'
        query = ('update xwikircs set '
                 'XWR_ISDIFF=0, '
                 'XWR_PATCH = \''+ xml + '\' '
                 'where XWR_DOCID = \'' + data_handler.XWD_ID + '\' and XWR_VERSION1 = \''+   data_handler.XWD_ID[:1] + '\' and XWR_VERSION2 = 1')
        self.cursor.execute(query)
        self.cnx.rollback()
        #self.cnx.commit()
        return True
    def insert_into_xwikilistitems(self, data_handler: xWIKIDB_data_handler):
        # selecting XWL_ID
        query = ('select XWO_ID from xwikiobjects '
                 'where XWO_NAME = \'' + data_handler.XWD_AUTHOR + '\' and XWO_CLASSNAME = \'XWiki.WatchListClass\'')
        self.cursor.execute(query)
        if self.cursor.rowcount == 0:
            print('XWL_ID not found for user:', data_handler.XWD_AUTHOR)
            return False
        elif self.cursor.rowcount == 1:
            for id in self.cursor:
                XWL_ID = id[0]
        else:
            print('Logic failure: more than 1 XWL_ID for user:', data_handler.XWD_AUTHOR)
            return False
        if data_handler.XWL_ID is None or data_handler.XWL_ID != XWL_ID:
            data_handler.XWL_ID = XWL_ID
            # query = ('insert into xwikilistitems (XWL_ID, XWL_NAME, XWL_NUMBER, XWL_VALUE) values (-1600470005484774485, 'documents', 12, 'xwiki:Sandbox.ololo_page.test_lol.new_test_lol.WebHome')
            query = ('insert into xwikilistitems (XWL_ID, XWL_NAME, XWL_NUMBER, XWL_VALUE) '
                     'values (\'' + data_handler.XWL_ID + '\', \'documents\', 12, \'xwiki: '+data_handler.XWD_FULLNAME+'\'))')
            self.cursor.execute(query)
            self.cnx.rollback()
            # pages_num = self.cursor.lastrowid
            # self.cnx.commit()
            return True
