USE Karma;  
GO  
CREATE PROCEDURE get_user_karma_current_score 
    @user_id uniqueidentifier
AS   
    SET NOCOUNT ON;  
    DECLARE	@return_value float
	declare @page_id as uniqueidentifier
	declare @persent as float
	declare @up as float
	declare @down as float
	DECLARE @CURSOR CURSOR
	declare @karma_total_score as float
	set @karma_total_score = 0
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
-- bonus for a page without votes (1 karma point)
set @karma_total_score = @karma_total_score + @persent
--select @page_id, 'no votes found, adding..',@persent, @karma_total_score as 'current karma'
END
ELSE
BEGIN
/*
select [dbo].[KnownPages].page_title as 'page_title', [dbo].[Page_Karma_votes].[direction] as 'direction', @persent as 'multipl',[dbo].[KnownPages_Users].user_name
from [dbo].[KnownPages] 
left join [dbo].[Page_Karma_votes] on [dbo].[KnownPages].id = [dbo].[Page_Karma_votes].page_id
left join [dbo].[KnownPages_Users] on [dbo].[Page_Karma_votes].user_id = [dbo].[KnownPages_Users].id
where [dbo].[KnownPages].id = @page_id
*/
select @up = count(*) from [dbo].[Page_Karma_votes] where [page_id] = @page_id and [direction] = 1
select @down = count(*) from [dbo].[Page_Karma_votes] where [page_id] = @page_id and [direction] = 0
set @karma_total_score = @karma_total_score + ((@up-@down)* @persent)
--select @up as 'up', @down as 'down',((@up-@down)* @persent) as 'summary', @karma_total_score as 'current karma'
END
FETCH NEXT FROM @CURSOR INTO @page_id, @persent
END
CLOSE @CURSOR
set @return_value = @karma_total_score
select @return_value
GO  