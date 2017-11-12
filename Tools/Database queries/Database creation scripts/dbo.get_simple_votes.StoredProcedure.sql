/*    ==Scripting Parameters==

    Source Server Version : SQL Server 2017 (14.0.3006)
    Source Database Engine Edition : Microsoft SQL Server Enterprise Edition
    Source Database Engine Type : Standalone SQL Server

    Target Server Version : SQL Server 2017
    Target Database Engine Edition : Microsoft SQL Server Enterprise Edition
    Target Database Engine Type : Standalone SQL Server
*/

USE [Karma]
GO

/****** Object:  StoredProcedure [dbo].[get_simple_votes]    Script Date: 11/12/2017 5:42:07 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[get_simple_votes]
    @seed varchar(300)
AS   
SET NOCOUNT ON
	declare @up as float
	declare @down as float
	declare @karma_total_score as float
	set @karma_total_score = 0

select @up = count(*) from [dbo].[Simple_votes] where [seed] = @seed and [direction] = 1
select @down = count(*) from [dbo].[Simple_votes] where [seed] = @seed and [direction] = 0
set @karma_total_score = @karma_total_score + (@up-@down)
select @up as up, @down as down, @karma_total_score as total
GO

