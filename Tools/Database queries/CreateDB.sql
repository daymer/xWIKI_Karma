if db_id('Karma') is null BEGIN 
	CREATE DATABASE [Karma];
	END
ELSE BEGIN
	print 'Error: DB already exists'
	END
GO

if db_id('Karma') is not null BEGIN 
	USE [Karma]
	END 
GO

CREATE TABLE [dbo].[KnownPages]
(ID uniqueidentifier,
page_title nvarchar(max),
page_id varchar(MAX),
author nvarchar(max),
author_ID nvarchar(255) NULL,
added datetime,
last_modified datetime NULL,
version int,
last_check datetime NULL,
is_uptodate bit NULL,
characters_total nvarchar(max),
platform nvarchar(max)
)
CREATE INDEX iAdded ON KnownPages (Added)
CREATE UNIQUE INDEX iID ON KnownPages (ID)
/*
	drop index KnownPages.iAdded
	drop index KnownPages.iID
    drop table [dbo].[KnownPages]


*/

CREATE TABLE KnownPages_datagrams
(ID uniqueidentifier,
KnownPageID uniqueidentifier,
datagram varbinary(max) NULL,
contributors_datagram varbinary(max) NULL
)
CREATE UNIQUE INDEX iID ON KnownPages_datagrams (ID)
CREATE UNIQUE INDEX iKnownPagesID ON KnownPages_datagrams (KnownPageID)
/*
	drop index KnownPages_datagrams.iKnownPagesID
	drop index KnownPages_datagrams.iID
    drop table [dbo].[KnownPages_datagrams]


*/

CREATE TABLE KnownPages_contribution
(KnownPageID uniqueidentifier,
datagram_contribution varbinary(max)
)
CREATE UNIQUE INDEX iKnownPageID ON KnownPages_contribution (KnownPageID)

CREATE TABLE KnownPages_Users
(ID uniqueidentifier,
user_name nvarchar(max)
)
CREATE UNIQUE INDEX iID ON KnownPages_Users (ID)

CREATE TABLE KnownPages_UsersContribution
(UserID uniqueidentifier,
KnownPageID uniqueidentifier,
contribution int
)
CREATE INDEX iKnownPageID ON KnownPages_UsersContribution (KnownPageID)

/*
	drop index KnownPages_UsersContribution.iKnownPageID
    drop table [dbo].[KnownPages_UsersContribution]


*/
USE Karma;  
GO

CREATE PROCEDURE [dbo].[get_user_karma_raw_score]
    @id uniqueidentifier

AS   
    SET NOCOUNT ON;  
    DECLARE	@return_value int
	IF OBJECT_ID('tempdb..#TempTable') IS NOT NULL DROP Table #TempTable
	select [dbo].[KnownPages].page_title, ROUND(1* (CAST([dbo].[KnownPages_UsersContribution].contribution AS float) / CAST([dbo].[KnownPages].characters_total AS float)),2) as persent
	INTO #TempTable
	from [dbo].[KnownPages_UsersContribution] 
	left join [dbo].[KnownPages] on [dbo].[KnownPages_UsersContribution].KnownPageID = [dbo].[KnownPages].ID
	left join [dbo].[KnownPages_Users] on [dbo].[KnownPages_UsersContribution].UserID=[KnownPages_Users].id
	where UserID = @id and [characters_total] >0
	select SUM(persent) from #TempTable;  
GO

CREATE PROCEDURE [dbo].[get_user_karma_raw]
    @id uniqueidentifier

OUTPUT AS   
	select [dbo].[KnownPages].page_title as 'page_title', ROUND(1* (CAST([dbo].[KnownPages_UsersContribution].contribution AS float) / CAST([dbo].[KnownPages].characters_total AS float)),2) as 'percent'
	from [dbo].[KnownPages_UsersContribution] 
	left join [dbo].[KnownPages] on [dbo].[KnownPages_UsersContribution].KnownPageID = [dbo].[KnownPages].ID
	left join [dbo].[KnownPages_Users] on [dbo].[KnownPages_UsersContribution].UserID=[KnownPages_Users].id
	where UserID = @id and [characters_total] >0
GO

CREATE TABLE [dbo].[Page_Karma_votes]
(ID uniqueidentifier PRIMARY KEY CLUSTERED,
page_id uniqueidentifier not NULL,
user_id uniqueidentifier not NULL,
direction bit not NULL, -- 1 means up, 0 means down
added datetime not NULL,
UNIQUE (page_id,user_id)
)

CREATE INDEX Ipage_id ON Page_Karma_votes (page_id)
CREATE UNIQUE INDEX iID ON Page_Karma_votes (ID)
/*
	drop index Page_Karma_votes.Ipage_id
	drop index Page_Karma_votes.iID
    drop table [dbo].[Page_Karma_votes]


*/


CREATE TABLE UserKarma_slice
(ID uniqueidentifier Not null,
user_id uniqueidentifier Not null,
karma_score float Not null,
karma_diff float,
change_time datetime Not null,
)
CREATE UNIQUE INDEX iID ON UserKarma_slice (ID)
CREATE INDEX iUser_ID ON UserKarma_slice (user_id)
/*
	


*/


CREATE TABLE UserKarma_current
(ID uniqueidentifier,
user_id uniqueidentifier,
karma_score varbinary(max),
change_time datetime
)
CREATE UNIQUE INDEX iID ON UserKarma_current (ID)
CREATE UNIQUE INDEX iUser_ID ON UserKarma_current (user_id)
/*
	


*/

USE Karma;  
GO

CREATE PROCEDURE [dbo].[get_user_karma_current_score] 
    @user_id uniqueidentifier
AS   
    SET NOCOUNT ON;  
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
select @karma_total_score
GO

CREATE PROCEDURE [dbo].[get_user_karma_current_score_detailed] 
    @user_id uniqueidentifier

OUTPUT AS 
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
select * from #Temp order by added_to_karma desc;
--select sum(added_to_karma) from #Temp
GO

CREATE PROCEDURE [dbo].[get_user_karma_current_score_to_var]
    @user_id uniqueidentifier,
	@return_value float OUTPUT
AS   
    SET NOCOUNT ON;  
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
GO

CREATE PROCEDURE [dbo].[make_new_karma_slice]
    @user_id uniqueidentifier
AS   
SET NOCOUNT ON   
declare @curent_karma_score as float
declare @previous_karma_score as float
exec [dbo].[get_user_karma_current_score_to_var] @user_id, @curent_karma_score output
select top 1 @previous_karma_score=[karma_score] from [dbo].[UserKarma_slice] where [user_id] = @user_id order by change_time desc
if (@previous_karma_score = @curent_karma_score)
	begin
		select 'Karma wasn''t changed' as result
	END
else
	begin
		insert into [dbo].[UserKarma_slice] values (newid(),@user_id, @curent_karma_score, @previous_karma_score, getdate())
		select round(@curent_karma_score, 2) as result
	END

GO

CREATE PROCEDURE [dbo].[get_page_karma_and_votes]
    @page_id uniqueidentifier
AS   
SET NOCOUNT ON
	declare @up as float
	declare @down as float
	declare @karma_total_score as float
	set @karma_total_score = 0

select @up = count(*) from [dbo].[Page_Karma_votes] where [page_id] = @page_id and [direction] = 1
select @down = count(*) from [dbo].[Page_Karma_votes] where [page_id] = @page_id and [direction] = 0
set @karma_total_score = @karma_total_score + (@up-@down)
if (@karma_total_score = 0 and @up != @down) 
	begin
	set @karma_total_score = 1
	end;
select @up as up, @down as down, @karma_total_score as karma_total_score
GO

CREATE PROCEDURE [dbo].[make_new_global_karma_slice]
AS   
    SET NOCOUNT ON; 
	DECLARE @user_id as uniqueidentifier
	DECLARE @CURSOR CURSOR
SET @CURSOR = CURSOR SCROLL
FOR
select id from [Karma].[dbo].[KnownPages_Users]
OPEN @CURSOR
FETCH NEXT FROM @CURSOR INTO @user_id
WHILE @@FETCH_STATUS = 0
BEGIN
  exec [dbo].[make_new_karma_slice] @user_id
FETCH NEXT FROM @CURSOR INTO @user_id
END
CLOSE @CURSOR
GO

CREATE PROCEDURE [dbo].[delete_page]
    @page_id uniqueidentifier
AS   
SET NOCOUNT ON

delete [dbo].[KnownPages_contribution] where KnownPageID = @page_id
delete [dbo].[KnownPages_datagrams] where KnownPageID = @page_id
delete [dbo].[KnownPages_UsersContribution] where KnownPageID = @page_id
delete [dbo].[Page_Karma_votes] where page_id = @page_id
delete [dbo].[KnownBugs] where KnownPages_id = @page_id
delete [dbo].[KnownPages] where id = @page_id

GO

CREATE PROCEDURE [dbo].[delete_page_by_page_id]
    @page_id varchar(MAX)
AS   
SET NOCOUNT ON
declare @id as uniqueidentifier
select @id=[id] from [dbo].[KnownPages] where [page_id] = @page_id
delete [dbo].[KnownPages_contribution] where KnownPageID = @id
delete [dbo].[KnownPages_datagrams] where KnownPageID = @id
delete [dbo].[KnownPages_UsersContribution] where KnownPageID = @id
delete [dbo].[Page_Karma_votes] where page_id = @id
delete [dbo].[KnownBugs] where KnownPages_id = @page_id
delete [dbo].[KnownPages] where id = @id

GO

CREATE PROCEDURE [dbo].[get_user_karma_current_score_global]
AS
		declare @page_id as uniqueidentifier
		declare @user_name as nvarchar(MAX)
		declare @user_id as uniqueidentifier
		declare @persent as float
		declare @up as float
		declare @down as float
		DECLARE @CURSOR CURSOR
		DECLARE @CURSOR_users CURSOR
		declare @karma_total_score as float
	SET NOCOUNT ON
	IF OBJECT_ID('tempdb.dbo.#TempKarmaTotal', 'U') IS NOT NULL
	  DROP TABLE #TempKarmaTotal; 
	CREATE TABLE tempdb.dbo.#TempKarmaTotal(user_name nvarchar(MAX), karma_total_score float)

	SET @CURSOR_users = CURSOR SCROLL
	FOR
	SELECT [ID], [user_name] FROM [Karma].[dbo].[KnownPages_Users] where user_name like LOWER('xwiki%') and user_name not in
	('XWiki.bot','XWiki.drozhdestvenskiy','XWiki.XWikiGuest','XWiki.root', 'XWiki.guest')
	OPEN @CURSOR_users
	FETCH NEXT FROM @CURSOR_users INTO @user_id, @user_name
	set @karma_total_score = 0
		WHILE @@FETCH_STATUS = 0
		BEGIN
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
			insert INTO #TempKarmaTotal(user_name, karma_total_score) values (@user_name, @karma_total_score)
			set @karma_total_score = 0
	
	FETCH NEXT FROM @CURSOR_users INTO @user_id, @user_name 
	END
	CLOSE @CURSOR_users
	select user_name, karma_total_score from #TempKarmaTotal order by karma_total_score desc
GO

CREATE TABLE [dbo].[KnownBugs]
(ID uniqueidentifier not Null,
PRIMARY KEY (ID),
KnownPages_id uniqueidentifier not Null,
FOREIGN KEY (KnownPages_id) REFERENCES KnownPages(ID),
bug_id nvarchar(max) not Null,
product nvarchar(max) not Null,
tbfi nvarchar(max) not Null,
components xml not Null
)
CREATE UNIQUE INDEX iKnownPages_id ON KnownBugs (KnownPages_id)
Create PRIMARY XML Index icomponents ON KnownBugs (components)
/*
	drop index KnownPages.iKnownPages_id
	drop index KnownPages.icomponents
    drop table [dbo].[KnownBugs]


*/

USE Karma;  
GO

CREATE PROCEDURE [dbo].[update_or_Add_bug_page]
@KnownPages_id as uniqueidentifier,
@bug_id as varchar(max), 
@product as varchar(max),
@tbfi as varchar(max),
@xml as xml
AS
  BEGIN
   IF NOT EXISTS (SELECT * FROM [dbo].[KnownBugs] 
                   WHERE [KnownPages_id] = @KnownPages_id)
   BEGIN
       insert into [dbo].[KnownBugs] ([ID],[KnownPages_id],[bug_id],[product],[tbfi],[components])
	   values (newid(), @KnownPages_id, @bug_id, @product, @tbfi, @xml)
   END
   ELSE
	BEGIN
	update [dbo].[KnownBugs] set [bug_id] = @bug_id, [product] = @product, [tbfi] = @tbfi, [components] = @xml where [KnownPages_id] = @KnownPages_id
	END
END
GO