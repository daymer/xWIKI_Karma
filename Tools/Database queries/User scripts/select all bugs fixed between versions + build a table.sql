DECLARE @version_start int = 1536,
 @version_end int = 1922

IF OBJECT_ID('tempdb..#temp') IS NOT NULL DROP TABLE #temp
select [dbo].[KnownBugs].bug_id as bug_id,
CASE  WHEN [KnownBugs].bug_title is Null
	 THEN  [KnownPages].page_title
	 ELSE 'Bug ' + cast([dbo].[KnownBugs].[bug_id] as varchar) + ' - '+[dbo].[KnownBugs].bug_title
END
	as title,	 
 [dbo].[KnownPages].page_id,  [dbo].[KnownBugs_TFS_state].build, [KnownBugs].[added_to_wiki] into #temp from [dbo].[KnownBugs_TFS_state]
inner join [dbo].[KnownBugs] on [dbo].[KnownBugs_TFS_state].[KnownBug_ID] = [KnownBugs].[ID]
inner join [dbo].[KnownPages] on [dbo].[KnownPages].ID=[dbo].[KnownBugs].KnownPages_id
where [state] in ('Finished', 'In Inspecting', 'Fixed') 
	and LEFT([dbo].[KnownBugs_TFS_state].[build],6)  = '9.5.0.' 
	and cast(REPLACE([dbo].[KnownBugs_TFS_state].[build], '9.5.0.', '') as int) BETWEEN (@version_start+1) and @version_end
	order by  [dbo].[KnownBugs].bug_id

DECLARE @bug_id int,
 @bug_title varchar(max),
 @page_id varchar(max),
 @build nvarchar(max),
 @CURSOR CURSOR,
 @print_line varchar(max),
 @uri varchar(max)
 print('|**Bug ID**|**Title**|**Build**')
SET @CURSOR = CURSOR SCROLL
	FOR
		select bug_id, title, page_id, build from #temp order by bug_id
OPEN @CURSOR

FETCH NEXT FROM @CURSOR INTO @bug_id, @bug_title, @page_id, @build
WHILE @@FETCH_STATUS = 0
	BEGIN
		set @print_line = ''
		set @uri = 
			(CASE 
					when @page_id like 'xwiki:Main.Bugs and Fixes.Found Bugs.Migrated from mediaWIKI%' 
						THEN 'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Migrated%20from%20mediaWIKI/'+ RIGHT(@page_id, 32)+'||rel="noopener noreferrer" target="_blank"]]'
					when @page_id like 'xwiki:Main.Bugs and Fixes.Found Bugs.VBR.%' 
						THEN 'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/VBR/'+ REPLACE(@page_id, 'xwiki:Main.Bugs and Fixes.Found Bugs.VBR.', '')+'||rel="noopener noreferrer" target="_blank"]]'
					when @page_id like 'xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.%' 
						THEN 'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Agent%20for%20Microsoft%20Windows/'+ REPLACE(@page_id, 'xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.', '')+'||rel="noopener noreferrer" target="_blank"]]'
					when @page_id like 'xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.2\.1.%' 
						THEN 'http://xwiki.support2.veeam.local/bin/view/Main/Bugs%20and%20Fixes/Found%20Bugs/Veeam%20Agent%20for%20Microsoft%20Windows/2.1/'+ REPLACE(@page_id, 'xwiki:Main.Bugs and Fixes.Found Bugs.Veeam Agent for Microsoft Windows.', '')+'||rel="noopener noreferrer" target="_blank"]]'

					ELSE 'undefined||rel="noopener noreferrer" target="_blank"]]'


			END)

		set @print_line = ('|' + cast(@bug_id as varchar) + '|[['+REPLACE(REPLACE(@bug_title, CHAR(13), ''), CHAR(10), '')+'>>url:'+REPLACE(@uri,'.WebHome','')+'|'+@build)


		print(@print_line)
		FETCH NEXT FROM @CURSOR INTO @bug_id, @bug_title, @page_id, @build
	END
CLOSE @CURSOR