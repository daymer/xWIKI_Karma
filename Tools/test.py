#http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/Migrated%20Bugs/pages/Bug%20103397%20-%20Veeam%20Agent%20for%20Windows%20Integration%20with%20B&R%20console%20gives%20incorrect%20end%20time%20for%20sessions;%20BEM%20shows%20broken%20throughput

from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig, xWikiConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator
import hashlib
import requests
target_pool = 'Migrated Bugs'
parent = 'Migrated Bugs'
platform = 'MediaWIKI'
syntax = 'mediawiki/1.6'
space = target_pool


title = 'Bug 104952 - Backup fails with partitions;size() &#37; RecsPerTable error'
m = hashlib.md5()
page = m.hexdigest()

xWikiConfig = xWikiConfig(target_pool)
xWikiClient_instance = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)

''' Delete all pages
result = xWikiClient_instance.page_names(target_pool)
for page in result:
    try:
        url = 'http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/Migrated%20Bugs/pages/' + page
        data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><page xmlns="http://www.xwiki.org"><title>' + page + '</title></page>'
        headers = {'Content-Type': 'application/xml'}
        auth = xWikiClient_instance.auth_user, xWikiClient_instance.auth_pass
        response = requests.delete(url, data=data, auth=auth, headers=headers)
        response.raise_for_status()
        print(response.status_code)
    except requests.exceptions.HTTPError:
        print('Error: Cannot delete page:', page)
'''

''' Create page
'''
result = xWikiClient_instance.submit_page(space=space, page=page, content='', syntax=syntax, title=title, parent=parent)
print(result)
'''
'''

''' Delete page
#result = xWikiClient.delete_page(space=space, page=title, title=title, parent=parent)
url = 'http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/Migrated%20Bugs/pages/Bug%2041767%20-%20BackupCopy%20job%20outputs:%20Failed%20to%20compact%20full%20backup%20file'
data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><page xmlns="http://www.xwiki.org"><title>Bug 41767 - BackupCopy job outputs: Failed to compact full backup file</title></page>'
headers = {'Content-Type': 'application/xml'}
auth = xWikiClient.auth_user, xWikiClient.auth_pass
response = requests.delete(url, data=data, auth=auth, headers=headers)
response.raise_for_status()
print(response.status_code)
'''

#http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/Migrated Bugs/pages/Bug 104952 - Backup fails with partitions;size() % RecsPerTable error

