import Configuration
from  Users import Users
from Configuration import MySQLConfig, ConfluenceConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator


ConfluenceConfig = ConfluenceConfig()
Migrator = Migrator(ConfluenceConfig)
xWikiConfig = Configuration.xWikiConfig('Migration pool')
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
PageTitle = 'Bug 74213 - Storage snapshot only jobs run an additional day if synthetic full was enabled before changing the repository to NetApp'
platform = 'MediaWIKI'

path_to_attach = 'http://wiki.support.veeam.local/files/d/d7/Case01759022_normal_repo.png'
attach_name = 'Case01759022 normal repo.png'
space = 'Migration pool'
page = PageTitle

result = xWikiClient.add_new_attach(space, page, attach_name, path_to_attach)
print(result)

#http://lists.xwiki.org/pipermail/users/2010-February/015251.html

#http://wiki.support.veeam.local/files/d/d7/Case01759022_normal_repo.png
#http://wiki.support.veeam.local/files/7/72/Case01759022_netapp_repo.png
#http://server/xwiki/rest/wikis/{wiki}/spaces/{space}/pages/{page}/attachments
