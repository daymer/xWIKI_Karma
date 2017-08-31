#http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/Migrated%20Bugs/pages/Bug%20103397%20-%20Veeam%20Agent%20for%20Windows%20Integration%20with%20B&R%20console%20gives%20incorrect%20end%20time%20for%20sessions;%20BEM%20shows%20broken%20throughput

from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig, xWikiConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator, PageCreator
import hashlib
import requests
target_pool = 'Migration pool'
parent = 'Migration pool'
platform = 'MediaWIKI'
syntax = 'mediawiki/1.6'
space = target_pool

''' 
title = 'Bug 49790 - "Next run" field in EM doesn\'t match corresponding field in B&R console if the time offset from UTC isn\'t multiple of hour (e.g. UTC +05:30, UTC +09:30).'
m = hashlib.md5()
page = m.hexdigest()
'''
xWikiConfig = xWikiConfig(target_pool)
xWikiClient_instance = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
MediaWIKIConfig = MediaWIKIConfig()
ConfluenceConfig = ConfluenceConfig()
PAGE_CREATOR = PageCreator(ConfluenceConfig, MediaWIKIConfig, xWikiConfig)
''' Delete all pages'''
print('Looking for pages in the following xWIKI space:', space)
for page in MysqlConnector_INSTANCE.get_XWD_FULLNAMEs(space):
    if page == target_pool+'.WebHome':
        continue
    page_object = PAGE_CREATOR.create_new_page_by_title_and_platform(page, 'xWIKI')
    print(page)
    try:
        title = page_object.page_title
    except:
        print('Error: Cannot delete page:', page, 'looks like a redirect')
        continue
    try:
        url = 'http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/'+ target_pool +'/pages/' + page_object.page_xWIKI_page
        data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><page xmlns="http://www.xwiki.org"><title>' + title + '</title></page>'
        headers = {'Content-Type': 'application/xml'}
        auth = xWikiClient_instance.auth_user, xWikiClient_instance.auth_pass
        response = requests.delete(url, data=data.encode('utf-8'), auth=auth, headers=headers)
        response.raise_for_status()
        if response.status_code == 204:
            print(page_object.page_title, 'removed with result:', response.status_code)
        else:
            print(page_object.page_title, 'found, but result is', response.status_code)
    except requests.exceptions.HTTPError:
        print('Error: Cannot delete page:', page_object.page_title)

''' Create page 

result = xWikiClient_instance.submit_page(space=space, page=page, content='', syntax=syntax, title=title, parent=parent)
print(result)

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

