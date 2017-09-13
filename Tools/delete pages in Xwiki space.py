
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig, xWikiConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator, PageCreator
import hashlib
import requests
target_pool = 'Migrated bugs'
parent = 'Migrated bugs'
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