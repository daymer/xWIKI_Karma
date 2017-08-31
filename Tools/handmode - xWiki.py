import Configuration
from Mechanics import PageCreator, SQLConnector, ContribBuilder, CustomLogging
import pickle

SQLConfig = Configuration.SQLConfig()
ConfluenceConfig = Configuration.ConfluenceConfig()
MediaWIKIConfig = Configuration.MediaWIKIConfig()
xWikiConfig = Configuration.xWikiConfig(['Migration pool', 'Sandbox']) #['Blog', 'Main', 'Sandbox', 'XWiki'] - example of space usage
PAGE_CREATOR = PageCreator(ConfluenceConfig, MediaWIKIConfig, xWikiConfig)
SQLConnector = SQLConnector(SQLConfig)
CustomLogging = CustomLogging('NotSilent')

title = '.NET Error: Mixed mode assembly is built against version \'v2.0.50727\' of the runtime and cannot be loaded in the 4.0 runtime without additional configuration information'
title = 'Migration pool.4343edbab705f181c0ec7c2462087a96'
CurrentPage = PAGE_CREATOR.create_new_page_by_title_and_platform(title, 'xWIKI')
if CurrentPage is None:
    print('Page wasn\'t found in provided spaces. Try to search in [\'Blog\', \'Main\', \'Sandbox\', \'XWiki\']')
    exit()
CustomLogging.page_analysis_started(CurrentPage.page_title)
CurrentPage.page_id = PAGE_CREATOR.collect_page_id(CurrentPage)
# incremental or full mode
CurrentPage.dbVersion = SQLConnector.CheckExistencebyID(CurrentPage)
CurrentPage.page_author = PAGE_CREATOR.collect_page_author(CurrentPage)
CurrentPage.page_versions = PAGE_CREATOR.collect_page_history(CurrentPage)
CustomLogging.page_processing_started(CurrentPage)
if CurrentPage.dbVersion == None:
    CustomLogging.page_processing_target(CurrentPage)
    # getting sources for all versions
    for VersionNumber in range(1, CurrentPage.page_versions + 1):
        #print('getting source for version num', VersionNumber)
        CurrentPage.add_new_page_version(
            PAGE_CREATOR.get_version_content_by_version(VersionNumber, CurrentPage))
    # comparing all versions
    ContribBuilder = ContribBuilder()
    ContribBuilder.Initialcompare(CurrentPage)
    CurrentPage.TOTALCharacters = len(CurrentPage.VersionsGlobalArray)
    for VersionNum in range(1, CurrentPage.page_versions + 1):
        UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
        #print(CurrentPage.contributors[VersionNum] +' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
        if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) == None:
            CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: len(UserXContribute)})
        else:
            NowInDict = CurrentPage.TotalContribute[CurrentPage.contributors[VersionNum]]
            CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: NowInDict + len(UserXContribute)})
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
    #getting sources for all missing versions + latest in DB
    for VersionNumber in range(CurrentPage.dbVersion, CurrentPage.page_versions + 1):
        CurrentPage.add_new_page_version(PAGE_CREATOR.get_version_content_by_version(VersionNumber, CurrentPage))
    CustomLogging.page_processing_target(CurrentPage)
    #loading old datagram
    CurrentPage.pageSQL_id = SQLConnector.GetPageSQLID(CurrentPage)
    TempArray = SQLConnector.GetDatagrams(CurrentPage)
    CurrentPage.VersionsGlobalArray = pickle.loads(TempArray[0])
    TempContributors = pickle.loads(TempArray[1])
    # comparing latest versions
    ContribBuilder = ContribBuilder('not_silent')
    ContribBuilder.Incrementalcompare(CurrentPage)
    CurrentPage.TOTALCharacters = len(CurrentPage.VersionsGlobalArray)
    for version, user in TempContributors.items(): #Warning! dict.update is used, which means that accidentally matching pairs version:user will be overwritten.
        CurrentPage.contributors.update({version: user})
    # recalculating contribution for all versions
    for VersionNum in range(1, CurrentPage.page_versions + 1):
        # print(CurrentPage.contributors[VersionNum] +' has contributed ' + str(len(UserXContribute)) + ' in version ' + str(VersionNum))
        UserXContribute = [x for x in CurrentPage.VersionsGlobalArray if x[1] == VersionNum]
        if CurrentPage.TotalContribute.get(CurrentPage.contributors[VersionNum]) == None:
            CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: len(UserXContribute)})
        else:
            NowInDict = CurrentPage.TotalContribute[CurrentPage.contributors[VersionNum]]
            CurrentPage.TotalContribute.update({CurrentPage.contributors[VersionNum]: NowInDict + len(UserXContribute)})
    # Showing stats, counting percents
    CustomLogging.page_counting_finished(CurrentPage)
    CustomLogging.page_summary(CurrentPage)
    #pushing updates to SQL
    SQLConnector.UpdatePagebyID(CurrentPage)
    SQLConnector.UpdateDatagramByID(CurrentPage)
    SQLConnector.PushContributionDatagramByID(CurrentPage)
    SQLConnector.PushContributionByUser(CurrentPage)
elif CurrentPage.dbVersion == CurrentPage.page_versions:
    SQLConnector.UpdateKnownPagesLast_check(CurrentPage)