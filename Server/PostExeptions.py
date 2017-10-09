class WebPostRequestException(Exception):
    def __init__(self, message, arguments):
        """Base class for other WebPostRequest exceptions"""
        Exception.__init__(self, message + ": {0}".format(arguments))
        self.ErrorMessage = message
        self.ErrorArguments = arguments
        pass


class PageXWIKIUnknownException(WebPostRequestException):
    """Raised when the requested page wasn't found in xWiki DB"""
    pass


class PageKarmaDBUnknownException(WebPostRequestException):
    """Raised when the requested page wasn't found on Karma SQL"""
    #page_unknown_answer = json.dumps({'Error': 'Bad request - there is no known page with ID "' + page_id + '" in the database'}, separators=(',', ':'))
    pass


class BadRequestException(WebPostRequestException):
    """Raised when not all needed values were submitted with post"""
    # return json.dumps({'Error': 'Bad request - no id or platform was provided'}, separators=(',', ':'))
    # return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
    # return json.dumps({'Error': 'Bad request - there is no known page with id "' + page_id + '" in the database'},
    # return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
    # return json.dumps({'Error': 'bad request - no user_name, platform or page_title was provided'}, separators=(',', ':'))
    # return json.dumps({'Error': 'Unable to get statistics'}, separators=(',', ':'))
    # return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
    # return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
    # return json.dumps({'Error': 'bad request - no username was provided'}, separators=(',', ':'))
    # return json.dumps({'Error': 'bad request - username not found'}, separators=(',', ':'))
    # return json.dumps({'Error': 'Bad request - no XWD_FULLNAME or platform was provided'}, separators=(',', ':'))
    # return json.dumps({'Error': 'Bad request - no XWD_FULLNAME or platform was provided'}, separators=(',', ':'))
    # answer = {'Error': 'Failed to delete, Null XWD_FULLNAME was provided'}
    # json.dumps({'Error': 'Bad request - start/end is incorrect'}, separators=(',', ':'))
    # json.dumps({'Error': 'Bad request - start > end'}, separators=(',', ':'))
    pass


class EmptyPage(WebPostRequestException):
    """Raised when page exists but has 0 characters"""
    #  answer = {'Error': 'Page exists but has 0 characters'}
    pass


class DeprecatedPage(WebPostRequestException):
    """Raised when page indexing is deprecated (s. reindex_page_by_xwd_fullname)"""
    #  answer = {'Error': 'Indexing of non-main and non-staging pages using this request is not allowed'}
    pass


class IndexingTimeOut(WebPostRequestException):
    """Raised when page indexing is re-asked too quickly (current xwiki bug)"""
    #  answer = {'Error': 'Doubled request from indexing of the same page before ' + str(self.re_index_timeout) + ' timeout'}
    #  print('Doubled request from indexing of the same page, denied')
    pass


class IndexingFailure(WebPostRequestException):
    """Raised when page indexing is re-asked too quickly (current xwiki bug)"""
    #  answer = {'Error': 'Failed to add to processing'}
    pass


class PageDeleteFailure(WebPostRequestException):
    """Raised when exec_delete_page_by_page_id fails to be executed """
    #  answer = {'Error': 'Failed to delete'}
    pass


class GlobalKarmaInvokeFailure(WebPostRequestException):
    """Raised when exec_make_new_global_karma_slice fails to be executed """
    #  return json.dumps({'Error': 'Failed to invoke'}, separators=(',', ':'))
    pass

class BugsNothingFound(WebPostRequestException):
    """Raised when no bugs were found by provided query """
    #  return json.dumps({'error': 'Nothing was found'}, separators=(',', ':'))
    pass

class MethodNotSupported(WebPostRequestException):
    """Raised when post logic has no requested method """
    pass