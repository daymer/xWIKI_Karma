class PageGlobal(object):
    def __init__(self):
        self.creation_date = None
        self.latest_version = None
        self.fist_author = None
        self.contributors = {}
        self.page_versions_dict = []
        self.versions_global_array = []
        self.total_contribute = {}
        self.total_characters = 0
        self.dbVersion = None
        self.SQL_id = None
        self.ID = None


class PageConfluence(PageGlobal):
    def __init__(self, page_title: str):
        PageGlobal.__init__(self)
        self.title = page_title


class PageMediaWiki(PageGlobal):
    def __init__(self, page_title: str):
        PageGlobal.__init__(self)
        self.title = page_title


class PageXWiki(PageGlobal):
    def __init__(self, page_title: str, page: str):
        PageGlobal.__init__(self)
        self.title = page_title  # XWD_TITLE
        self.page = page  # XWD_FULLNAME
        self.path = self.get_space_and_nested_space(self.page)
        self.space = self.path[0]

    def get_space_and_nested_space(self, XWD_FULLNAME: str):
        replaced_title = XWD_FULLNAME.replace('.WebHome', '')
        replaced_title = replaced_title.replace('\\.', '<dirtyhack>')
        array = replaced_title.split('.')
        path_array = []
        for each in array:
            path_array.append(each.replace('<dirtyhack>', '\\.'))
        return path_array
        #/wikis/{wikiName}/spaces/{spaceName}[/spaces/{nestedSpaceName}]*/pages/{pageName}[?prettyNames={true,false}&objects={true,false}&class={true,false}&attachments={true,false}]
        # var1: Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI.0061b1c914a094d577ceb4c8e7bc00ae
            # http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/Main/spaces/Bugs%20and%20Fixes/spaces/Found%20Bugs/spaces/Migrated%20from%20mediaWIKI/spaces/0df2efe3d77be114667307af657eaa71/pages/WebHome
        # var2: Main.Bugs and Fixes.Fix Upload.WebHome
            # http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/Main/spaces/Bugs%20and%20Fixes/spaces/Fix%20Upload/pages/WebHome

