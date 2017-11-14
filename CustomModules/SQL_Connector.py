import pickle
import pyodbc
import traceback
from datetime import datetime
from CustomModules import PageMechanics
import CustomModules
import Configuration
import logging


class SQLConnector:
    def __init__(self, sql_config: Configuration.SQLConfig):
        self.connection = pyodbc.connect(
            'DRIVER=' + sql_config.Driver + ';PORT=1433;SERVER=' + sql_config.Server + ';PORT=1443;DATABASE='
            + sql_config.Database + ';UID=' + sql_config.Username + ';PWD=' + sql_config.Password)
        self.cursor = self.connection.cursor()

    def select_page_id_from_dbo_knownpages(self, page_title: str, platform: str):
        self.cursor.execute(
            "select [page_id] FROM [dbo].[KnownPages] where [page_title] = ? and [platform]= ?", page_title,
            platform)
        raw = self.cursor.fetchone()
        if raw is not None:
            return raw.page_id
        return None

    def select_id_from_dbo_knownpages(self, page_object: CustomModules.PageMechanics.PageGlobal=None, platform: str=None, page_id: str=None, page_title: str=None):
        if platform is None:
            if isinstance(page_object, CustomModules.PageMechanics.PageXWiki):
                platform = 'xwiki'
            elif isinstance(page_object, CustomModules.PageMechanics.PageConfluence):
                platform = 'confluence'
            elif isinstance(page_object, CustomModules.PageMechanics.PageMediaWiki):
                platform = 'mediawiki'
            else:
                return None
        if page_id is not None and page_title is None:
            if platform.lower() == 'xwiki' and not page_id.startswith('xwiki:'):
                page_id = 'xwiki:' + page_id
            self.cursor.execute("select [id] from [dbo].[KnownPages] where [page_id] = ? and [platform] LIKE LOWER(?)", page_id, platform)
            raw = self.cursor.fetchone()
            if raw:
                return raw.id
            return None
        if page_title is not None and page_id is None:
            self.cursor.execute(
                "select [id] from [dbo].[KnownPages] where [page_title] = ? and [platform] LIKE LOWER(?)", page_title, platform)
            raw = self.cursor.fetchone()
            if raw:
                return raw.id
            return None

    def select_id_characters_total_from_dbo_knownpages(self, platform: str, page_id: str=None, page_title: str=None):
        if page_id is not None:
            if platform.lower() == 'xwiki':
                page_id = 'xwiki:' + page_id
            self.cursor.execute(
                "select [id],[characters_total] FROM [dbo].[KnownPages] where [page_id] = ? and [platform] LIKE LOWER(?)",
                page_id, platform)
            raw = self.cursor.fetchone()
            if raw:
                return raw.id, raw.characters_total
            return None
        if page_title is not None:
            self.cursor.execute(
                "select [id], [characters_total] from [dbo].[KnownPages] where [page_title] = ? and [platform] LIKE LOWER(?)",
                page_title,
                platform)
            raw = self.cursor.fetchone()
            if raw:
                return raw.id, raw.characters_total
            return None

    def select_id_from_dbo_knownpages_users(self, username: str):
        self.cursor.execute(
            "select [id] from [dbo].[KnownPages_Users] where [user_name] = ?", username)
        raw = self.cursor.fetchone()
        if raw:
            return raw.id
        return None

    def select_karma_score_from_userkarma_slice(self, user_id: str, date_start: datetime, date_end: datetime):
        date_end_year = '%02d' % date_end.year
        date_end_month = '%02d' % date_end.month
        date_end_day = '%02d' % date_end.day
        date_start_year = '%02d' % date_start.year
        date_start_month = '%02d' % date_start.month
        date_start_day = '%02d' % date_start.day
        try:
            self.cursor.execute(
                "select [karma_score], CONVERT(varchar(max), DATEDIFF(second,{d '1970-01-01'},[change_time])) as [change_time] FROM [dbo].[UserKarma_slice] where [user_id] = ? and change_time between CONVERT(datetime, ?+?+?) and CONVERT(datetime, ?+?+?)",
                user_id, date_start_year, date_start_month, date_start_day, date_end_year, date_end_month, date_end_day)
            raw = self.cursor.fetchall()
            if raw:
                return raw
            return None
        except:
            print("Sad story, but your query is a shit")
            print(
                "select [karma_score], [change_time] FROM [dbo].[UserKarma_slice] where [user_id] = " + user_id + " and change_time between CONVERT(datetime, " + str(
                    date_start.year) + str(date_start.month) + str(date_start.day) + ") and CONVERT(datetime, " + str(
                    date_end.year) + str(date_end.month) + str(date_end.day) + ")")

    def select_from_known_bugs_by_filter(self, components_filer: list, product_filter: list, tbfi_filter: list, start: str, end: str) -> list:

        query = "WITH OrderedRecords AS" \
                "(" \
                "SELECT case when [dbo].[KnownBugs].[bug_title] is NULL then [dbo].[KnownPages].[page_title] when [dbo].[KnownBugs].[bug_title] is not NULL then [dbo].[KnownBugs].[bug_title] end as page_title, [dbo].[KnownBugs].[bug_id], [dbo].[KnownBugs].[product], [dbo].[KnownBugs].[tbfi], [dbo].[KnownBugs].[components], [dbo].[KnownPages].page_id," \
                "ROW_NUMBER() OVER (ORDER BY [dbo].[KnownPages].id) AS 'RowNumber' " \
                "FROM [dbo].[KnownBugs] " \
                "left join [dbo].[KnownPages] on [dbo].[KnownBugs].KnownPages_id = [dbo].[KnownPages].id " \
                "WHERE "
        for idx, component in enumerate(components_filer):
            query += "(Charindex('" + component + "',CAST(components AS VARCHAR(MAX)))>0 )"
            if idx != len(components_filer) - 1:
                query += " AND "
        if len(components_filer) != 0 and len(product_filter) > 0:
            query += " AND "
        for idx, product in enumerate(product_filter):
            query += "([product]='" + product + "')"
            if idx != len(product_filter) - 1:
                query += " AND "
        if len(product_filter) != 0 and len(tbfi_filter) > 0:
            query += " AND "
        for idx, tbfi in enumerate(tbfi_filter):
            query += "([tbfi]='" + tbfi + "')"
            if idx != len(tbfi_filter) - 1:
                query += " AND "
        query += ")"
        query += "SELECT [page_title], [bug_id], [product], [tbfi], [components], [page_id], [RowNumber] FROM OrderedRecords WHERE RowNumber BETWEEN " + start + " and " + end + " order by bug_id"
        # print(query)
        self.cursor.execute(query)
        raw = self.cursor.fetchall()
        if raw is None:
            return []
        return raw

    def select_page_title_from_dbo_knownpages(self, native_sql_id: str):
        self.cursor.execute(
            "SELECT [page_title] FROM [dbo].[KnownPages] where [ID] = ?", native_sql_id)
        raw = self.cursor.fetchone()
        if raw:
            return raw.page_title
        return None

    def select_datagram_contribution_from_dbo_knownpages_contribution(self, sql_id: str):
        self.cursor.execute(
            "select [datagram_contribution] from [dbo].[KnownPages_contribution] where [KnownPageID] = ?", sql_id)
        raw = self.cursor.fetchone()
        if raw:
            return raw.datagram_contribution
        return None

    def select_datagram_contributors_datagram_from_dbo_knownpages_datagrams(self, sql_id: str):
        if sql_id is None:
            raise KeyError('sql_id cannot be NONE')
        self.cursor.execute(
            "select [datagram], [contributors_datagram] from [dbo].[KnownPages_datagrams] where [KnownPageID] = ?",
            sql_id)
        raw = self.cursor.fetchone()
        if raw:
            return raw.datagram, raw.contributors_datagram
        return None

    def select_datagrams_from_dbo_knownpages_datagrams(self, page_title: str, platform: str):
        # Used only for migration and export, that's why it's enough to use page_title
        page_id = self.select_id_from_dbo_knownpages(platform=platform, page_title=page_title)
        self.cursor.execute(
            "select [datagram], [contributors_datagram] from [dbo].[KnownPages_datagrams] where [KnownPageID] = ?",
            page_id)
        raw = self.cursor.fetchone()
        if raw:
            datagram = pickle.loads(raw.datagram)
            contributors_datagram = pickle.loads(raw.contributors_datagram)
            return datagram, contributors_datagram
        return None

    def select_page_titles_platforms_by_filter(self, page_title: str = None, query: str = None):
        if page_title is None and query is None:
            return None
        if page_title is not None and query is not None:
            return None
        if query is not None:
            self.cursor.execute(query)
            raw = self.cursor.fetchall()
            if raw:
                return raw
            return None
        elif page_title is not None:
            self.cursor.execute(
                "SELECT page_title, platform FROM [dbo].[KnownPages] where page_title like LOWER('%" + page_title + "%')")
            raw = self.cursor.fetchall()
            if raw:
                return raw
            return None

    def select_version_from_dbo_knownpages(self, page_id: str):
        self.cursor.execute(
            "select [version] from [dbo].[KnownPages] where [page_id] = '" + page_id + "'")
        row = self.cursor.fetchone()
        if row:
            return int(row.version)
        return None

    def select_distinct_product_from_dbo_known_bugs(self)->list:
        self.cursor.execute(
            "SELECT distinct [product] FROM [dbo].[KnownBugs] order by [product]")
        row = self.cursor.fetchall()
        if row:
            result = []
            for line in row:
                result.append(line[0])
            return result
        return None

    def select_distinct_tbfi_from_dbo_known_bugs(self)->list:
        self.cursor.execute(
            "SELECT distinct [tbfi] FROM [dbo].[KnownBugs] order by [tbfi]")
        row = self.cursor.fetchall()
        if row:
            result = []
            for line in row:
                result.append(line[0])
            return result
        return None

    def select_distinct_components_from_dbo_known_bugs(self)->list:
        self.cursor.execute(
            "  SELECT distinct [components].value('(./components/component/name)[1]', 'VARCHAR(300)') as nodeName FROM [dbo].[KnownBugs] order by nodeName")
        row = self.cursor.fetchall()
        if row:
            result = []
            for line in row:
                result.append(line[0])
            return result
        return None

    def insert_into_dbo_knownpages(self, page_object: PageMechanics.PageGlobal):
        if isinstance(page_object, PageMechanics.PageXWiki):
            page_platform = 'xwiki'
        elif isinstance(page_object, PageMechanics.PageConfluence):
            page_platform = 'confluence'
        elif isinstance(page_object, PageMechanics.PageMediaWiki):
            page_platform = 'mediawiki'
        else:
            page_platform = 'unsupported'
        try:
            self.cursor.execute(
                "insert into [dbo].[KnownPages] ([ID],[page_title],[page_id],[author],[author_ID],[added],"
                "[last_modified],[version],[last_check],[is_uptodate], [characters_total], [platform]) values (NEWID(),?,?,?,?,getdate(),getdate(),?,getdate(),'1',?,?)",
                page_object.page_title, page_object.page_id, page_object.page_author, 'Null', page_object.page_versions,
                page_object.TotalCharacters, page_platform)
            self.connection.commit()
            id_of_new_known_page = self.select_id_from_dbo_knownpages(platform=page_platform, page_id=page_object.page_id)
            return id_of_new_known_page
        except pyodbc.DataError:
            self.connection.rollback()
            print(datetime.now(),
                  'Initial add of ' + page_object.page_title + ' rolled back due to the following error:\n' + traceback.format_exc())
            print("insert into [dbo].[KnownPages] ([ID],[page_title],[page_id],[author],[author_ID],[added],"
                  "[last_modified],[version],[last_check],[is_uptodate], [characters_total], [platform]) values (NEWID(),'" + page_object.page_title + "','" + page_object.page_id + "','" + page_object.page_author + "','Null',getdate(),getdate()," + str(
                page_object.page_versions) + ",getdate(),'1','" + str(
                page_object.TotalCharacters) + "','" + page_platform + "')")
            self.connection.rollback()
            print(datetime.now(),
                  'Initial add of ' + page_object.page_title + ' rolled back due to the following error: page with this [page_id] already exists, need to make incremental run')
            raise Exception('Initial add of ' + page_object.page_title + ' rolled back due to the following error:\n' + traceback.format_exc())

    def insert_into_dbo_knownpages_datagrams(self, page_object: PageMechanics.PageGlobal):
        binary_global_array = pickle.dumps(page_object.VersionsGlobalArray, 4)
        binary_contributors = pickle.dumps(page_object.contributors, 4)
        try:
            self.cursor.execute(
                "insert into [dbo].[KnownPages_datagrams] ([ID],[KnownPageID],[datagram], [contributors_datagram]) values (NEWID(),?,?,?)",
                page_object.SQL_id, binary_global_array, binary_contributors)
            self.connection.commit()
        except:
            self.connection.rollback()
            self.cursor.execute(
                "delete [dbo].[KnownPages] where ID =?",
                page_object.SQL_id)
            self.connection.commit()
            error_handler = traceback.format_exc()
            print(datetime.now(),
                   'Initial add of ' + page_object.page_title + ' rolled back due to the following error while adding its datagram:\n' + error_handler)

    def insert_into_dbo_knownpages_contribution(self, page_object: PageMechanics.PageGlobal):
        binary_total_contribute = pickle.dumps(page_object.TotalContribute, 4)
        # is already added?
        s_q_l_contribution = self.select_datagram_contribution_from_dbo_knownpages_contribution(sql_id=page_object.SQL_id)
        if s_q_l_contribution is None:
            self.cursor.execute(
                "insert into [dbo].[KnownPages_contribution] ([KnownPageID],[datagram_contribution]) values (?,?)",
                page_object.SQL_id, binary_total_contribute)
            self.connection.commit()
        else:
            self.cursor.execute(
                "update [dbo].[KnownPages_contribution] set [datagram_contribution] = ? where KnownPageID=?",
                binary_total_contribute, page_object.SQL_id)
            self.connection.commit()

    def insert_into_dbo_knownpages_userscontribution(self, page_object: PageMechanics.PageGlobal):
        for user, value in page_object.TotalContribute.items():
            self.cursor.execute(
                "select [ID] from [dbo].[KnownPages_Users] where [user_name] = ?",
                user)
            raw = self.cursor.fetchone()
            if raw:
                user_id = raw.ID
            else:  # user doesn't exist in DB
                self.cursor.execute(
                    "insert into [dbo].[KnownPages_Users] ([ID],[user_name]) values (NEWID(),?)",
                    user)
                self.connection.commit()
                self.cursor.execute(
                    "select [ID] from [dbo].[KnownPages_Users] where [user_name] = ?",
                    user)
                raw = self.cursor.fetchone()
                user_id = raw.ID
            # check, if user contribute was already added for this page
            self.cursor.execute(
                "select count(UserID) as count from [dbo].[KnownPages_UsersContribution] where [UserID] = ? and [KnownPageID] = ?",
                user_id, page_object.SQL_id)
            raw = self.cursor.fetchone()
            if int(raw.count) == 1:
                # already added, updating
                self.cursor.execute(
                    "update [dbo].[KnownPages_UsersContribution] set [contribution] = ? where [UserID] = ? and [KnownPageID] = ?",
                    value, user_id, page_object.SQL_id)
                self.connection.commit()
            elif int(raw.count) == 0:
                # inserting
                self.cursor.execute(
                    "insert into [dbo].[KnownPages_UsersContribution] ([UserID],[KnownPageID],[contribution]) values (?,?,?)",
                    user_id, page_object.SQL_id, value)
                self.connection.commit()
            if user == page_object.page_author: # TODO: move this update to page initialize or somewhere else
                self.cursor.execute(
                    "update [dbo].[KnownPages] set author_ID = ? where ID = ?",
                    user_id, page_object.SQL_id)
                self.connection.commit()

    def insert_into_dbo_page_karma_votes(self, sql_id: str, user_id: str, direction: str):
        # checking if this user has already voted for this page
        direction = bool(int(direction))
        self.cursor.execute(
            "select id, [direction] from [dbo].[Page_Karma_votes] where page_id=? and user_id =?",
            sql_id, user_id)
        raw = self.cursor.fetchone()
        if raw:
            current_direction = raw[1]
            if current_direction is True and direction is True or current_direction is False and direction is False:
                return 'Error: Already voted'
            if current_direction is False and direction is True or current_direction is True and direction is False:
                self.cursor.execute(
                    "delete from [dbo].[Page_Karma_votes] where id =?", raw.id)
                self.connection.commit()
                return 'Vote deleted'
        else:
            self.cursor.execute(
                "insert into [dbo].[Page_Karma_votes] values(NEWID(), ?, ?, ?, GETDATE())",
                sql_id, user_id, direction)
            self.connection.commit()
            return 'Vote committed'

    def simple_vote(self, seed: str, user_id: str, direction: str):
        # checking if this user has already voted for this page
        direction = bool(int(direction))
        self.cursor.execute(
            "select id, [direction] from [dbo].[Simple_votes] where seed=? and user_id =?",
            seed, user_id)
        raw = self.cursor.fetchone()
        if raw:
            current_direction = raw[1]
            if current_direction is True and direction is True or current_direction is False and direction is False:
                return 'Error: Already voted'
            if current_direction is False and direction is True or current_direction is True and direction is False:
                self.cursor.execute(
                    "delete from [dbo].[Simple_votes] where id =?", raw.id)
                self.connection.commit()
                return 'Vote deleted'
        else:
            self.cursor.execute(
                "insert into [dbo].[Simple_votes] values(NEWID(), ?, ?, ?, GETDATE())",
                seed, user_id, direction)
            self.connection.commit()
            return 'Vote committed'

    def insert_into_dbo_web_requests(self, known_page_id: str, user_id: str, source_platform_id: str, requested_url: str, result: str)->bool:
        logger = logging.getLogger()
        try:
            if known_page_id != 'NULL':
                self.cursor.execute(
                    "insert into [dbo].[WebRequests] values (NEWID(), GETDATE(), ?, ?, ?, ?, ?)", known_page_id, requested_url, user_id, source_platform_id, result)
            else:
                self.cursor.execute(
                    "insert into [dbo].[WebRequests] values (NEWID(), GETDATE(), NULL, ?, ?, ?, ?)", requested_url, user_id, source_platform_id, result)
            self.connection.commit()
            return True
        except Exception as error:
            self.connection.rollback()
            logger = logging.getLogger()
            logger.error('Unable to insert new WebRequests due to the following error: ' + error)
            return False

    def update_dbo_knownpages_is_uptodate(self, page_id: str, up_to_date: bool):
        if up_to_date is True:
            self.cursor.execute(
                "update [dbo].[KnownPages] set [is_uptodate] = 1, [last_check]= CONVERT(datetime,?) where [page_id]= ?",
                str(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")[:-3]), page_id)
            self.connection.commit()
        else:
            self.cursor.execute(
                "update [dbo].[KnownPages] set [is_uptodate]=0, [last_check]=? where [page_id]=?",
                str(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")[:-3]),  page_id)
            self.connection.commit()

    def update_dbo_knownpages_last_check_last_modified(self, sql_id: str, page_versions: int, total_characters: int):
        self.cursor.execute(
            "update [dbo].[KnownPages] set [last_check]=getdate(),[last_modified]=getdate(), version = ?, characters_total = ? where [id] = ?",
            page_versions, total_characters, sql_id)
        self.connection.commit()

    def update_dbo_knownpages_datagrams(self, page_object: PageMechanics.PageGlobal):
        binary_global_array = pickle.dumps(page_object.VersionsGlobalArray, 4)
        binary_contributors = pickle.dumps(page_object.contributors, 4)
        self.cursor.execute(
            "update [dbo].[KnownPages_datagrams] set datagram=?, contributors_datagram=? where [KnownPageID] =?",
            binary_global_array, binary_contributors, page_object.SQL_id)
        self.connection.commit()

    def update_dbo_knownpages(self, native_sql_id: str, new_title: str) -> bool:
        try:
            self.cursor.execute("update [dbo].[KnownPages] set [page_title] = ? where [ID] = ?", new_title, native_sql_id)
            self.connection.commit()
            return True
        except:
            self.connection.rollback()
            return False

    def exec_delete_page_by_page_id(self, page_id: str)->bool:
        try:
            self.cursor.execute(
                "EXEC [dbo].[delete_page_by_page_id] ?",
                page_id)
            self.connection.commit()
            return True
        except:
            self.connection.rollback()
            return False

    def exec_make_new_global_karma_slice(self)->bool:
        try:
            self.cursor.execute(
                "EXEC [dbo].[make_new_global_karma_slice]")
            self.connection.commit()
            return True
        except:
            self.connection.rollback()
            return False

    def exec_get_user_karma_current_score_global(self):
        self.cursor.execute(
            "EXEC [dbo].[get_user_karma_current_score_global]")
        raw = self.cursor.fetchall()
        if raw:
            return raw
        return None

    def exec_get_user_karma_raw_score(self, user_id: str):
        self.cursor.execute(
            "EXEC get_user_karma_raw_score @id = ?", user_id)
        raw = self.cursor.fetchone()
        if raw:
            return raw.karma
        return None

    def exec_get_page_karma_and_votes(self, page_id: str):
        self.cursor.execute(
            "EXEC dbo.[get_page_karma_and_votes] @page_id = ?", page_id)
        raw = self.cursor.fetchone()
        if raw:
            return raw.up, raw.down, raw.karma_total_score
        return None

    def exec_get_simple_votes(self, seed: str):
        self.cursor.execute(
            "EXEC dbo.[get_simple_votes] @seed = ?", seed)
        raw = self.cursor.fetchone()
        if raw:
            return raw.up, raw.down, raw.total
        return None

    def exec_get_user_karma_current_score_detailed(self, user_id: str):
        self.cursor.execute(
            "EXEC [dbo].[get_user_karma_current_score_detailed] @user_id = ?", user_id)
        while self.cursor.nextset():  # NB: This always skips the first result-set
            try:
                raw = self.cursor.fetchall()
                break
            except pyodbc.ProgrammingError:
                continue
        if raw:
            return raw
        return None

    def exec_get_user_karma_current_score(self, user_id: str):
        self.cursor.execute(
            "EXEC [dbo].[get_user_karma_current_score] @user_id = ?", user_id)
        raw = self.cursor.fetchone()
        if raw:
            return raw.karma
        return None

    def exec_make_new_karma_slice(self, user_id: str):
        self.cursor.execute(
            "EXEC [dbo].[make_new_karma_slice] @user_id = ?", user_id)
        raw = self.cursor.fetchone()
        if raw:
            self.cursor.connection.commit()
            return raw.result
        return None

    def exec_update_or_add_bug_page(self, known_pages_id: str, bug_id: str, product: str, tbfi: str, xml: bytearray, bug_title) -> bool:
        if bug_title is None:
            bug_title = 'NULL'
        try:
            if bug_title != 'NULL':
                self.cursor.execute(
                    "EXEC [dbo].[update_or_add_bug_page] ?, ?, ?, ?, ?, ?", known_pages_id, bug_id, product, tbfi, xml, bug_title)
                self.connection.commit()
            elif bug_title == 'NULL':
                self.cursor.execute(
                    "EXEC [dbo].[update_or_add_bug_page] ?, ?, ?, ?, ?, NULL", known_pages_id, bug_id, product, tbfi, xml)
                self.connection.commit()
            return True
        except:
            self.connection.rollback()
            return False

    def exec_get_user_karma_raw(self, user_id):
        self.cursor.execute(
            "EXEC [dbo].[get_user_karma_raw] @id = ?", user_id)
        raw = self.cursor.fetchall()
        if raw:
            return raw
        return None
