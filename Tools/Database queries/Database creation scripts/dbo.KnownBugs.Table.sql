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
/****** Object:  Table [dbo].[KnownBugs]    Script Date: 10/5/2017 10:13:52 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[KnownBugs]') AND type in (N'U'))
BEGIN
CREATE TABLE [dbo].[KnownBugs](
	[ID] [uniqueidentifier] NOT NULL,
	[KnownPages_id] [uniqueidentifier] NOT NULL,
	[bug_id] [nvarchar](max) NOT NULL,
	[product] [nvarchar](max) NOT NULL,
	[tbfi] [nvarchar](max) NOT NULL,
	[components] [xml] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
END
GO
/****** Object:  Index [iKnownPages_id]    Script Date: 10/5/2017 10:13:52 PM ******/
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[KnownBugs]') AND name = N'iKnownPages_id')
CREATE UNIQUE NONCLUSTERED INDEX [iKnownPages_id] ON [dbo].[KnownBugs]
(
	[KnownPages_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ARITHABORT ON
SET CONCAT_NULL_YIELDS_NULL ON
SET QUOTED_IDENTIFIER ON
SET ANSI_NULLS ON
SET ANSI_PADDING ON
SET ANSI_WARNINGS ON
SET NUMERIC_ROUNDABORT OFF
GO
/****** Object:  Index [icomponents]    Script Date: 10/5/2017 10:13:52 PM ******/
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[KnownBugs]') AND name = N'icomponents')
CREATE PRIMARY XML INDEX [icomponents] ON [dbo].[KnownBugs]
(
	[components]
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
GO
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE object_id = OBJECT_ID(N'[dbo].[FK__KnownBugs__Known__123EB7A3]') AND parent_object_id = OBJECT_ID(N'[dbo].[KnownBugs]'))
ALTER TABLE [dbo].[KnownBugs]  WITH CHECK ADD FOREIGN KEY([KnownPages_id])
REFERENCES [dbo].[KnownPages] ([ID])
GO
