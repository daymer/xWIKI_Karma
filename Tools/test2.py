test = {'links': [], 'pageSummaries': [{'links': [{'href': 'http://127.0.0.1:8080/rest/wikis/xwiki/spaces/Main/spaces/Internal%20Projects/spaces/667e76872fed0d8d39419f00ffd6018e', 'rel': 'http://www.xwiki.org/rel/space', 'type': None, 'hrefLang': None}, {'href': 'http://127.0.0.1:8080/rest/wikis/xwiki/spaces/Main/spaces/Internal%20Projects/spaces/667e76872fed0d8d39419f00ffd6018e/pages/WebHome', 'rel': 'http://www.xwiki.org/rel/parent', 'type': None, 'hrefLang': None}, {'href': 'http://127.0.0.1:8080/rest/wikis/xwiki/spaces/Main/spaces/Internal%20Projects/spaces/667e76872fed0d8d39419f00ffd6018e/pages/WebHome/history', 'rel': 'http://www.xwiki.org/rel/history', 'type': None, 'hrefLang': None}, {'href': 'http://127.0.0.1:8080/rest/wikis/xwiki/spaces/Main/spaces/Internal%20Projects/spaces/667e76872fed0d8d39419f00ffd6018e/pages/WebHome/objects', 'rel': 'http://www.xwiki.org/rel/objects', 'type': None, 'hrefLang': None}, {'href': 'http://127.0.0.1:8080/rest/wikis/xwiki/spaces/Main/spaces/Internal%20Projects/spaces/667e76872fed0d8d39419f00ffd6018e/pages/WebHome/tags', 'rel': 'http://www.xwiki.org/rel/tags', 'type': None, 'hrefLang': None}, {'href': 'http://127.0.0.1:8080/rest/syntaxes', 'rel': 'http://www.xwiki.org/rel/syntaxes', 'type': None, 'hrefLang': None}, {'href': 'http://127.0.0.1:8080/rest/wikis/xwiki/spaces/Main/spaces/Internal%20Projects/spaces/667e76872fed0d8d39419f00ffd6018e/pages/WebHome', 'rel': 'http://www.xwiki.org/rel/page', 'type': None, 'hrefLang': None}], 'id': 'xwiki:Main.Internal Projects.667e76872fed0d8d39419f00ffd6018e.WebHome', 'fullName': 'Main.Internal Projects.667e76872fed0d8d39419f00ffd6018e.WebHome', 'wiki': 'xwiki', 'space': 'Main.Internal Projects.667e76872fed0d8d39419f00ffd6018e', 'name': 'WebHome', 'title': 'VIQA Best Practices', 'parent': 'xwiki:Main.Internal Projects.WebHome', 'parentId': 'xwiki:Main.Internal Projects.WebHome', 'version': '6.2', 'author': 'XWiki.dmironov', 'authorName': None, 'xwikiRelativeUrl': 'http://xwiki.support2.veeam.local:80/bin/view/Main/Internal%20Projects/667e76872fed0d8d39419f00ffd6018e/', 'xwikiAbsoluteUrl': 'http://xwiki.support2.veeam.local:80/bin/view/Main/Internal%20Projects/667e76872fed0d8d39419f00ffd6018e/', 'translations': {'links': [], 'translations': [], 'default': None}, 'syntax': 'mediawiki/1.6'}]}
text = test['pageSummaries'][0]['title']
print(text)
