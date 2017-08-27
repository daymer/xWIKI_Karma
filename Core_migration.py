import getopt
import sys
import Configuration
from Users import Users
from Configuration import MySQLConfig, ConfluenceConfig, MediaWIKIConfig
from Mechanics import SQLConnector, xWikiClient, MysqlConnector, Migrator
import traceback
##############################################################
#                      Test variables                        #
UseTestVarsSwitch = False
TestVars = {
    'title': '',
    'platform': ''
}
#                                                            #
##############################################################


def print_help():
        print('Core_migration.py v1.0')
        print('Usage:')
        print(
            'Core_migration.py -t <title> -p <platform>')
        print('------------------------------Examples------------------------------------------')
        print('Core_migration .py -t "Diskspd (performance tester)" -p "MediaWIKI"')


def startup(argv):
        title = ''
        platform = ''
        try:
            opts, args = getopt.getopt(argv, "h:t:p:",
                                       ["help=", "title=", "platform="])
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
        if title == '' or platform == '':
            print('Invalid arguments supplied. See help.')
            print('title:', title)
            print('platform:', platform)
            sys.exit(2)
        else:
            return title, platform

# Initial vars
if not sys.argv[1:]:
    print('Started without arguments, s: "-h" or "--help"')
    if UseTestVarsSwitch is True:
        # Test vars
        title = TestVars['title']
        platform = TestVars['platform']
    else:
        sys.exit(2)
        ###
else:
    title = str(startup(sys.argv[1:])[0])
    platform = str(startup(sys.argv[1:])[1])


# Initializing agent
print('Initializing agent')
MySQLconfig_INSTANCE = MySQLConfig()
MysqlConnector_INSTANCE = MysqlConnector(MySQLconfig_INSTANCE)
SQLConfig = Configuration.SQLConfig()
SQLConnector = SQLConnector(SQLConfig)
ConfluenceConfig = ConfluenceConfig()
MediaWIKIConfig = MediaWIKIConfig()
xWikiConfig = Configuration.xWikiConfig('Migration pool')
xWikiClient = xWikiClient(xWikiConfig.api_root, xWikiConfig.auth_user, xWikiConfig.auth_pass)
Migrator = Migrator(ConfluenceConfig=ConfluenceConfig, MediaWIKIConfig=MediaWIKIConfig, xWikiConfig=xWikiConfig)
UserList = Users()

# Starting migration process
print('Starting migration process')

SQLQuery = SQLConnector.GetDatagramsByPageTitleandPlatform(title, platform)
if SQLQuery is None:
    print('ERROR: Page isn\'t indexed yet')
    sys.exit(2)
datagram = SQLQuery[0]
contributors_datagram = SQLQuery[1]

UniqueUsers = set(contributors_datagram.values())
# print(UniqueUsers)
# print(contributors_datagram)

for idx, user in enumerate(UniqueUsers):
    for version, author in contributors_datagram.items():
        if author == user:
            for symbol in datagram:
                if symbol[1] == version:
                    symbol[1] = idx
global_counter_of_symbols = 0
version = 0
latest_text = None
last_version = None
for idx, author in enumerate(UniqueUsers):
    version +=1
    text = ''
    counter_of_symbols = 0
    for symbol in datagram:
        if symbol[1] <= idx:
            text += symbol[0]
            if symbol[1] == idx:
                counter_of_symbols += 1
    global_counter_of_symbols += counter_of_symbols
    print(author, 'with id:', idx, 'has contributed:', counter_of_symbols)
    if counter_of_symbols == 0:
        version -= 1
        continue
    author = UserList.users[author]
    if author is None:
        author = "XWiki.root"
    if platform == 'Confluence':
        syntax = 'confluence+xhtml/1.0'
    elif platform == 'MediaWIKI':
        syntax = 'mediawiki/1.6'
    else:
        syntax = 'xwiki/2.1'
    DataTuple = (
        ('space', 'Migration pool'),
        ('parent', 'Migration pool'),
        ('title', title),
        ('content', text),
        ('author', author),
        ('version', version),
        ('syntax', syntax),  # 'confluence/1.0' 'xwiki/2.1' 'MediaWiki/1.6'
        ('test', False),
        ('only_update', False),
        ('last_run', False),
    )
    MysqlConnector_INSTANCE.add_new_version(*DataTuple)
    latest_text = text
    last_version = version +1

if latest_text is not None and last_version is not None:
    content = latest_text + ' '
    DataTuple = (
            ('space', 'Migration pool'),
            ('parent', 'Migration pool'),
            ('title', title),
            ('content', content),
            ('author', "XWiki.TestTest"),
            ('version', last_version),
            ('syntax', syntax),  # 'confluence/1.0' 'xwiki/2.1' 'MediaWiki/1.6'
            ('test', False),
            ('only_update', False),
            ('last_run', True),
        )
    MysqlConnector_INSTANCE.add_new_version(*DataTuple)
    tags = False
    files = False
    if platform == 'Confluence':
        page_id = SQLConnector.GetPageID_by_title_and_platform(title, platform)
        tags = Migrator.get_tags(platform=platform, id=page_id, test_str=None)
        files = Migrator.get_files(platform=platform, id=page_id, test_str=latest_text)
    elif platform == 'MediaWIKI':
        tags = Migrator.get_tags(platform=platform, id=None, test_str=latest_text)
        files = Migrator.get_files(platform=platform, id=None, test_str=latest_text)
    if title.startswith('Bug') or title.startswith('bug') or title.startswith('BUG'):
        tags.append('bug')
    print(files)
    # Doing tags
    if tags is not False:
        result = xWikiClient.add_tag_to_page(dict(DataTuple)['space'], dict(DataTuple)['title'], tags, title=None, parent=None)
        print(result, len(tags), 'tags:', tags)
    else:
        print('No tags were found')
    # Doing attachments
    if files is not False and len(files) != 0:
        for file in files:
            try:
                result = Migrator.make_and_attach(platform, file_name=file, page=title,
                                                  space='Migration pool')
                print(result, 'file:', file)
            except Exception as e:
                print('Failed on file:', file)
                print(traceback.format_exc())
                print('Failed on file:', file)
        print('Total proceed:', len(files))
    else:
        print('No files were found')
