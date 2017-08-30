from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig, xWikiConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator
import hashlib
import requests
target_pool = 'Migration pool'
#target_pool ='Migrated Bugs'
platform = 'MediaWIKI'
syntax = 'mediawiki/1.6'
space = target_pool

xWikiConfig = xWikiConfig(target_pool)
xWikiClient_instance = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)

''' Delete all pages 
'''
result = xWikiClient_instance.page_names(target_pool)
print(result)

for page in result:
    try:
        url = 'http://xwiki.support2.veeam.local/rest/wikis/xwiki/spaces/' + target_pool + '/pages/' + page
        data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><page xmlns="http://www.xwiki.org"><title>' + page + '</title></page>'
        headers = {'Content-Type': 'application/xml'}
        auth = xWikiClient_instance.auth_user, xWikiClient_instance.auth_pass
        response = requests.delete(url, data=data, auth=auth, headers=headers)
        response.raise_for_status()
        print(response.status_code)
    except requests.exceptions.HTTPError:
        print('Error: Cannot delete page:', page)