/*    ==Scripting Parameters==

    Source Server Version : SQL Server 2016 (13.0.4206)
    Source Database Engine Edition : Microsoft SQL Server Express Edition
    Source Database Engine Type : Standalone SQL Server

    Target Server Version : SQL Server 2016
    Target Database Engine Edition : Microsoft SQL Server Express Edition
    Target Database Engine Type : Standalone SQL Server
*/

USE [Karma]
GO

/****** Object:  StoredProcedure [dbo].[get_user_karma_raw_score]    Script Date: 10/8/2017 9:09:26 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
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
	select SUM(persent) as karma from #TempTable;  
GO

