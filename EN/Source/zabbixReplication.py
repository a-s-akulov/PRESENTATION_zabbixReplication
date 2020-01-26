############### NOTE TEST - 192.168.3.80 NOTE ####################







try:
    import os
    import sys
    import requests
    import pyodbc
    import time
    from datetime import datetime
except BaseException as error:
    input(f"\n An error has occurred when the program tried to import some module. Error:\n\n{error}\n\n Press ENTER to exit")
    exit()

try:
    from my_modules import my_json
    from my_modules import my_sql
except BaseException as error:
    input(f"\n An error has occurred when the program tried to import some module from 'my_modules' directory. Error:\n\n{error}\n\n Press ENTER to exit")
    sys.exit(0)

# NOTE:
# Роутер (IPSec)= 15
# Камера, камера(кабинет) = 19
# WAN1 = 16
# WAN2 = 17
# KKT = 34

# name = Shop + GroupName + host

class ZabbixReplication():
    """Replication zabbix server with other database.

    Autor: akulov.a
    Organization website: www.chitai-gorod.du

    def autoReplication - start automaticaly replication

    """
    def __init__(self):
        """ SET PARAMS. """

        # Groups: ZabbixGroup = [WorkspaceGroups]], [TemplatesId], ProxyId
        self.GROUPS = {
            '15': ([8], ["36497", "36498"], "0"), # IPSec = ([Роутер], ["36497", "36498"] Templates, NoProxy)
            '19': ([6, 19], ["36499","36500"], "36505"), # Камеры = ([Камера, Камера (кабинет)], ["36499","36500"] Templates, NoProxy)
            '16': ([14], ["36501"]["36501"], "36506"), # WAN1 = (WAN1, ["36501"]["36501"] s, NoProxy)
            '17': ([21], ["36502"], "0"), # WAN2 = (WAN2, 36502 Template, NoProxy)
            '34': ([20], ["36503","36504"], "36506"), # KKT = (ККТ, ["36503","36504"] Templates, proxyid='26037')
        }

        # Maintenance groups: City timezone = Zabbix hostGroup (zabbix group in some maintenance group)
        self.maintenanceGroups = {
            2: "53",
            3: "43", # timezone 3: Moscow = zabbix hostGroup '56'
            4: "45",
            5: "46",
            6: "47",
            7: "48",
            8: "49",
            9: "50",
            10: "51",
            11: "52",
            "default": "", # if not found delta at SQL server, or if timezone not defined at self.maintenanceGroups - set this group (if "" - no group)
        }

        self.excludePrefix = "[!]" # Если отображаемое имя хоста в Zabbix начинается с него - хост не удаляется (игнорируется программой)

        # TRIGGERS
        self.TRIGGERS = {
            # '15':
            # {
            #     "15group_1type_trigger_009ver": # IDENTIFICATOR of trigger - sets as description
            #     {
            #         'expression': r'{%hostName%:agent.ping.last()}=0',
            #         'comments': r'',
            #         'url': r'',
            #         'recovery_expression': r'',
            #         'correlation_tag': r'',
            #         'priority': r'4',
            #         'status': r'0',
            #         'type': r'0',
            #         'recovery_mode': r'0',
            #         'correlation_mode': r'0',
            #         'manual_close': r'0',

            #         'tags': [
            #         ],

            #     },
            # },
        }

        # ITEMS
        self.ITEMS = {
            # '15':
            # {
            #     "15group_1type_item_001ver": # IDENTIFICATOR of item - sets as name
            #     {
            #         'description': r'',
            #         'key_': r'agent.ping',
            #         'url': r'',
            #         'type': r'0',
            #         'value_type': r'3',
            #         'delay': r'30s',
            #         'http_proxy': r'',
            #         'ipmi_sensor': r'',
            #         'jmx_endpoint': r'',
            #         'logtimefmt': r'',
            #         'params': r'',
            #         'password': r'',
            #         'port': r'',
            #         'posts': r'',
            #         'privatekey': r'',
            #         'publickey': r'',
            #         'snmp_community': r'',
            #         'snmp_oid': r'',
            #         'snmpv3_authpassphrase': r'',
            #         'snmpv3_contextname': r'',
            #         'snmpv3_privpassphrase': r'',
            #         'snmpv3_securityname': r'',
            #         'ssl_cert_file': r'',
            #         'ssl_key_file': r'',
            #         'ssl_key_password': r'',
            #         'status_codes': r'200',
            #         'timeout': r'3s',
            #         'trapper_hosts': r'',
            #         'units': r'',
            #         'username': r'',
            #         'valuemapid': r'0',
            #         'allow_traps': r'0',
            #         'authtype': r'0',
            #         'follow_redirects': r'1',
            #         'history': r'90d',
            #         'inventory_link': r'0',
            #         'master_itemid': r'0',
            #         'output_format': r'0',
            #         'post_type': r'0',
            #         'request_method': r'0',
            #         'retrieve_mode': r'0',
            #         'snmpv3_authprotocol': r'0',
            #         'snmpv3_privprotocol': r'0',
            #         'snmpv3_securitylevel': r'0',
            #         'status': r'0',
            #         'trends': r'365d',
            #         'verify_host': r'0',
            #         'verify_peer': r'0',

            #         'applications': [
            #         ],


            #         'preprocessing': [
            #         ],
            #     },
            # },
        }

        self.forceRebuildTriggersDependencies = False # if True - rebuilds all dependencies for all triggers
        self.triggersDependencies = {
            '15': # IpSec
            {
                'High ICMP ping loss':
                {
                    'Unavailable by ICMP ping': ['15'],
                },
                'High ICMP ping response time':
                {
                    'Unavailable by ICMP ping': ['15'],
                },
                'Unavailable by ICMP ping':
                {
                    'Unavailable by ICMP ping': ['16', '17'],
                },
            },

            '19': # CAMS
            {
                'High ICMP ping loss':
                {
                    'Unavailable by ICMP ping': ['19'],
                },
                'High ICMP ping response time':
                {
                    'Unavailable by ICMP ping': ['19'],
                    'High ICMP ping loss': ['19'],
                },
            },

            '16': # WAN1
            {
                'High ICMP ping loss':
                {
                    'Unavailable by ICMP ping': ['16'],
                },
                'High ICMP ping response time':
                {
                    'High ICMP ping loss': ['16'],
                    'Unavailable by ICMP ping': ['16'],
                },
            },

            '17': # WAN2
            {
                'High ICMP ping loss':
                {
                    'Unavailable by ICMP ping': ['17'],
                },
                'High ICMP ping response time':
                {
                    'High ICMP ping loss': ['17'],
                    'Unavailable by ICMP ping': ['17'],
                },
            },

        }

        self.shutdownTime = 10 # Delay until program closes after replication is completed (seconds)




        # start logging
        self.logfileName = "" # DON'T TUCH!
        self.logging = False # DON'T TUCH!
        self.log_init()

        self.addHosts = dict()
        self.deleteHosts = list()







    # START PROGRAM
    def auto_replication(self):
        """Automaticaly data replicate zabbix server with other database."""
        self._katprint(f"[INFO] Autor: akulov.a\n [INFO] Program is entended for data replication from SQL server to Zabbix\n\n\n")
        self.updatedShops = set()
        SQL.get_sql_data()
        JSON.get_json_data()

        # Create an list of hosts for delete
        self.get_list_delete()

        # Delete hosts from Zabbix (exclude duplicates)
        if len(self.deleteHosts) != 0:
            self._katprint(">>> Deleting uncorrect hosts from Zabbix (exclude duplicates)...")
            list_ = [JSON.jsonHosts['hosts'][s]['host']['hostid'] for s in self.deleteHosts]

            # DELETING HOSTS FROM ZABBIX!!!!
            JSON.delete_json_hosts(list_)
            for s in self.deleteHosts:
                host = JSON.jsonHosts['hosts'][s]['host']
                self._katprint(f"> Uncorrect host deleted. IP: '{s}', jsonGroup: {host['jsonGroup']}, "\
                    f"maintenanceGroup: '{host['maintenanceGroup']}', Name: '{host['name']}', templates: '{host['templates']}', "\
                    f"proxy: '{host['proxy']}'")
                # clear JSON.jsonHosts
                self.del_from_jsonHosts(ip=s)
                
            self._katprint(f"\n> Uncorrect hosts successfully deleted ({len(self.deleteHosts)})\n")
        else:
            self._katprint(">>> No uncorrect hosts detected (exclude duplicates)\n")

        # Delete duplicate hosts
        if len(JSON.duplicates) != 0:
            self._katprint(">>> Deleting duplicate hosts from Zabbix...")

            # DELETING HOSTS FROM ZABBIX!!!!
            JSON.delete_json_hosts(JSON.duplicates)

            for hostid in JSON.duplicates:
                # clear JSON.jsonHosts
                if hostid in JSON.jsonHosts['hostids']:
                    host = JSON.jsonHosts['hosts'][JSON.jsonHosts['hostids'][hostid]]['host']
                    self._katprint(f"> Duplicate host deleted. IP: '{s}', jsonGroup: {host['jsonGroup']}, "\
                        f"maintenanceGroup: '{host['maintenanceGroup']}', Name: '{host['name']}', templates: '{host['templates']}', "\
                        f"proxy: '{host['proxy']}'")
                    self.del_from_jsonHosts(ip=JSON.jsonHosts['hostids'][hostid])
                else:
                    self._katprint(f"> Duplicate host deleted. hostid: {hostid}")

            JSON.duplicates = list()
            self._katprint(f"\n> Duplicate hosts successfully deleted ({len(JSON.duplicates)})\n")
        else:
            self._katprint(">>> No duplicate hosts detected\n")


        # ADD TO ZABBIX
        self._katprint(">>> Adding hosts from SQL to Zabbix...")
        self.get_list_add()
        ##################################################################
        added = 0
        for shopid_ in self.addHosts:
            for ip_ in self.addHosts[shopid_]:
                host_ = self.addHosts[shopid_][ip_]
                jsonGroup = host_['host']['jsonGroup']
                # ADD HOST TO ZABBIX!!!
                hostid = JSON.add_json_host(
                    shopid_,
                    jsonGroup,
                    ip_,
                    host_['host']['name'],
                    templates = host_['host']['templates'],
                    maintenanceGroup = host_['host']['maintenanceGroup'],
                    proxy = host_['host']['proxy'],
                    items = self.ITEMS[jsonGroup] if jsonGroup in self.ITEMS else {},
                    triggers = self.TRIGGERS[jsonGroup] if jsonGroup in self.TRIGGERS else {}
                )

                self._katprint(f"> Host added. IP: '{ip_}'"\
                    f", Group: {jsonGroup}"\
                    f", Name: '{host_['host']['name']}'"\
                    f", templates: '{host_['host']['templates']}'"\
                    f", maintenanceGroup: '{host_['host']['maintenanceGroup']}'"\
                    f", proxy: '{host_['host']['proxy']}'"\
                )

                added += 1
            self.updatedShops.add(shopid_)
        
        shopsToRebuildTriggers = set()
        if self.forceRebuildTriggersDependencies:
            shopsToRebuildTriggers = JSON.jsonHosts['shopids'].keys()
        else:
            shopsToRebuildTriggers = self.updatedShops
        ##################################################################
        del(self.addHosts)
        self._katprint(f"\n > Operation succesfully completed!\n > Added {added} hosts.\n\n"\
            ">>> Rebuilding triggers dependencies...")
        if len(self.triggersDependencies) == 0 or len(shopsToRebuildTriggers) == 0:
            self._katprint("> No triggers to rebuild dependencies.")
        else:
            self.rebuild_triggers_dependencies(shopsToRebuildTriggers)
            self._katprint("\n> Triggers dependencies rebuilded succesfully!\n")

        # FINALLY ALL OPERATIONS DONE, GO SLEEP
        self._katprint(f"\n\n===> Replication successfully completed, system shutdown after {self.shutdownTime} seconds.")
        time.sleep(self.shutdownTime)
        input("\n Press ENTER to exit") # KATTEST
        return 0
    

    # MAIN FNCS
    def get_list_add(self):
        """Create list of adding hosts.
        
        self.addHosts structure:
        {
            '%shopId%':
            {
                '%ip%':
                {
                    'host':
                    {
                        'shopId': int,
                        'sqlGroup': int,

                        'jsonGroup': str,
                        'ip': str,
                        'name': str,
                        'templates': [str],
                        'maintenanceGroup': str,
                        'proxy': str,

                        # ONLY AFTER ADDING
                        'hostid': str,
                        'interfaceid': str,
                    },
                },
            },
        }
        
        """
        self.addHosts = dict()
        availableGrps = []
        for x in self.GROUPS:
            availableGrps.extend(self.GROUPS[x][0])

        for s in SQL.sqlHosts:
            if s in JSON.jsonHosts['hosts']:
                continue

            sqlData = SQL.sqlHosts[s]
            sqlShopid = sqlData[0]
            sqlGroup = sqlData[1]
            sqlMaintenanceGroup = self.get_maintanenceGroup(SQL.sqlShops[sqlShopid]['timedelta'])
            sqlName = f"{SQL.sqlShops[sqlShopid]['name']} - {SQL.sqlHostTypes[sqlGroup]} - {s}"

            if sqlGroup not in availableGrps:
                continue

            jsonGroup = self.find_group_json(sqlGroup)
            templates = self.GROUPS[jsonGroup][1]
            proxy = self.GROUPS[jsonGroup][2]

            # creating host structure:
            if not sqlShopid in self.addHosts:
                self.addHosts[sqlShopid] = dict()
            self.addHosts[sqlShopid][s] = dict()
            self.addHosts[sqlShopid][s]["host"] = dict()

            host = self.addHosts[sqlShopid][s]

            # assembling host['host']:
            host['host']['shopId'] = sqlShopid
            host['host']['sqlGroup'] = sqlGroup

            host['host']['jsonGroup'] = jsonGroup
            host['host']['ip'] = s
            host['host']['name'] = sqlName
            host['host']['templates'] = templates
            host['host']['maintenanceGroup'] = sqlMaintenanceGroup
            host['host']['proxy'] = proxy
    
            self.addHosts[sqlShopid][s] = host


    def get_list_delete(self):
        """Check if data from Zabbix is correct.

        Crates list 'self.deleteHosts' of uncorrect hosts

        """
        self._katprint(">>> Calculating list of hosts for delete from Zabbix...")
        self.deleteHosts = list()
        for s in JSON.jsonHosts['hosts']:
            jsonData = JSON.jsonHosts['hosts'][s]
            jsonShopid = jsonData['host']['shopid']
            jsonHostid = jsonData['host']['hostid']
            jsonName = jsonData['host']['name']
            jsonTemplates = jsonData['host']['templates']
            jsonProxy = jsonData['host']['proxy']
            jsonItems = jsonData['items']
            jsonTriggers = jsonData['triggers']

            if jsonData['host']['jsonGroup'] in self.GROUPS:
                jsonGroup = jsonData['host']['jsonGroup']
                jsonMaintenanceGroup = jsonData['host']['maintenanceGroup']
            elif jsonData['host']['maintenanceGroup'] in self.GROUPS:
                jsonGroup = jsonData['host']['maintenanceGroup']
                jsonMaintenanceGroup = jsonData['host']['jsonGroup']
                jsonData['host']['jsonGroup'] = jsonGroup
                jsonData['host']['maintenanceGroup'] = jsonMaintenanceGroup
            else:
                continue

            if jsonName.startswith(self.excludePrefix):
                continue

            # Duplicates are deletes after self.deleteHosts list - this condition is for eliminating errors
            if jsonHostid in JSON.duplicates:
                continue

            if s not in SQL.sqlHosts:
                self.deleteHosts.append(s)
                continue
            
            sqlData = SQL.sqlHosts[s]
            sqlShopid = sqlData[0]
            sqlGroup = sqlData[1]
            sqlMaintenanceGroup = self.get_maintanenceGroup(SQL.sqlShops[sqlShopid]['timedelta'])
            sqlName = f"{SQL.sqlShops[sqlShopid]['name']} - {SQL.sqlHostTypes[sqlGroup]} - {s}"

            if jsonShopid != sqlShopid:
                self.deleteHosts.append(s)
                continue
            
            if jsonGroup not in self.GROUPS:
                self._fatal_error(f"Can't calculate delete list\n jsonGroup not in self.GROUPS!\n JSON data = '{s}': {jsonData}")
                return

            if sqlGroup not in self.GROUPS[jsonGroup][0]:
                self.deleteHosts.append(s)
                continue

            if len(jsonTemplates) != len(self.GROUPS[jsonGroup][1]):
                self.deleteHosts.append(s)
                continue

            # TEMPLATES
            if len(jsonTemplates) != len(self.GROUPS[jsonGroup][1]):
                self.deleteHosts.append(s)
                continue
            else:
                delete = False
                for templateid in self.GROUPS[jsonGroup][1]:
                    if templateid not in jsonTemplates:
                        delete = True
                        break
                if delete:
                    self.deleteHosts.append(s)
                    continue

            if jsonProxy != self.GROUPS[jsonGroup][2]:
                self.deleteHosts.append(s)
                continue

            if jsonName != sqlName:
                self.deleteHosts.append(s)
                continue

            if jsonMaintenanceGroup != sqlMaintenanceGroup:
                self.deleteHosts.append(s)
                continue

            # ITEMS and TRIGGERS
            countItemsConfigured = len(self.ITEMS[jsonGroup]) if jsonGroup in self.ITEMS else 0
            if len(jsonItems) < countItemsConfigured:
                self.deleteHosts.append(s)
                continue
            if jsonGroup in self.ITEMS:
                delete = False
                for item_ in self.ITEMS[jsonGroup]:
                    if not item_ in jsonItems:
                        delete = True
                        break
                if delete:
                    self.deleteHosts.append(s)
                    continue
            
            countTriggersConfigured = len(self.TRIGGERS[jsonGroup]) if jsonGroup in self.TRIGGERS else 0
            if len(jsonTriggers) < countTriggersConfigured:
                self.deleteHosts.append(s)
                continue
            if jsonGroup in self.TRIGGERS:
                delete = False
                for trigger_ in self.TRIGGERS[jsonGroup]:
                    if not trigger_ in jsonTriggers:
                        delete = True
                        break
                if delete:
                    self.deleteHosts.append(s)
                    continue

        self._katprint(f"> Delete list successfully calculated\n > Hosts for delete count (exclude duplicates): {len(self.deleteHosts)}\n")
    
    
    def find_group_json(self, sqlGroup):
        """Returns jsonGroup from self.GROUPS by one of sqlGroup."""
        jsonGroup = -1
        for idx, x in enumerate(self.GROUPS.values()):
            if sqlGroup in x[0]:
                jsonGroup = list(self.GROUPS.keys())[idx]
                break
        return jsonGroup

    def get_maintanenceGroup(self, delta: int):
        """Returns maintenanceGroup by delta with Moscow."""
        if delta == None:
            return self.maintenanceGroups["default"]

        timezone = 3 + delta
        return self.maintenanceGroups[timezone] if timezone in self.maintenanceGroups else self.maintenanceGroups["default"]


    def del_from_jsonHosts(self, ip=""):
        """Deleting all host's data from JSON.jsonHosts by ip."""
        try:
            host = JSON.jsonHosts['hosts'][ip]['host']
            hostid = host['hostid']
            shopid = host['shopid']
            jsonGroup = host['jsonGroup']

            # clear JSON.jsonHosts['hostids']
            del(JSON.jsonHosts['hostids'][hostid])

            # clear JSON.jsonHosts['shopids']
            if shopid in JSON.jsonHosts['shopids']:
                del(JSON.jsonHosts['shopids'][shopid][jsonGroup][hostid])
                if len(JSON.jsonHosts['shopids'][shopid][jsonGroup]) == 0:
                    del(JSON.jsonHosts['shopids'][shopid][jsonGroup])
                    if len(JSON.jsonHosts['shopids'][shopid]) == 0:
                        del(JSON.jsonHosts['shopids'][shopid])

            # clear JSON.jsonHosts['hosts']         
            del(JSON.jsonHosts['hosts'][ip])
        except BaseException as error:
            MAIN._fatal_error(error)

    
    def rebuild_triggers_dependencies(self, shopids: set):
        """Rebuild dependencies of all host's triggers in given shoplist."""
        self._katprint("> Getting currect triggers for updated shops...")
        hostids = set()
        for shopid in shopids:
            for jsonGroup in JSON.jsonHosts['shopids'][shopid]:
                for hostid in JSON.jsonHosts['shopids'][shopid][jsonGroup]:
                    ip = JSON.jsonHosts['shopids'][shopid][jsonGroup][hostid]

                    hostids.add(hostid)
                    JSON.jsonHosts['hosts'][ip]['triggers'] = dict() # clear JSON.jsonHosts['hosts'][ip]['triggers']

        triggers = JSON.return_triggers_by_hostid(list(hostids), select={
            'selectHosts': 'hostid'
        })

        triggerids = set()
        for trigger_ in triggers:
            for host_ in trigger_['hosts']:
                if not host_['hostid'] in JSON.jsonHosts['hostids']:
                    continue
                
                hostid = host_['hostid']
                ip = JSON.jsonHosts['hostids'][hostid]
                host = JSON.jsonHosts['hosts'][ip]

                description = trigger_['description']
                triggerid = trigger_['triggerid']

                host['triggers'][description] = {
                    'description': description,
                    'triggerid': triggerid,
                }

                triggerids.add(triggerid)
        del(triggers)

        self._katprint("> Clearing all dependencies for updated shops...")
        JSON.clear_trigger_dependencies(triggerids)
        self._katprint("> Building new dependencies...")

        dependencies = list()
        for shopid in shopids:
            for jsonGroup in JSON.jsonHosts['shopids'][shopid]:
                if jsonGroup not in self.triggersDependencies:
                    continue
                
                # ELSE
                dependGroupTemplate = self.triggersDependencies[jsonGroup]
                for hostid in JSON.jsonHosts['shopids'][shopid][jsonGroup]:
                    ip = JSON.jsonHosts['shopids'][shopid][jsonGroup][hostid]
                    ipFinder = ip[:ip.rfind(".") + 1]
                    host = JSON.jsonHosts['hosts'][ip]

                    for description in host['triggers']:
                        if description not in dependGroupTemplate:
                            continue
                        
                        # ELSE
                        for dependDescription in dependGroupTemplate[description]:
                            for dependJsonGroup in dependGroupTemplate[description][dependDescription]:
                                # FIND DEPENDENTED HOST
                                dependHost = host
                                if jsonGroup != dependJsonGroup:
                                    if dependJsonGroup not in JSON.jsonHosts['shopids'][shopid]:
                                        continue
                                    
                                    # ELSE
                                    dependIps = [ JSON.jsonHosts['shopids'][shopid][dependJsonGroup][hostid_] for hostid_ in JSON.jsonHosts['shopids'][shopid][dependJsonGroup] ]
                                    if len(dependIps) == 0:
                                        continue
                                    elif len(dependIps) == 1:
                                        dependHost = JSON.jsonHosts['hosts'][dependIps[0]]
                                    else:
                                        for dependIp in dependIps:
                                            if dependIp.startswith(ipFinder):
                                                dependHost = JSON.jsonHosts['hosts'][dependIp]
                                                break
                                        else:
                                            dependHost = JSON.jsonHosts['hosts'][dependIps[0]]

                                # FIND DEPENDENTED TRIGGERID
                                if dependDescription not in dependHost['triggers']:
                                    continue

                                # ELSE
                                dependTriggerid = dependHost['triggers'][dependDescription]['triggerid']
                                dependencies.append({
                                    'triggerid': host['triggers'][description]['triggerid'],
                                    'dependsOnTriggerid': dependTriggerid,
                                })
        self._katprint(f"> Dependencies builded for {len(shopids)} shop(s)")
        self._katprint(f"> Sending a request to the server...")
        JSON.create_trigger_dependencies(dependencies)


    # OTHER FNCS
    # def city_from_str(self, string: str):
    #     """ Returns city, getted from the string."""
    #     if not "(город)" in string.lower():
    #         return "Москва"

    #     string = string[:string.find("(")]
    #     string = string.strip()

    #     if string.lower().startswith("тц"):
    #         string = string[2:].strip()
    #         if " " in string:
    #             string = string[string.find(" "):].strip()

    #     if string.lower().endswith("бс"):
    #         string = string[:-2].strip()

    #     if string[-1].isdecimal():
    #         string = string[:-2]
    #     string = string.strip()

    #     string = string.replace("Ё", "Е").replace("ё", "е")

    #     return string


    def log_init(self):
        """Initialiazation of logs."""
        now = self.dateTime()
        date = now["date"]
        time = now["time"]

        logfileName = f"log\\{date}"
        if not os.path.exists(logfileName):
            try:
                os.makedirs(logfileName, exist_ok=True)
            except:
                self.logging = False
                self._fatal_error(f"Error to create an catalog '{logfileName}' for logfile!")
                return
        self.logfileName = f"{time.replace(':', '_' )}.log"
        self.logging = True
        self._katprint(f"[INFO] Logging started successfully\n")


    def _katprint(self, text):
        now = self.dateTime()
        date = now["date"]
        time = now["time"]
        file_name = f"log\\{date}\\{self.logfileName}"
        file_ = None

        if not self.logging:
            print(text)
            return
        
        # if logging is activated:
        if not os.path.exists(f"log\\{date}"):
            self.log_init()

        if os.path.exists(file_name):
            try:
                file_ = open(file_name, "a", encoding="utf-8")
            except:
                self.logging = False
                self._fatal_error(f"Error to open logfile '{file_name}'!")
                return
            else:
                with file_:
                    print(f" {time} {text}", file=file_)
                    print(f" {text}")
        else:
            print(f" {time} [LOG] Logfile is not founded! Try to create '{file_name}' file...")
            try:
                file_ = open(file_name, "w", encoding="utf-8")
            except:
                self.logging = False
                self._fatal_error(f"Error to create logfile '{file_name}'!")
                return
            else:
                print(f" {time} [LOG] Logfile created successfully.\n")
                with file_:
                    print(f" {time} {text}", file=file_)
                print(f" {text}")


    def dateTime(self):
        """Returns dictionary with 'date' and 'time' keys."""
        now = datetime.now()
        return {"date": f"{str(now.day).zfill(2)}.{str(now.month).zfill(2)}.{now.year}", "time": f"{str(now.hour).zfill(2)}:{str(now.minute).zfill(2)}:{str(now.second).zfill(2)}"}

    
    def _fatal_error(self, text):
        text = f"[ERROR] {text}\n"
        if self.logging:
            self._katprint(text)
        else:
            print(text)

        input(" Press ENTER to exit")
        sys.exit(0)




if __name__ == "__main__":
    MAIN = ZabbixReplication()
    SQL = my_sql.FncsSQL(MAIN, pyodbc)
    JSON = my_json.FncsJSON(MAIN, requests, os)
    MAIN.auto_replication()