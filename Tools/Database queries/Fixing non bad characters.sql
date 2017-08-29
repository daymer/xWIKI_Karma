update [Karma].[dbo].[KnownPages] set page_title=REPLACE(page_title, '“', '"')   where  page_title like  '%“%' 
update [Karma].[dbo].[KnownPages] set page_title=REPLACE(page_title, '”', '"')   where  page_title like  '%”%' 
update [Karma].[dbo].[KnownPages] set page_title=REPLACE(page_title, '&', 'and')   where  page_title like  '%&%'