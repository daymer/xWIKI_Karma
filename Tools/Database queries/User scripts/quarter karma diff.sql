DROP TABLE IF EXISTS #results
create table #results (
[user_id] uniqueidentifier,
[delta] float
)
declare @user_id uniqueidentifier,
 @user_count int,
 @karma_start float,
 @karma_stop float,
 @CURSOR CURSOR,
 @date_start date = '2018-04-01',
 @date_end date = '2018-06-30'
SET @CURSOR = CURSOR SCROLL
FOR
  select distinct [user_id] FROM [Karma].[dbo].[UserKarma_slice]
OPEN @CURSOR
FETCH NEXT FROM @CURSOR INTO @user_id
WHILE @@FETCH_STATUS = 0
BEGIN
	DROP TABLE IF EXISTS #temp
	set @user_count = 0
	select @user_count=count(@user_id) from [dbo].[UserKarma_slice] where user_id = @user_id
		if @user_count <2 
			BEGIN
				print Convert(varchar(36), @user_id) + ' has only 1 slice, ignoring'
				FETCH NEXT FROM @CURSOR INTO @user_id
				CONTINUE
			END
		ELSE  
			BEGIN
				select [dbo].[KnownPages_Users].user_name, karma_score, change_time into #temp
						  from [dbo].[UserKarma_slice]
						  inner join [dbo].[KnownPages_Users] on [dbo].[KnownPages_Users].ID = [user_id] 
						  where [user_id] = @user_id and change_time between @date_start and @date_end
						  order by  change_time
				select top 1 @karma_start=karma_score from #temp order by change_time 
				select top 1 @karma_stop=karma_score from #temp order by change_time desc
				insert into #results values (@user_id, @karma_stop-@karma_start)
			END
	
FETCH NEXT FROM @CURSOR INTO @user_id
END
CLOSE @CURSOR

select [dbo].[KnownPages_Users].user_name, delta from #results
inner join [dbo].[KnownPages_Users] on [dbo].[KnownPages_Users].ID =#results.[user_id] 
order by delta desc