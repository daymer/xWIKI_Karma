from PythonConfluenceAPI import ConfluenceAPI
from Configuration import ConfluenceConfig
ConfluenceConfig = ConfluenceConfig()
confluenceAPI = ConfluenceAPI(ConfluenceConfig.USER, ConfluenceConfig.PASS, ConfluenceConfig.ULR)
result = confluenceAPI.get_content_labels('25461027', prefix=None, start=None, limit=None, callback=None)
print(result['size'])
for each in result['results']:
    print(each['name'])
