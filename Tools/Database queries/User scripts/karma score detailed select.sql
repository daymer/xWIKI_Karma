use Karma
	declare @user_id uniqueidentifier
	set @user_id = 'B59CA9D0-16EC-4E27-86F7-D8D81843E0BE'
	declare @page_id as uniqueidentifier
	declare @persent as float
	declare @up as float
	declare @down as float
	DECLARE @CURSOR CURSOR
	declare @page_title_temp nvarchar(MAX)
	declare @karma_total_score as float
	set @karma_total_score = 0
	IF OBJECT_ID('tempdb..#Temp') IS NOT NULL DROP Table #Temp
	CREATE TABLE #Temp (
	page_title nvarchar(MAX),
	page_id uniqueidentifier,
	result nvarchar(max),
	up int,
	down int,
	added_to_karma float,
	)
SET @CURSOR = CURSOR SCROLL
FOR
	select [dbo].[KnownPages].id as id, ROUND(1* (CAST([dbo].[KnownPages_UsersContribution].contribution AS float) / CAST([dbo].[KnownPages].characters_total AS float)),2) as 'percent'
	from [dbo].[KnownPages_UsersContribution] 
	left join [dbo].[KnownPages] on [dbo].[KnownPages_UsersContribution].KnownPageID = [dbo].[KnownPages].ID
	left join [dbo].[KnownPages_Users] on [dbo].[KnownPages_UsersContribution].UserID=[KnownPages_Users].id
	where UserID = @user_id and [characters_total] >0
OPEN @CURSOR
FETCH NEXT FROM @CURSOR INTO @page_id, @persent
WHILE @@FETCH_STATUS = 0
BEGIN
IF ((select count(*) from [dbo].[Page_Karma_votes] where [page_id] = @page_id)= 0)
BEGIN
-- bonus for a page without votes (1 karma point * @persent)
select @page_title_temp =page_title from [dbo].[KnownPages] where id = @page_id
set @karma_total_score = @karma_total_score + @persent

Insert INTO #Temp (page_title,page_id,result,added_to_karma,up,down)
select @page_title_temp as page_title,@page_id as page_id, 'no votes found' as result, @persent as added_to_karma, NULL as up,  NULL as down
END
ELSE
BEGIN
select @up = count(*) from [dbo].[Page_Karma_votes] where [page_id] = @page_id and [direction] = 1
select @down = count(*) from [dbo].[Page_Karma_votes] where [page_id] = @page_id and [direction] = 0
set @karma_total_score = @karma_total_score + ((@up-@down)* @persent)
Insert INTO #Temp (page_title,page_id,result,added_to_karma,up,down)
select [dbo].[KnownPages].page_title as page_title,@page_id as page_id, 'votes found: '+cast((@up+@down) as nvarchar) as result, ((@up-@down)* @persent) as added_to_karma, @up as up,  @down as down
from [dbo].[Page_Karma_votes] 
left join [dbo].[KnownPages] on [dbo].[KnownPages].id = [dbo].[Page_Karma_votes].page_id
where [Page_Karma_votes].page_id = @page_id
GROUP BY page_title
END
FETCH NEXT FROM @CURSOR INTO @page_id, @persent
END
CLOSE @CURSOR
select * from #Temp
--select sum(added_to_karma) from #Temp