from ldap3 import Server, Connection, ALL, NTLM, ObjectDef, Reader
import ldap3.core.exceptions as exceptions
import Configuration

requested_hostname = 'sup-a1631'

def get_ad_host_description(connection_to_ldap,  requested_hostname: str) -> str:
    try:
        # print('Connected to', connection_to_ldap, 'as', connection_to_ldap.extend.standard.who_am_i())
        obj_computer = ObjectDef('computer', connection_to_ldap)
        r = Reader(connection_to_ldap, obj_computer, 'OU=User Computers,DC=amust,DC=local',
                   '(&(objectCategory=computer)(name=' + requested_hostname + '))')
        r.search()
        comp_description = r[0].Description
        return comp_description
    except Exception as error:
        return 'unknown'


result = get_ad_host_description(ldap_conf=Configuration.LdapConfig(), requested_hostname=requested_hostname)

print(result)