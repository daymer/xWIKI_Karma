from abc import ABCMeta

import PythonConfluenceAPI
import mwclient

from CustomModules import Mechanics


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
        self.dbVersion = None  # version of page in the Karma DB. None means that this Page wasn't indexed yet
        self.SQL_id = None
        self.ID = None
        self.page_versions = 0
        self.page_id = ''
        self.page_title = ''

    def get_version_content_by_version(self, version_number: str) -> tuple:
        """Used to collect a content of some particular page version. Returns tuple in form: version_number, page_version, contributor"""
        return

    def add_new_page_version(self, num_content_contributor: tuple) -> bool:
        """Used to add a content of version to the page data_handler"""
        self.PageVersionsDict.append([num_content_contributor[0], num_content_contributor[1]])
        self.contributors[num_content_contributor[0]] = num_content_contributor[2]
        return True

    def test(self):
        if type(self) is PageXWiki:
            print('Page_mechanics.PageXWiki')


class PageConfluence(PageGlobal):
    def __init__(self, page_title: str,  client_instance: PythonConfluenceAPI.ConfluenceAPI):
        PageGlobal.__init__(self)
        self.page_title = page_title
        self.ConfluenceClient_inst = client_instance
        page_content = self.ConfluenceClient_inst.get_content(content_type='page', title=self.page_title)
        self.page_id = page_content['results'][0]['id']
        page_history = self.ConfluenceClient_inst.get_content_history_by_id(self.page_id)
        self.page_versions = page_history['lastUpdated']['number']
        self.page_author = page_history['createdBy']['displayName']

    def get_version_content_by_version(self, version_number: str) -> tuple:
        try:
            page_version = self.ConfluenceClient_inst.get_content_by_id(self.page_id, 'historical', version=version_number)
            contributor = page_version['version']['by']['displayName']
            page_version = self.ConfluenceClient_inst.get_content_by_id(self.page_id, 'historical', version=version_number, expand='body.storage')
            version_content = page_version['body']['storage']['value']
        except Exception as exception:
            print('Unable to get version: ' + str(version_number) + 'of page ID' + str(self.page_id))
            print(exception)
            return None
        return version_number, version_content, contributor

class PageMediaWiki(PageGlobal):
    def __init__(self, page_title: str, client_instance: mwclient.Site):
        PageGlobal.__init__(self)
        self.mWikiClient_inst = client_instance
        self.page_title = page_title
        test_page = self.mWikiClient_inst.Pages[self.page_title]
        if test_page.redirect:
            # testing, if the page is question is only a redirect
            del test_page
            raise ValueError('Page was not found on the mWiki side')
        else:
            test_page_text = test_page.text()
            if not test_page_text:
                # testing, if the page has any text
                del test_page
                del test_page_text
                raise ValueError('Page has no text')
        self.page_id = self.get_page_id(self.page_title)

    def get_page_id(self, title):
        test_page = self.mWikiClient_inst.Pages[title]
        if test_page is None:
            return None
        return test_page.pageid


class PageXWiki(PageGlobal):
    def __init__(self, page: str, page_title: str, client_instance: Mechanics.XWikiClient):
        PageGlobal.__init__(self)
        self.xWikiClient_inst = client_instance
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
        if self.page_from_API is None:
            raise ValueError('Page was not found on the xWiki side')
        else:
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

    def get_version_content_by_version(self, version_number: int) -> tuple:
        if type(self) is PageXWiki:
            response = self.xWikiClient_inst.get_page_version_content_and_author(space=self.space, page=self.page, version=str(version_number) + '.1', nested_space=self.nested_spaces, is_terminal_page=self.is_terminal_page)
            page_version = response[0]
            contributor = response[1]
            return version_number, page_version, contributor
