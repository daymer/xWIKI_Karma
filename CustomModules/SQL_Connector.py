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
        self.logger = logging.getLogger()
        self.connection = pyodbc.connect(
            'DRIVER=' + sql_config.Driver + ';SERVER=' + sql_config.Server + ';DATABASE='
            + sql_config.Database + ';UID=' + sql_config.Username + ';PWD=' + sql_config.Password)
        self.cursor = self.connection.cursor()

    def select_bugs_between_dates(self, user_id: str, date_start: datetime, date_end: datetime):
        date_start = str(date_start.date())
        date_end = str(date_end.date())

        try:
            self.cursor.execute(
                "exec [dbo].[count_bugs_between_dates] ?, ?, ?", user_id, date_start, date_end)
            raw = self.cursor.fetchone()
            if raw:
                return raw
            else:
                return 0
        except:
            self.logger.error("Invalid query \n exec [dbo].[count_bugs_between_dates] ?, ?, ? " + str(user_id) + ', ' + str(date_start) + ', ' + str(date_end))
            return None

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

    def select_karma_diff_between_dates(self, user_id: str, date_start: datetime, date_end: datetime):
        date_end_year = '%02d' % date_end.year
        date_end_month = '%02d' % date_end.month
        date_end_day = '%02d' % date_end.day
        date_start_year = '%02d' % date_start.year
        date_start_month = '%02d' % date_start.month
        date_start_day = '%02d' % date_start.day
        try:
            self.cursor.execute(
                "exec [dbo].[select_karma_diff_between_dates] ?,?,?",
                user_id, str(date_start_year)+'-'+str(date_start_month)+'-'+str(date_start_day), str(date_end_year)+'-'+str(date_end_month)+'-'+str(date_end_day))
            raw = self.cursor.fetchone()
            if raw:
                return raw.user_id, raw.delta
            return None
        except:
            print("Sad story, but your query is a shit")
            print(
                '"exec [dbo].[select_karma_diff_between_dates] ?,?,?",user_id, str(date_start_year)+"-"+str(date_start_month)+"-"+str(date_start_day), str(date_end_year)+"-"+str(date_end_month)+"-"+str(date_end_day))')

    def select_from_known_bugs_by_filter(self, components_filer: list, product_filter: list, tbfi_filter: list, start: str, end: str) -> list:
        query = "WITH OrderedRecords AS" \
                "(" \
                "SELECT case when [dbo].[KnownBugs].[bug_title] is NULL then [dbo].[KnownPages].[page_title] when [dbo].[KnownBugs].[bug_title] is not NULL then [dbo].[KnownBugs].[bug_title] end as page_title, [dbo].[KnownBugs].id, [dbo].[KnownBugs].[bug_id], [dbo].[KnownBugs].[product], [dbo].[KnownBugs].[tbfi], [dbo].[KnownBugs].[components], [dbo].[KnownPages].page_id, [dbo].[KnownBugs].[added_to_wiki], [dbo].[KnownBugs].[added_by]," \
                "ROW_NUMBER() OVER (ORDER BY [dbo].[KnownBugs].bug_id) AS 'RowNumber' " \
                "FROM [dbo].[KnownBugs] " \
                "left join [dbo].[KnownPages] on [dbo].[KnownBugs].KnownPages_id = [dbo].[KnownPages].id " \
                "WHERE "
        if len(product_filter) > 0:
            query += "[product] in ("
            for idx, product in enumerate(product_filter):
                query += "'" + product + "'"
                if idx != len(product_filter) - 1:
                    query += ", "
                else:
                    query += ")"
        if len(tbfi_filter) > 0:
            if len(product_filter) > 0:
                query += "and [tbfi] in ("
            else:
                query += "[tbfi] in ("
            for idx, tbfi in enumerate(tbfi_filter):
                query += "'" + tbfi + "'"
                if idx != len(tbfi_filter) - 1:
                    query += ", "
                else:
                    query += ")"
        if len(components_filer) > 0:
            for idx, component in enumerate(components_filer):
                if idx == 0 and len(product_filter) != 0 or idx == 0 and len(tbfi_filter) != 0:
                    query += " and "
                elif idx > 0:
                    query += " and "
                query += "(Charindex('" + component + "',CAST(components AS VARCHAR(MAX)))>0)"
        query += ")"
        query += "SELECT [id], [page_title], [bug_id], [product], [tbfi], [components], [page_id],[added_to_wiki], [added_by], [RowNumber] FROM OrderedRecords WHERE RowNumber BETWEEN " + start + " and " + end + " order by added_to_wiki desc"  # moving to added_to_wiki from order by bug_id due to http://git.support2.veeam.local/internal-dev/internal-knowledgebase-engine/issues/65
        logger = logging.getLogger()
        logger.debug(query)
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
            "select [version] from [dbo].[KnownPages] where [page_id] = ?", page_id)
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

    def select_distinct_components_from_dbo_known_bugs(self)->list:  # deprecated
        self.cursor.execute(
            "select distinct T.N.value('.','varchar(300)') as nodeName from [dbo].[KnownBugs] cross apply components.nodes('./components/component/name') as T(N) order by nodeName")
        row = self.cursor.fetchall()
        if row:
            result = []
            for line in row:
                result.append(line[0])
            return result
        return None

    def select_distinct_components_by_product_from_dbo_known_bugs(self)->dict:  # deprecated
        self.cursor.execute(
            "select distinct T.N.value('.','varchar(300)') as nodeName, product from [dbo].[KnownBugs] cross apply components.nodes('./components/component/name') as T(N)")
        rows = self.cursor.fetchall()
        if rows:
            result = {
                'BNR': [],
                'EM': [],
                'VAW': [],
                'VAL': [],
                'VBO365': [],
                'VONE': [],
                'Undefined': [],
                'other': []
            }
            for line in rows:
                component_was_added = False
                for product in result.keys():
                    if line.product.startswith(product):
                        component_was_added = True
                        if line.nodeName not in result[product]:
                            result[product].append(line.nodeName)
                if component_was_added is False:
                    result['other'].append(line.product + ':' + line.nodeName)
            return result
        return None

    def select_dynamic_dbo_known_bugs(self)->dict:
        result = {}
        # loading products
        self.cursor.execute(
            "SELECT distinct product FROM [dbo].[KnownBugs]")
        rows = self.cursor.fetchall()
        if rows:
            for line in rows:
                product = line.product
                result.update({product: []})
        self.cursor.execute(
            "select distinct T.N.value('.','varchar(300)') as nodeName, product from [dbo].[KnownBugs] cross apply components.nodes('./components/component/name') as T(N)")
        rows = self.cursor.fetchall()
        if rows:
            for line in rows:
                result[line.product].append(line.nodeName)
            return result
        return None

    def select_top_x_requested_url_from_web_requests(self, user: str = 'global', count: str = '10'):
        if user != 'global':
            # personalized request
            self.cursor.execute(
                "select top ? [requested_url], COUNT([requested_url]) AS MOST_FREQUENT "
                "from [WebRequests] where [requested_url] != 'http://xwiki.support2.veeam.local/bin/view/Main/' "
                "user_name = ?"
                "GROUP BY requested_url"
                "ORDER BY COUNT(requested_url) DESC", count, user)
        else:
            self.cursor.execute(
                "select top ? [requested_url], COUNT([requested_url]) AS MOST_FREQUENT "
                "from [WebRequests] where [requested_url] != 'http://xwiki.support2.veeam.local/bin/view/Main/' "
                "and [requested_url] not like '%Personal%20Spaces%'"
                "GROUP BY requested_url"
                "ORDER BY COUNT(requested_url) DESC", count)
        row = self.cursor.fetchall()
        if row:
            return row.requested_url
        return None

    def select_count_id_from_knownbugs(self, bug_id: str):
        self.cursor.execute(
            "select count(id) as essentia from [dbo].[KnownBugs] where [bug_id] = ?", bug_id)
        row = self.cursor.fetchone()
        if row:
            existence_check = bool(int(row.essentia))
            return existence_check
        return None

    def select_id_from_knownbugs(self, bug_id: str):
        self.cursor.execute(
            "SELECT [ID] FROM [dbo].[KnownBugs] where [bug_id] = ?", bug_id)
        row = self.cursor.fetchone()
        if row:
            known_bugs_id = row.ID
            return known_bugs_id
        return None

    def select_tfs_info_from_knownbugs_tfs_state(self, known_bug_id: str):
        self.cursor.execute(
            "SELECT [created_date],[changed_date],[state],[status],[build],[check_date] FROM [dbo].[KnownBugs_TFS_state] where [id] = ?", known_bug_id)
        row = self.cursor.fetchone()
        if row:
            return row
        return None

    def select_bug_fix_link(self, known_pages_id: str):
        self.cursor.execute(
            "SELECT [fix_link]  FROM [dbo].[KnownBugs] where [KnownPages_id] = ?", known_pages_id)
        row = self.cursor.fetchone()
        if row:
            return row.fix_link
        return None

    def select_count_id_from_knownbugs_tfs_state(self, known_bug_id: str):
        self.cursor.execute(
            "SELECT count([KnownBug_ID]) as essentia FROM [dbo].[KnownBugs_TFS_state] where [KnownBug_ID] = ?", known_bug_id)
        row = self.cursor.fetchone()
        if row:
            existence_check = bool(int(row.essentia))
            return existence_check
        return None

    def select_custom_select(self, select: str):
        if not select.lower().startswith('select'):
            return None
        self.cursor.execute(select)
        row = self.cursor.fetchall()
        if row:
            return row
        return None

    def select_state_status_from_knownbugs_fts_state(self, knownbug_id: str):
        self.cursor.execute('select state, status from [dbo].[KnownBugs_TFS_state] where KnownBug_ID=?', knownbug_id)
        row = self.cursor.fetchone()
        if row:
            return row.state, row.status
        return None, None

    def select_build_from_knownbugs_fts_state(self, knownbug_id: str):
        self.cursor.execute('select build from [dbo].[KnownBugs_TFS_state] where KnownBug_ID=?', knownbug_id)
        row = self.cursor.fetchone()
        if row:
            return row.build
        return None

    def insert_into_dbo_knownpages(self, page_object: PageMechanics.PageGlobal):
        logger = logging.getLogger()
        logger.debug('page_object.TotalCharacters: ' + str(type(page_object.TotalCharacters)) + ', ' + str(page_object.TotalCharacters))
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
                page_object.page_title, page_object.page_id, page_object.page_author, 'Null', page_object.page_versions, page_object.TotalCharacters, page_platform)
            self.connection.commit()
            id_of_new_known_page = self.select_id_from_dbo_knownpages(platform=page_platform, page_id=page_object.page_id)
            return id_of_new_known_page
        except pyodbc.DataError:
            self.connection.rollback()
            logger.error(
                  'Initial add of ' + str(page_object.page_title) + ' rolled back due to the following error:\n' + str(traceback.format_exc()))
            logger.error("insert into [dbo].[KnownPages] ([ID],[page_title],[page_id],[author],[author_ID],[added],"\
                  "[last_modified],[version],[last_check],[is_uptodate], [characters_total], [platform]) values (NEWID(),'" + str(page_object.page_title) + "','" + str(page_object.page_id)
                         + "','" + str(page_object.page_author) + "','Null',getdate(),getdate()," + str(
                page_object.page_versions) + ",getdate(),'1','" + str(
                page_object.TotalCharacters) + "','" + page_platform + "')")
            logger.error('Initial add of ' + str(page_object.page_title) + ' rolled back due to the following error: page with this [page_id] already exists, need to make incremental run')
            raise Exception('Initial add of ' + page_object.page_title + ' rolled back due to the following error:\n' + traceback.format_exc())
        except Exception as error:
            self.connection.rollback()
            logger.error(
                  'Initial add of ' + str(page_object.page_title) + ' rolled back due to the following error:\n' + str(traceback.format_exc()))
            logger.error("insert into [dbo].[KnownPages] ([ID],[page_title],[page_id],[author],[author_ID],[added],"\
                  "[last_modified],[version],[last_check],[is_uptodate], [characters_total], [platform]) values (NEWID(),'" + str(page_object.page_title) + "','" + str(page_object.page_id)
                         + "','" + str(page_object.page_author) + "','Null',getdate(),getdate()," + str(
                page_object.page_versions) + ",getdate(),'1','" + str(
                page_object.TotalCharacters) + "','" + page_platform + "')")


            raise Exception('Initial add of ' + page_object.page_title + ' rolled back due to the following error:\n' + traceback.format_exc())

    def insert_into_dbo_knownpages_users(self, user_name: str):
        try:
            self.cursor.execute(
                "insert into [dbo].[KnownPages_Users] ([ID],[user_name]) values (NEWID(),?)", user_name)
            self.connection.commit()
            self.cursor.execute(
                "select [ID] from [dbo].[KnownPages_Users] where [user_name]= ?", user_name)
            row = self.cursor.fetchone()
            return row.ID
        except pyodbc.DataError:
            self.connection.rollback()
            raise Exception('Initial add of user' + user_name + ' rolled back due to the following error:\n' + traceback.format_exc())

    def insert_into_dbo_knownpages_datagrams(self, page_object: PageMechanics.PageGlobal):
        logger_inst = logging.getLogger()
        if page_object.SQL_id is None:
            logger_inst.critical('Critical failure: page_object.SQL_id cannot be NONE')
            exit(1)
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
            logger_inst.error('Initial add of ' + page_object.page_title + ' rolled back due to the following error while adding its datagram:\n' + error_handler)
            logger_inst.error('Values: page_object.SQL_id ' + str(page_object.SQL_id))

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

    def insert_into_dbo_knownbugs_tfs_state(self, known_bug_id: str, created_date: str, changed_date: str, state: str, status: str, build: str):
        try:
            self.cursor.execute(
                "insert into [dbo].[KnownBugs_TFS_state] values (?,?,?,?,?,?, GETDATE())", known_bug_id, created_date, changed_date, state, status, build)
            self.connection.commit()
        except pyodbc.DataError:
            self.connection.rollback()
            raise Exception('insert of TFS Bug info related to "' + known_bug_id + ' rolled back due to the following error:\n' + traceback.format_exc())

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

    def insert_into_dbo_webrequests_vote_for_page_as_user(self, xwd_fullname, direction, user_name, link):
        logger = logging.getLogger()
        current_id = None
        try:
            self.cursor.execute('select NEWID()')
            raw = self.cursor.fetchone()
            if raw:
                current_id = raw[0]
            if current_id is not None:
                self.cursor.execute(
                    "insert into [dbo].[WebRequests_vote_for_page_as_user] values (?, GETDATE(), ?, ?, ?, ?, ?, 0)", current_id, user_name,
                    link, direction, xwd_fullname, 0)
                self.connection.commit()
                return current_id
            else:
                raise Exception
        except Exception as error:
            self.connection.rollback()
            logger = logging.getLogger()
            logger.error('Unable to insert new WebRequests_vote_for_page_as_user due to the following error: ' + error)
            return False

    def update_dbo_webrequests_vote_for_page_as_user(self, token_id: str, result: bool):
        try:
            self.cursor.execute(
                    "update [dbo].[WebRequests_vote_for_page_as_user] set [committed] = 1, [result] =?  where ID = ?", result, token_id)
            self.connection.commit()
            return True
        except Exception as error:
            self.connection.rollback()
            logger = logging.getLogger()
            logger.error('Unable to update state in WebRequests_vote_for_page_as_user due to the following error: ' + error)
            return False

    def insert_into_dbo_webrequests_reindex_page_by_xwd_fullname(self, xwd_fullname, link):
        logger = logging.getLogger()
        current_id = None
        try:
            self.cursor.execute('select NEWID()')
            raw = self.cursor.fetchone()
            if raw:
                current_id = raw[0]
            if current_id is not None:
                self.cursor.execute(
                    "insert into [dbo].[WebRequests_reindex_page_by_XWD_FULLNAME] values (?, GETDATE(), ?, ?, 0, 0, 0, 0, Null, Null)",
                    current_id, link, xwd_fullname)
                self.connection.commit()
                return current_id
            else:
                raise Exception
        except Exception as error:
            self.connection.rollback()
            logger = logging.getLogger()
            logger.error('Unable to insert new [WebRequests_reindex_page_by_XWD_FULLNAME] due to the following error: ' + error)
            return False

    def update_dbo_webrequests_reindex_page_by_xwd_fullname(self, token_id, result, is_full, is_bug: bool=False, fix_link:str=None, fix_link_has_changed:bool=None):
        try:
            if is_full == 'pass':
                if is_bug is True:
                    self.cursor.execute(
                        "update [dbo].[WebRequests_reindex_page_by_XWD_FULLNAME] set [committed] = 1, [result] = ?, [is_bug] = 1, fix_link = ?, fix_link_updated = ?  where ID = ?",
                        result, fix_link, fix_link_has_changed, token_id)
                else:
                    self.cursor.execute(
                            "update [dbo].[WebRequests_reindex_page_by_XWD_FULLNAME] set [committed] = 1, [result] = ? where ID = ?", result, token_id)
            else:
                self.cursor.execute(
                        "update [dbo].[WebRequests_reindex_page_by_XWD_FULLNAME] set [committed] = 1, [result] = ?, [full] = ?  where ID = ?", result, is_full, token_id)
            self.connection.commit()
            return True
        except Exception as error:
            self.connection.rollback()
            logger = logging.getLogger()
            logger.error('Unable to update state in WebRequests_reindex_page_by_XWD_FULLNAME due to the following error: ' + str(error))
            return False

    def insert_into_dbo_webrequests_delete_page_by_xwd_fullname(self, xwd_fullname, link):
        logger = logging.getLogger()
        current_id = None
        try:
            self.cursor.execute('select NEWID()')
            raw = self.cursor.fetchone()
            if raw:
                current_id = raw[0]
            if current_id is not None:
                self.cursor.execute(
                    "insert into [dbo].[WebRequests_delete_page_by_XWD_FULLNAME] values (?, GETDATE(), ?, ?, 0, 0)",
                    current_id, link, xwd_fullname)
                self.connection.commit()
                return current_id
            else:
                raise Exception
        except Exception as error:
            self.connection.rollback()
            logger = logging.getLogger()
            logger.error('Unable to insert new [WebRequests_delete_page_by_XWD_FULLNAME] due to the following error: ' + str(error))
            return False

    def update_dbo_webrequests_delete_page_by_xwd_fullname(self, token_id: str, result: bool):
        try:
            self.cursor.execute(
                    "update [dbo].[WebRequests_delete_page_by_XWD_FULLNAME] set [committed] = 1, result = ? where ID = ?", result, token_id)
            self.connection.commit()
            return True
        except Exception as error:
            self.connection.rollback()
            logger = logging.getLogger()
            logger.error('Unable to update state in [WebRequests_delete_page_by_XWD_FULLNAME] due to the following error: ' + str(error))
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

    def update_dbo_knownbugs_tfs_state(self, known_bug_id: str, created_date: str, changed_date: str, state: str, status: str, build: str):
        try:
            self.cursor.execute(
                "update [dbo].[KnownBugs_TFS_state] set [created_date]=?,"
                "[changed_date]=?,"
                "[state]=?,"
                "[status]=?,"
                "[build]=?,"
                "[check_date]=GETDATE() where [KnownBug_ID] = ?", created_date, changed_date, state, status, build, known_bug_id)
            self.connection.commit()
        except pyodbc.DataError:
            self.connection.rollback()
            raise Exception('update of TFS Bug info related to "' + known_bug_id + ' rolled back due to the following error:\n' + traceback.format_exc())

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

    def exec_update_or_add_bug_page(self, known_pages_id: str, bug_id: str, product: str, tbfi: str, xml: bytearray, bug_title: str, added_to_wiki: str, added_to_wiki_by: str, fix_link: str) -> bool:
        logger = logging.getLogger()
        logger.debug('exec_update_or_add_bug_page arguments: known_pages_id: ' + known_pages_id
                      + ' bug_id: ' + str(bug_id)
                      + ' product: ' + str(product)
                      + ' tbfi: ' + str(tbfi)
                      + ' xml: ' +str(xml)
                      + ' bug_title: ' + str(bug_title)
                      + ' added_to_wiki: ' + str(added_to_wiki)
                      + ' added_to_wiki_by: ' + str(added_to_wiki_by)
                      + ' fix_link: ' + str(fix_link))
        if bug_title is None:
            bug_title = 'NULL'
        try:
            if bug_title != 'NULL':
                self.cursor.execute(
                    "EXEC [dbo].[update_or_add_bug_page] ?, ?, ?, ?, ?, ?, ?, ?, ?", known_pages_id, bug_id, product, tbfi, xml, bug_title, added_to_wiki, added_to_wiki_by, fix_link)
                self.connection.commit()
            elif bug_title == 'NULL':
                self.cursor.execute(
                    "EXEC [dbo].[update_or_add_bug_page] ?, ?, ?, ?, ?, NULL, ?, ?, ?", known_pages_id, bug_id, product, tbfi, xml, added_to_wiki, added_to_wiki_by, fix_link)
                self.connection.commit()
            return True
        except Exception as error:
            self.connection.rollback()
            logging_func = logging.getLogger()
            logging.critical(error)
            return False

    def exec_get_user_karma_raw(self, user_id):
        self.cursor.execute(
            "EXEC [dbo].[get_user_karma_raw] @id = ?", user_id)
        raw = self.cursor.fetchall()
        if raw:
            return raw
        return None
