import requests
import urllib3
session = requests.session()
data = {'grant_type': 'myadmin',
        'client_id': 'mysecretpass'
        }
search_url = 'http://172.24.4.183:80/'
try:
        login_status = session.post(search_url+'login', data=data)
except (urllib3.exceptions.NewConnectionError, ConnectionRefusedError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError) as error:
        print('API unreachable, error: \n', error)
        exit(1)
result = session.get(search_url+'api_check')
if result.status_code != 200 or login_status.status_code != 200:
        print('API unreachable')
        exit(1)
bug_id = '48906'
bug_info = session.get(search_url+'api/bug_details/{0}'.format(bug_id))
bug_info_json = bug_info.json()
print(bug_info_json['results']['Created Date'])
print(bug_info_json['results']['Changed Date'])
print(bug_info_json['results']['State'])
print(bug_info_json['results']['Status'])
print(bug_info_json['results']['Build'])
