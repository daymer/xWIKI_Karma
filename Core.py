from PythonConfluenceAPI import ConfluenceAPI
from mwclient import Site
import Configuration
import pickle
from Mechanics import PageCreator, SQLConnector, ContribBuilder, CustomLogging, ExclusionsDict


ContribBuilder = ContribBuilder()
SQLConfig = Configuration.SQLConfig()
ConfluenceConfig = Configuration.ConfluenceConfig()
MediaWIKIConfig = Configuration.MediaWIKIConfig()
xWikiConfig = Configuration.xWikiConfig()
PAGE_CREATOR = PageCreator(ConfluenceConfig, MediaWIKIConfig, xWikiConfig)
SQLConnector = SQLConnector(SQLConfig)
CustomLogging = CustomLogging('NOTsilent')
#getting all pages in Confluence:
confluenceAPI = ConfluenceAPI(ConfluenceConfig.USER, ConfluenceConfig.PASS, ConfluenceConfig.ULR)

# Task:
#    Confluence: VB (Veeam B&R Basic knowledge), WB (Veeam Support Hints and Tricks), GZ (Ground Zero)
#    MediaWIKI: just all
#    xWIKI: ['Blog', 'Main', 'Sandbox', 'XWiki']
Task = {
    'VB': 'Confluence',
    'WB': 'Confluence',
    'GZ': 'Confluence',
    'ALL mWIKI': 'MediaWIKI'
    #'Main': 'xWIKI',
    #'Sandbox': 'xWIKI',
    #'Migration pool': 'xWIKI'
}
TaskExclusions = ExclusionsDict()
TaskExclusions['Confluence'] = None
TaskExclusions['MediaWIKI'] = 'Found Bugs'
TaskExclusions['MediaWIKI'] = 'Registry values B&R'
TaskExclusions['MediaWIKI'] = 'Veeam ONE Registry Keys'
TaskExclusions['MediaWIKI'] = 'Patches and fixes for B&R'
#TaskExclusions['MediaWIKI'] = 'Bug%'
#TaskExclusions['MediaWIKI'] = 'BUG%'
#TaskExclusions['MediaWIKI'] = 'bug%'
TaskExclusions['MediaWIKI'] = 'Case Handling'
TaskExclusions['MediaWIKI'] = 'Team Members'
TaskExclusions['xWIKI'] = None
toAnalyze = []
TaskPages = {}
TotalSize = 0
for space, platform in Task.items():
    if platform =='Confluence':
        respond = confluenceAPI.get_content('page', space, None, 'current', None, None, 0, 500)
        size = respond['size']
        TotalSize += size
        print(size, 'Confluence pages were found in space', space)
        toAnalyze = respond['results']
        for page in toAnalyze:
            if TaskExclusions[platform] is not None:
                if not PAGE_CREATOR.check_exclusions(page['title'], platform, TaskExclusions):
                    continue
                else:
                    TaskPages.update({page['title']: platform})
                    size += 1
            else:
                TaskPages.update({page['title']: platform})
                size += 1
    if platform =='MediaWIKI':
        size = 0
        for page in PAGE_CREATOR.MediaWikiAPI.allpages():
            if TaskExclusions[platform] is not None:
                if not PAGE_CREATOR.check_exclusions(page.name, platform, TaskExclusions):
                    print(page.name, 'was excluded, total excluded:', PAGE_CREATOR.TotalExcluded)
                    continue
                else:
                    TaskPages.update({page.name: platform})
                    size += 1
            else:
                TaskPages.update({page.name: platform})
                size += 1
        #print(size, 'MediaWIKI pages were found in space', space)
        TotalSize += size
    if platform == 'xWIKI':
        size = 0
        for page in PAGE_CREATOR.xWikiAPI.page_names(space):
            if TaskExclusions[platform] is not None:
                if not PAGE_CREATOR.check_exclusions(page, platform, TaskExclusions):
                    continue
                else:
                    TaskPages.update({page: platform})
                    size += 1
            else:
                TaskPages.update({page: platform})
                size += 1
        print(size, 'xWIKI pages were found in space', space)
        TotalSize += size
CustomLogging.log_task_start(TotalSize, PAGE_CREATOR.TotalExcluded)

#startin main process
for title, platform in TaskPages.items():
    CustomLogging.page_analysis_started(title)
    CurrentPage = PAGE_CREATOR.create_new_page_by_title_and_platform(title, platform)
    if CurrentPage is None:
        CustomLogging.skip_some_page(title)
        continue
    CurrentPage.page_id = PAGE_CREATOR.collect_page_id(CurrentPage)
    if CurrentPage.page_id is None:
        CustomLogging.skip_some_page(title)
        continue
    # TODO: add page rename into DB
    # incremental or full mode
    CurrentPage.dbVersion = SQLConnector.CheckExistencebyID(CurrentPage)
    CurrentPage.page_versions = PAGE_CREATOR.collect_page_history(CurrentPage)
    CurrentPage.page_author = PAGE_CREATOR.collect_page_author(CurrentPage)
    CustomLogging.page_processing_started(CurrentPage)
    if CurrentPage.dbVersion == None:
        CustomLogging.page_processing_target(CurrentPage)
        # getting sources for all versions
        for VersionNumber in range(1, CurrentPage.page_versions + 1):
            new_version = PAGE_CREATOR.get_version_content_by_version(VersionNumber, CurrentPage)
            CurrentPage.add_new_page_version(new_version)
        # comparing all versions
        try:
            ContribBuilder.Initialcompare(CurrentPage)
        except:
            print(CurrentPage.PageVersionsDict)
        CurrentPage.TOTALCharacters = len(CurrentPage.VersionsGlobalArray)
        for VersionNum in range(1, CurrentPage.page_versions + 1):
            # print(CurrentPage.contributors[VersionNum] +' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
            UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
            if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) == None:
                CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: len(UserXContribute)})
            else:
                NowInDict = CurrentPage.TotalContribute[CurrentPage.contributors[VersionNum]]
                CurrentPage.TotalContribute.update(
                    {CurrentPage.contributors[VersionNum]: NowInDict + len(UserXContribute)})
        # Showing stats, counting percents
        CustomLogging.page_counting_finished(CurrentPage)
        CustomLogging.page_summary(CurrentPage)
        # pushing new page to SQL
        CurrentPage.pageSQL_id = SQLConnector.PushNewPage(CurrentPage)
        SQLConnector.PushNewDatagram(CurrentPage)
        SQLConnector.PushContributionDatagramByID(CurrentPage)
        SQLConnector.PushContributionByUser(CurrentPage)
    elif CurrentPage.dbVersion < CurrentPage.page_versions:
        SQLConnector.UpdateKnownPagesLast_check(CurrentPage)
        # getting sources for all missing versions + latest in DB
        for VersionNumber in range(CurrentPage.dbVersion, CurrentPage.page_versions + 1):
            new_version = PAGE_CREATOR.get_version_content_by_version(VersionNumber, CurrentPage)
            CurrentPage.add_new_page_version(new_version)
        CustomLogging.page_processing_target(CurrentPage)
        # loading old datagram
        CurrentPage.pageSQL_id = SQLConnector.GetPageSQLID(CurrentPage)
        TempArray = SQLConnector.GetDatagrams(CurrentPage)
        CurrentPage.VersionsGlobalArray = pickle.loads(TempArray[0])
        TempContributors = pickle.loads(TempArray[1])
        # comparing latest versions
        ContribBuilder.Incrementalcompare(CurrentPage)
        CurrentPage.TOTALCharacters = len(CurrentPage.VersionsGlobalArray)
        for version, user in TempContributors.items():  # Warning! dict.update is used, which means that accidentally matching pairs version:user will be overwritten.
            CurrentPage.contributors.update({version: user})
        # recalculating contribution for all versions
        for VersionNum in range(1, CurrentPage.page_versions + 1):
            # print(CurrentPage.contributors[VersionNum] +' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
            UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
            if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) == None:
                CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: len(UserXContribute)})
            else:
                NowInDict = CurrentPage.TotalContribute[CurrentPage.contributors[VersionNum]]
                CurrentPage.TotalContribute.update(
                    {CurrentPage.contributors[VersionNum]: NowInDict + len(UserXContribute)})
        # Showing stats, counting percents
        CustomLogging.page_counting_finished(CurrentPage)
        CustomLogging.page_summary(CurrentPage)
        # pushing updates to SQL
        SQLConnector.UpdatePagebyID(CurrentPage)
        SQLConnector.UpdateDatagramByID(CurrentPage)
        SQLConnector.PushContributionDatagramByID(CurrentPage)
        SQLConnector.PushContributionByUser(CurrentPage)
    elif CurrentPage.dbVersion == CurrentPage.page_versions:
        SQLConnector.UpdateKnownPagesLast_check(CurrentPage)

CustomLogging.log_task_ended()
