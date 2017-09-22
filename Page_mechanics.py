import Mechanics
from abc import ABCMeta

class PageGlobal(object):
    __metaclass__ = ABCMeta
    def __init__(self):
        self.creation_date = None
        self.latest_version = None
        self.fist_author = None
        self.contributors = {}
        self.PageVersionsDict = []
        self.VersionsGlobalArray = []
        self.TotalContribute = {}
        self.TotalCharacters = 0
        self.dbVersion = None # version of page in the Karma DB. None means that this Page wasn't indexed yet
        self.SQL_id = None
        self.ID = None

    def get_version_content_by_version(self, version_number: str) -> tuple:
        """Used to collect a content of some particular page version. Returns tuple in form: version_number, page_version, contributor"""
        return

    def add_new_page_version(self, num_content_contributor: tuple) -> bool:
        """Used to add a content of version to the page data_handler"""
        return

    def test(self):
        if type(self) is PageXWiki:
            print('Page_mechanics.PageXWiki')

class PageConfluence(PageGlobal):
    def __init__(self, page_title: str):
        PageGlobal.__init__(self)
        self.title = page_title


class PageMediaWiki(PageGlobal):
    def __init__(self, page_title: str):
        PageGlobal.__init__(self)
        self.title = page_title


class PageXWiki(PageGlobal):
    def __init__(self, page: str, page_title: str, xWikiClient_inst: Mechanics.xWikiClient):
        PageGlobal.__init__(self)
        self.xWikiClient_inst = xWikiClient_inst
        self.page_title = page_title  # XWD_TITLE
        self.page = page  # XWD_FULLNAME
        self.path = self.set_space_and_nested_space(self.page)
        self.space = self.path.pop(0)
        self.page = self.path.pop(-1)
        if len(self.path) != 0:
            self.nested_spaces = self.path
        else:
            self.nested_spaces = None
        if page.endswith('.WebHome'):
            self.is_terminal_page = False
        else:
            self.is_terminal_page = True
        self.page_from_API = self.xWikiClient_inst.page(space=self.space, page=self.page, nested_space=self.nested_spaces, is_terminal_page=self.is_terminal_page)

        self.page_id = self.page_from_API['id']
        self.page_versions = self.page_from_API['majorVersion']
        self.page_author = self.page_from_API['creator']


    def set_space_and_nested_space(self, XWD_FULLNAME: str):
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

    def get_version_content_by_version(self, version_number: int) -> tuple:
        if type(self) is PageXWiki:
            response = self.xWikiClient_inst.get_page_version_content_and_author(space=self.space, page=self.page, version=str(version_number) + '.1', nested_space=self.nested_spaces, is_terminal_page=self.is_terminal_page)
            page_version = response[0]
            contributor = response[1]
            return version_number, page_version, contributor

    def add_new_page_version(self, num_content_contributor: tuple)-> bool:
            self.PageVersionsDict.append([num_content_contributor[0], num_content_contributor[1]])
            self.contributors[num_content_contributor[0]] = num_content_contributor[2]
            return True
