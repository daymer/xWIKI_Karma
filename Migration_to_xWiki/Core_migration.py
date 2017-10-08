import getopt
import sys

import Configuration
import CustomModules.SQL_Connector
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Migration_to_xWiki.Users_association import Users
from CustomModules import Mechanics
from CustomModules.Mechanics import XWikiClient, MysqlConnector, Migrator, ConfluenceAPI

##############################################################
#                      Test variables                        #
UseTestVarsSwitch = True
TestVars = {
    'title': '.NET Error: Mixed mode assembly is built against version \'v2.0.50727\' of the runtime and cannot be loaded in the 4.0 runtime without additional configuration information',
    'platform': 'MediaWIKI',
    'target_pool': 'Migration pool',
    'iparent': 'Migration pool'
}
#                                                            #
##############################################################

def print_help():
        print('Core_migration.py v1.1')
        print('Usage:')
        print(
            'Core_migration.py -t <title> -p <platform> -z <target pool> -i <iparent>')
        print('------------------------------Examples------------------------------------------')
        print('Core_migration .py -t "Diskspd (performance tester)" -p "MediaWIKI" -t "Migration pool" -i "Migration pool"')


def startup(argv):
        title = ''
        platform = ''
        target_pool = ''
        parent = ''
        try:
            opts, args = getopt.getopt(argv, "h:t:p:z:i:",
                                       ["help=", "title=", "platform=", "target=", "iparent="])
        except getopt.GetoptError:
            print_help()
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print_help()
                sys.exit()
            elif opt in ("-t", "--title"):
                title = arg
            elif opt in ("-p", "--platform"):
                platform = arg
            elif opt in ("-z", "--ztarget"):
                target_pool = arg
            elif opt in ("-i", "--iparent"):
                parent = arg
        if title == '' or platform == '' or target_pool == '' or parent == '':
            print('Invalid arguments supplied. See help.')
            print('title:', title)
            print('platform:', platform)
            print('ztarget:', target_pool)
            print('iparent:', parent)
            sys.exit(2)
        else:
            return title, platform, target_pool, parent

# Initial vars
if not sys.argv[1:]:
    print('Started without arguments, s: "-h" or "--help"')
    if UseTestVarsSwitch is True:
        # Test vars
        title = TestVars['title']
        platform = TestVars['platform']
        target_pool = TestVars['target_pool']
        parent = TestVars['iparent']
    else:
        sys.exit(2)
        ###
else:
    title = str(startup(sys.argv[1:])[0])
    platform = str(startup(sys.argv[1:])[1])
    target_pool = str(startup(sys.argv[1:])[2])
    parent = str(startup(sys.argv[1:])[3])



MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
SQLConfig = Configuration.SQLConfig()
xWikiConfig = Configuration.xWikiConfig(target_pool)
xWikiClient = XWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
ConfluenceConfig_instance = Configuration.ConfluenceConfig()
confluenceAPI_instance = ConfluenceAPI(username=ConfluenceConfig_instance.USER, password=ConfluenceConfig_instance.PASS, uri_base=ConfluenceConfig_instance.ULR)
MediaWIKIConfig = MediaWIKIConfig()
Migrator = Migrator(ConfluenceConfig=ConfluenceConfig_instance, MediaWIKIConfig=MediaWIKIConfig, xWikiConfig=xWikiConfig)
UserList = Users()
SQLConnector_instance = CustomModules.SQL_Connector.SQLConnector(SQLConfig)


result = Mechanics.Migrate_page(title, platform, target_pool, parent, MySQLconfig_INSTANCE,
                                MysqlConnector_INSTANCE, SQLConfig, SQLConnector_instance, ConfluenceConfig,
                                MediaWIKIConfig, xWikiConfig, xWikiClient, Migrator, UserList)

print(result)
