  drop table #temp
  select distinct T.N.value('.','varchar(300)') as nodeName, product, bug_id into #temp from [dbo].[KnownBugs] cross apply components.nodes('./components/component/name') as T(N) 

  select distinct nodeName from #temp order by nodeName