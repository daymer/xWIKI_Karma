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

/****** Object:  Table [dbo].[WebRequests]    Script Date: 11/9/2017 3:42:30 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[WebRequests](
	[ID] [uniqueidentifier] NOT NULL,
	[date] [datetime] NOT NULL,
	[KnownPages_ID] [uniqueidentifier] NULL,
	[requested_url] [nvarchar](300) NOT NULL,
	[user] [nvarchar](300) NOT NULL,
	[source_platform_id] [nvarchar](300) NOT NULL
) ON [PRIMARY]
GO


