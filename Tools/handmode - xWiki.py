import pickle

import Configuration
from CustomModules.Mechanics import PageCreator, ContributionComparator, CustomLogging
from CustomModules.SQL_Connector import SQLConnector

SQLConfig = Configuration.SQLConfig()
ConfluenceConfig = Configuration.ConfluenceConfig()
MediaWIKIConfig = Configuration.MediaWIKIConfig()
xWikiConfig = Configuration.xWikiConfig(['Migration pool', 'Sandbox']) #['Blog', 'Main', 'Sandbox', 'XWiki'] - example of space usage
PAGE_CREATOR = PageCreator(ConfluenceConfig, MediaWIKIConfig, xWikiConfig)
SQLConnector = SQLConnector(SQLConfig)
CustomLogging = CustomLogging('NotSilent')

title = 'Main.Internal Technical Docs.Knowledge Domains.Troubleshooting.Strategies & How-To​'
CurrentPage = PAGE_CREATOR.create_new_page_by_title_and_platform(title, 'xWIKI')
if CurrentPage is None:
    print('Page wasn\'t found in provided spaces. Try to search in [\'Blog\', \'Main\', \'Sandbox\', \'XWiki\']')
    exit()
CustomLogging.page_analysis_started(CurrentPage.page_title)
CurrentPage.page_id = PAGE_CREATOR.collect_page_id(CurrentPage)

# incremental or full mode
CurrentPage.dbVersion = SQLConnector.select_version_from_dbo_knownpages(CurrentPage)

CurrentPage.page_author = PAGE_CREATOR.collect_page_author(CurrentPage)

CurrentPage.page_versions = PAGE_CREATOR.collect_page_history(CurrentPage)

CustomLogging.page_processing_started(CurrentPage)
print(CurrentPage.dbVersion, CurrentPage.page_versions)

if CurrentPage.dbVersion == None:
    CustomLogging.page_processing_target(CurrentPage)
    # getting sources for all versions
    for VersionNumber in range(1, CurrentPage.page_versions + 1):
        #print('getting source for version num', VersionNumber)
        CurrentPage.add_new_page_version(
            PAGE_CREATOR.get_version_content_by_version(VersionNumber, CurrentPage))
    # comparing all versions
    ContribBuilder = ContributionComparator()
    ContribBuilder.initial_compare(CurrentPage)
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
    CurrentPage.pageSQL_id = SQLConnector.insert_into_dbo_knownpages(CurrentPage)
    SQLConnector.insert_into_dbo_knownpages_datagrams(CurrentPage)
    SQLConnector.insert_into_dbo_knownpages_contribution(CurrentPage)
    SQLConnector.insert_into_dbo_knownpages_userscontribution(CurrentPage)
elif CurrentPage.dbVersion < CurrentPage.page_versions:
    SQLConnector.update_dbo_knownpages_is_uptodate(CurrentPage)
    #getting sources for all missing versions + latest in DB
    for VersionNumber in range(CurrentPage.dbVersion, CurrentPage.page_versions + 1):
        CurrentPage.add_new_page_version(PAGE_CREATOR.get_version_content_by_version(VersionNumber, CurrentPage))
    CustomLogging.page_processing_target(CurrentPage)
    #loading old datagram
    CurrentPage.pageSQL_id = SQLConnector.select_id_from_dbo_knownpages(CurrentPage)
    TempArray = SQLConnector.select_datagram_contributors_datagram_from_dbo_knownpages_datagrams(sql_id=CurrentPage.SQL_id)
    CurrentPage.VersionsGlobalArray = pickle.loads(TempArray[0])
    TempContributors = pickle.loads(TempArray[1])
    # comparing latest versions
    ContribBuilder = ContributionComparator('not_silent')
    ContribBuilder.incremental_compare(CurrentPage)
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
    SQLConnector.update_dbo_knownpages_last_check_last_modified(CurrentPage)
    SQLConnector.update_dbo_knownpages_datagrams(CurrentPage)
    SQLConnector.insert_into_dbo_knownpages_contribution(CurrentPage)
    SQLConnector.insert_into_dbo_knownpages_userscontribution(CurrentPage)
elif CurrentPage.dbVersion == CurrentPage.page_versions:
    CustomLogging.page_processing_started(CurrentPage)
    SQLConnector.update_dbo_knownpages_is_uptodate(CurrentPage)