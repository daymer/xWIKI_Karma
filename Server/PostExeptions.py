class WebPostRequestException(Exception):
    def __init__(self, message, arguments):
        """Base class for other WebPostRequest exceptions"""
        Exception.__init__(self, message + ": {0}".format(arguments))
        self.ErrorMessage = message
        self.ErrorArguments = arguments
        pass


class BadRequestException(WebPostRequestException):
    """Raised when not all needed values were submitted with post"""
    pass


class EmptyPage(WebPostRequestException):
    """Raised when page exists but has 0 characters"""
    pass


class DeprecatedPage(WebPostRequestException):
    """Raised when page indexing is deprecated (s. reindex_page_by_xwd_fullname)"""
    pass


class IndexingTimeOut(WebPostRequestException):
    """Raised when page indexing is re-asked too quickly (current xwiki bug)"""
    pass


class IndexingFailure(WebPostRequestException):
    """Raised when page indexing is re-asked too quickly (current xwiki bug)"""
    pass


class PageDeleteFailure(WebPostRequestException):
    """Raised when exec_delete_page_by_page_id fails to be executed """
    pass


class KarmaInvokeFailure(WebPostRequestException):
    """Raised when exec_make_new_global_karma_slice or exec_get_user_karma_current_score_global fails to be executed """
    pass


class NothingFound(WebPostRequestException):
    """Raised when no bugs were found by provided query """
    pass


class MethodNotSupported(WebPostRequestException):
    """Raised when post logic has no requested method """
    pass

