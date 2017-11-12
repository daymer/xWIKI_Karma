select top 10 lower(requested_url), COUNT(lower(requested_url)) AS MOST_FREQUENT
from [WebRequests] --where user_name = 'XWiki.IKochemasov'
GROUP BY lower(requested_url)
ORDER BY COUNT(lower(requested_url)) DESC