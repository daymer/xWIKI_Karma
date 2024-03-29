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
/****** Object:  StoredProcedure [dbo].[make_new_karma_slice]    Script Date: 10/5/2017 10:13:52 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[make_new_karma_slice]') AND type in (N'P', N'PC'))
BEGIN
EXEC dbo.sp_executesql @statement = N'CREATE PROCEDURE [dbo].[make_new_karma_slice] AS' 
END
GO

ALTER PROCEDURE [dbo].[make_new_karma_slice]
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
