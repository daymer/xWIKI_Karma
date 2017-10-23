from ldap3 import Server, Connection, ALL, NTLM, ObjectDef, Reader
import ldap3.core.exceptions as exceptions
import Configuration
import logging

requested_hostname = 'sup-a1631'
ldap_conf = Configuration.LdapConfig()
ldap_server = Server(ldap_conf.ad_server, get_info=ALL)
CONN_TO_LDAP = Connection(ldap_server, user=ldap_conf.username, password=ldap_conf.password, authentication=NTLM,
                  auto_bind=True)


def get_ad_host_description(connection_to_ldap,  requested_hostname: str) -> str:
    logger = logging.getLogger('root')
    try:
        # print('Connected to', connection_to_ldap, 'as', connection_to_ldap.extend.standard.who_am_i())
        obj_computer = ObjectDef('computer', connection_to_ldap)
        r = Reader(connection_to_ldap, obj_computer, 'OU=User Computers,DC=amust,DC=local',
                   '(&(objectCategory=computer)(name=' + requested_hostname + '))')
        r.search()
        comp_description = r[0].Description
        return str(comp_description)
    except Exception as error:
        logger.error(error)
        return 'unknown'


result = get_ad_host_description(connection_to_ldap=CONN_TO_LDAP, requested_hostname=requested_hostname)

print(result)