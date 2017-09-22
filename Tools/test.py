from Mechanics import SQLConnector
import Configuration

SQL_config_inst = Configuration.SQLConfig()
SQL_Connector_inst = SQLConnector(SQL_config_inst)
xml = '<?xml version="1.0" encoding="UTF-8" ?><components><component><name>BackupToTape</name></component><component><name>BackupValidator</name></component><component><name>BoSS</name></component></components>'
b = bytearray()
b.extend(map(ord, xml))
result = SQL_Connector_inst.Update_or_Add_bug_page(known_pages_id='D65FB534-358B-443D-A704-5E61CDE8909F', bug_id='222444',  product='BNR 9.5.0.1038', tbfi='9.5 update 3', xml=b)
print(result)