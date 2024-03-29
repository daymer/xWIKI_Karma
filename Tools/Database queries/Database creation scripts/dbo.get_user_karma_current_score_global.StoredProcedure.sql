/*    ==Scripting Parameters==

    Source Server Version : SQL Server 2016 (13.0.4206)
    Source Database Engine Edition : Microsoft SQL Server Express Edition
    Source Database Engine Type : Standalone SQL Server

    Target Server Version : SQL Server 2017
    Target Database Engine Edition : Microsoft SQL Server Standard Edition
    Target Database Engine Type : Standalone SQL Server
*/
USE [Karma]
GO
/****** Object:  StoredProcedure [dbo].[get_user_karma_current_score_global]    Script Date: 10/5/2017 10:13:52 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[get_user_karma_current_score_global]') AND type in (N'P', N'PC'))
BEGIN
EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [dbo].[get_user_karma_current_score_global] AS' 
END
GO
ALTER PROCEDURE [dbo].[get_user_karma_current_score_global]
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
	('XWiki.bot','XWiki.XWikiGuest','XWiki.root', 'XWiki.guest', 'XWiki.drozhdestvenskiy')
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
