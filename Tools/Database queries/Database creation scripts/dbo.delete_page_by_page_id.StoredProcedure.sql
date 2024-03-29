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
/****** Object:  StoredProcedure [dbo].[delete_page_by_page_id]    Script Date: 10/5/2017 10:13:52 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[delete_page_by_page_id]') AND type in (N'P', N'PC'))
BEGIN
EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [dbo].[delete_page_by_page_id] AS' 
END
GO
ALTER PROCEDURE [dbo].[delete_page_by_page_id]
    @page_id varchar(MAX)
AS   
SET NOCOUNT ON
declare @id as uniqueidentifier
select @id=[id] from [dbo].[KnownPages] where [page_id] = @page_id
delete [dbo].[KnownPages_contribution] where KnownPageID = @id
delete [dbo].[KnownPages_datagrams] where KnownPageID = @id
delete [dbo].[KnownPages_UsersContribution] where KnownPageID = @id
delete [dbo].[Page_Karma_votes] where page_id = @id
delete [dbo].[KnownBugs] where KnownPages_id = @id
delete [dbo].[KnownPages] where id = @id

GO
