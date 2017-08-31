

from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig, xWikiConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator
import hashlib
import requests
target_pool = 'Migrated Bugs'
parent = 'Migrated Bugs'
platform = 'MediaWIKI'
syntax = 'mediawiki/1.6'
space = 'Sandbox'

xWikiConfig = xWikiConfig(target_pool)
xWikiClient_instance = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
page = 'TESTPAGE'
title = 'TESTPAGE'



result = xWikiClient_instance.get_page(space=space)
print(result)

