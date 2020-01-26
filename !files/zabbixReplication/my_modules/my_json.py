class FncsJSON():
    """JSON module."""
    def __init__(self, parent, jsonModule, osModule):
        """Params initialization.
        
        params: server, login, password - getting from user environment variables ('MyZabbix_server', 'MyZabbix_login', 'MyZabbix_password').
        
        """
        global MAIN, requests, os
        MAIN, requests, os = parent, jsonModule, osModule

        self.jsonHosts = dict()
        self.jsonHosts['hostids'] = dict()
        self.duplicates = []
        self.authKey = -1

        # ZABBIX CONFIG PARAMS
        self.JSONConfig = {
            "server": os.environ.get("MyZabbix_server"), # user environment variable 'MyZabbix_server'
            "login": os.environ.get("MyZabbix_login"), # user environment variable 'MyZabbix_login'
            "password": os.environ.get("MyZabbix_password"), # user environment variable 'MyZabbix_password'
            "headers": {"Content-Type": "application/json-rpc"},
            }
        for s in ["server", "login", "password"]:
            if self.JSONConfig[s] == None:
                MAIN._fatal_error(f"""Can't use user environment variable 'MyZabbix_{s}' - returned '{str(self.JSONConfig[s])}'""")
                return



    def get_json_data(self):
        """Get hosts list from zabbix server to self.jsonHosts.
        
        self.jsonHosts structure:
        {
            'hostids':
            {
                '%hostid%': str, (IP)
            },

            'shopids':
            {
                '%shopid%':
                {
                    '%jsonGroup%':
                    {
                        '%hostid%': str, (IP)
                    },
                },
            },

            'hosts':
            {
                '%ip%':
                {
                    'host':
                    {
                        'shopid': int,
                        'sqlGroups': [int],
                        'jsonGroup': str,
                        'ip': str,
                        'name': str,
                        'systemName': str,
                        'templates': [str],
                        'maintenanceGroup': str,
                        'proxy': str,
                        'hostid': str,
                        'interfaceid': str,
                    },

                    'items':
                    {
                        '%name%':
                        {
                            'name': str,
                            'itemid': str
                        },
                    },

                    'triggers':
                    {
                        '%description%':
                        {
                            'description': str,
                            'triggerid': str,
                        }
                    },
                },
            }
        }
        
        """
        query = {
                   "jsonrpc": "2.0",
                    "method": "user.login",
                    "params": {
                        "user": self.JSONConfig["login"],
                        "password": self.JSONConfig["password"]
                    },
                    "id": 0,
                    "auth": None
                }

        # get authentication key to self.authKey
        MAIN._katprint(f""">>> Getting Authentication key from server '{self.JSONConfig["server"]}'...""")
        answer = self.send_json_request(query)
        if "result" in answer:
            self.authKey = answer["result"]
        else:
            MAIN._fatal_error(f"""Can't jet authKey from server '{self.JSONConfig["server"]}'\n"""\
                    f""" answer['result'] error: '{ "UNKNOWN" if "error" not in answer else answer["error"]}'.""")
            return
        MAIN._katprint(f"""> Authentication key successfully received\n""")

        # TIME TO GET HOSTS
        MAIN._katprint(f""">>> Getting data from Zabbix server...""")

        self.jsonHosts = dict()
        self.jsonHosts['hostids'] = dict()
        self.jsonHosts['shopids'] = dict()
        self.jsonHosts['hosts'] = dict()
        query = {
                   "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "output": ["host", "name", "proxy_hostid"],
                        "selectInterfaces": ["ip", "interfaceid"],
                        "selectParentTemplates": ["templateid"],
                        "selectGroups": []
                    },
                    "id": 1,
                    "auth": self.authKey
                }
        answer = self.send_json_request(query)
        if "result" in answer:
            for x in answer["result"]:
                ip = x["interfaces"][0]["ip"]
                interfaceid = x["interfaces"][0]["interfaceid"]
                hostid = x["hostid"]
                group = x["groups"][0]["groupid"]
                name = x["name"]
                templates = [ template_['templateid'] for template_ in x["parentTemplates"] ]
                maintenanceGroup = x["groups"][1]["groupid"] if len(x["groups"]) > 1 else ""
                proxy = x["proxy_hostid"]

                shopid = x["host"].split("_")
                shopid = shopid[1] if len(shopid) == 2 else "-1"
                try:
                    shopid = int(shopid)
                except:
                    shopid = -1

                if group not in MAIN.GROUPS:
                    if maintenanceGroup in MAIN.GROUPS:
                        group, maintenanceGroup = maintenanceGroup, group
                    else:
                        continue

                # if already exists - add to duplicate list this and first and continue to next step of FOR
                if ip in self.jsonHosts['hosts']:
                    self.duplicates.append(hostid)
                    first = self.jsonHosts['hosts'][ip]
                    if first['host']['hostid'] not in self.duplicates:
                        self.duplicates.append(first['host']['hostid'])
                    continue
                
                # assembling self.jsonHosts['hostids']:
                self.jsonHosts['hostids'][hostid] = ip

                # assembling self.jsonHosts['shopids']
                if not shopid in self.jsonHosts['shopids']:
                    self.jsonHosts['shopids'][shopid] = dict()
                if not group in self.jsonHosts['shopids'][shopid]:
                    self.jsonHosts['shopids'][shopid][group] = dict()
                self.jsonHosts['shopids'][shopid][group][hostid] = ip
                
                # assembling self.jsonHosts['hosts']
                self.jsonHosts['hosts'][ip] = dict()
                self.jsonHosts['hosts'][ip]['items'] = dict()
                self.jsonHosts['hosts'][ip]['triggers'] = dict()
                self.jsonHosts['hosts'][ip]['host'] = {
                    'shopid': shopid,
                    'sqlGroup': MAIN.GROUPS[group][0] if group in MAIN.GROUPS else [],
                    'jsonGroup': group,
                    'ip': ip,
                    'name': name,
                    'templates': templates,
                    'maintenanceGroup': maintenanceGroup,
                    'proxy': proxy,
                    'hostid': hostid,
                    'interfaceid': interfaceid,
                }
            
            hostids = list(self.jsonHosts['hostids'].keys())

            # assembling self.jsonHosts['hosts'][%ip%]['items']
            items = self.return_items_by_hostid(hostids, output=[
                "name",
                "itemid",
                "hostid"
            ])
            for item in items:
                hostid = item['hostid']
                ip = self.jsonHosts['hostids'][hostid]

                self.jsonHosts['hosts'][ip]['items'][item['name']] = {
                    'name': item['name'],
                    'itemid': item['itemid']
                }

            # assembling self.jsonHosts['hosts'][%ip%]['triggers']
            triggers = self.return_triggers_by_hostid(list(hostids), select={
                'selectHosts': 'hostid'
            })
            for trigger in triggers:
                for host_ in trigger['hosts']:
                    if not host_['hostid'] in self.jsonHosts['hostids']:
                        continue
                    
                    hostid = host_['hostid']
                    ip = self.jsonHosts['hostids'][hostid]
                    host = self.jsonHosts['hosts'][ip]

                    description = trigger['description']
                    triggerid = trigger['triggerid']

                    host['triggers'][description] = {
                        'description': description,
                        'triggerid': triggerid,
                    }

            MAIN._katprint(f"""> Data successfully received\n > Duplicates detected: {len(self.duplicates)}\n > Hosts detected: {len(self.jsonHosts['hosts'])}\n""")

        else:
            MAIN._fatal_error(f"Server don't returns an answer with 'result' data. Taken data:\n\n{answer}")
            return


    def return_items_by_hostid(self, hostid, output = [
            "name",
            "itemid",
            ]):
        "returns items data for host with given hostid by input fields."
        query = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "hostids": hostid,
                "output": output,
            },
            "id": 1,
            "auth": self.authKey
        }
        answer = self.send_json_request(query)
        if not "result" in answer:
            MAIN._fatal_error(f"Server don't returns an answer with 'result' data of item. Taken data:\n\n{answer}")
            return

        return answer["result"] if (answer["result"] != None) and (len(answer["result"]) > 0) else []

        
    def return_triggers_by_hostid(self, hostid, select={}, output = [
            "description",
            "triggerid"
            ]):
        "returns triggers data for host with given hostid by input fields."
        query = {
            "jsonrpc": "2.0",
            "method": "trigger.get",
            "params": {
                "hostids": hostid,
                "output": output,
            },
            "id": 1,
            "auth": self.authKey
        }
        if select:
            for key in select:
                query['params'][key] = select[key]

        answer = self.send_json_request(query)
        if not "result" in answer:
            MAIN._fatal_error(f"Server don't returns an answer with 'result' data of trigger. Taken data:\n\n{answer}")
            return

        return answer["result"] if (answer["result"] != None) and (len(answer["result"]) > 0) else []


    def add_json_host(self,
            shopid: int,
            group: str,
            ip: str,
            name: str,
            templates = [],
            maintenanceGroup = "",
            proxy = "0",
            items = {},
            triggers = {},
            _fatal_error=True
        ):
        """Creates host at Zabbix by group(int or str), ip (str) and name(str)."""
        group = str(group)
        shopid = int(shopid)
        systemName = f"{ip}_{shopid}"

        query = {
            "jsonrpc": "2.0",
            "method": "host.create",
            "params": {
                "host": systemName,
                "interfaces": [
                    {
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": ip,
                        "dns": "",
                        "port": "10050"
                    }
                ],
                "groups": [
                    {
                        "groupid": group
                    }
                ],
                "name": name
            },
            "auth": self.authKey,
            "id": 1
        }
        if templates:
            templates = list(templates)
            query["params"]["templates"] = list()
            for templateid in templates:
                query["params"]["templates"].append(
                    {
                        "templateid": templateid,
                    }
                )
        if maintenanceGroup and not maintenanceGroup.isspace():
            maintenanceGroup = str(maintenanceGroup)
            query["params"]["groups"].append(
                {
                    "groupid": maintenanceGroup,
                }
            )
        if proxy and proxy != "0":
            query["params"]["proxy_hostid"] = proxy

        answer = self.send_json_request(query)
        try:
            hostid = answer["result"]["hostids"][0]
        except BaseException as error:
            text = f"Can't create host with params:\n\n Name: '{name}'\n IP: '{ip}'\n group: {group}\n templates: '{templates}'\n maintenanceGroup: '{maintenanceGroup}'\n proxy: '{proxy}'\n\n "\
                f"hostid = answer['result']['hostids'][0] error: {error}\n\n Answer from server: {answer}"
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False
        
        # get interfaceid:
        query = {
                   "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "hostids": hostid,
                        "selectInterfaces": ["interfaceid"],
                    },
                    "id": 1,
                    "auth": self.authKey
                }
        answer = self.send_json_request(query)
        try:
            interfaceid = answer["result"][0]["interfaces"][0]["interfaceid"]
        except BaseException as error:
            text = f"Can't get interfaceid after creatig host with params:\n\n Name: '{name}'\n IP: '{ip}'\n groupid: {group}\n templates: '{templates}'\n maintenanceGroup: '{maintenanceGroup}'\n proxy: '{proxy}'\n\n "\
                f"interfaceid = answer['result']['interfaces'][0]['interfaceid'] error: {error}\n\n Answer from server: {answer}"
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False


        # assembling data to self.jsonHosts['hostids']:
        self.jsonHosts['hostids'][hostid] = ip

        # assembling data to self.jsonHosts['shopids']:
        if not shopid in self.jsonHosts['shopids']:
            self.jsonHosts['shopids'][shopid] = dict()
        if not group in self.jsonHosts['shopids'][shopid]:
            self.jsonHosts['shopids'][shopid][group] = dict()
        self.jsonHosts['shopids'][shopid][group][hostid] = ip

        # assembling data to self.jsonHosts['hosts']:
        self.jsonHosts['hosts'][ip] = dict()
        self.jsonHosts['hosts'][ip]['host'] = dict()
        self.jsonHosts['hosts'][ip]['items'] = dict()
        self.jsonHosts['hosts'][ip]['triggers'] = dict()

        self.jsonHosts['hosts'][ip]['host'] = {
            'shopid': shopid,
            'sqlGroups': MAIN.GROUPS[group][0],
            'jsonGroup': group,
            'ip': ip,
            'name': name,
            'systemName': systemName,
            'templates': templates,
            'maintenanceGroup': maintenanceGroup,
            'proxy': proxy,
            'hostid': hostid,
            'interfaceid': interfaceid
        }

        # assembling data to self.jsonHosts['hosts']['%ip%']['items']:
        itemsCreated = {}
        for itemName in items:
            itemid = self.create_json_item(hostid, name, itemName, interfaceid, items[itemName])
            itemsCreated[itemName] = {
                'name': itemName,
                'itemid': itemid
            }
        self.jsonHosts['hosts'][ip]['items'] = itemsCreated

        # assembling data to self.jsonHosts['hosts']['%ip%']['triggers']:
        triggersCreated = {}
        for triggerName in triggers:            
            triggerid = self.create_json_trigger(
                hostid,
                systemName,
                triggerName,
                triggers[triggerName],
                interfaceid=interfaceid)
            triggersCreated[triggerName] = {
                'description': triggerName,
                'triggerid': triggerid
            }
        self.jsonHosts['hosts'][ip]['triggers'] = triggersCreated
        return hostid

    
    def create_json_item(self, hostid: str, hostName: str, itemName: str, interfaceid: str, item: dict):
        """Creates item with given structure."""
        # creating query
        try:
            hostid = str(hostid)
            interfaceid = str(interfaceid)
            hostName = str(hostName)

            query = {
                "jsonrpc": "2.0",
                "method": "item.create",
                "params": {
                    "delay": str(item['delay']),
                    "hostid": hostid,
                    "interfaceid": interfaceid,
                    "key_": str(item['key_']).replace(
                        "%hostid%", hostid).replace(
                        "%hostName%", hostName).replace(
                        "%interfaceid%", interfaceid),
                    "name": str(itemName),
                    "type": int(item['type']),
                    "url": str(item['url']).replace(
                        "%hostid%", hostid).replace(
                        "%hostName%", hostName).replace(
                        "%interfaceid%", interfaceid),
                    "value_type": int(item['value_type']),
                },
                "auth": self.authKey,
                "id": 1
            }
            # str optional params
            for param in [
                "delay",
                "hostid",
                "interfaceid",
                "key_",
                "name",
                "url",
                'description',
                'history',
                'http_proxy',
                'ipmi_sensor',
                'jmx_endpoint',
                'logtimefmt',
                'params',
                'password',
                'port',
                'posts',
                'privatekey',
                'publickey',
                'snmp_community',
                'snmp_oid',
                'snmpv3_authpassphrase',
                'snmpv3_contextname',
                'snmpv3_privpassphrase',
                'snmpv3_securityname',
                'ssl_cert_file',
                'ssl_key_file',
                'ssl_key_password',
                'status_codes',
                'timeout',
                'trapper_hosts',
                'trends',
                'units',
                'username',
                'valuemapid',
            ]:
                if param in item:
                    query['params'][param] = str(item[param]).replace(
                        "%hostid%", hostid).replace(
                        "%hostName%", hostName).replace(
                        "%interfaceid%", interfaceid)
            # int optional params
            for param in [
                "type",
                "value_type",
                'allow_traps',
                'authtype',
                'follow_redirects',
                'inventory_link',
                'master_itemid',
                'output_format',
                'post_type',
                'request_method',
                'retrieve_mode',
                'snmpv3_authprotocol',
                'snmpv3_privprotocol',
                'snmpv3_securitylevel',
                'status',
                'verify_host',
                'verify_peer',
            ]:
                if param in item:
                    query['params'][param] = int(item[param])
            # "applications" array param
            if "applications" in item:
                apps = []
                for app in item['applications']:
                    apps.append(str(app).replace(
                        "%hostid%", hostid).replace(
                        "%hostName%", hostName).replace(
                        "%interfaceid%", interfaceid))
                query['params']['applications'] = apps
            # "preprocessing" array param
            if "preprocessing" in item:
                preps = []
                for prep in item['preprocessing']:
                    preps.append(
                        {
                            'type': str(prep['type']),
                            'params': str(prep['params']).replace(
                                "%hostid%", hostid).replace(
                                "%hostName%", hostName).replace(
                                "%interfaceid%", interfaceid),
                        }
                    )
                query['params']['preprocessing'] = preps
            # "query_fields" array param
            if "query_fields" in item:
                qrs = []
                for qr in item['query_fields']:
                    key = qr.keys()[0]
                    qrs.append(
                        {
                            str(key): str(qr[key])
                        }
                    )
                query['params']['query_fields'] = qrs
        except BaseException as error:
            MAIN._fatal_error(f"Can't create query with given values for creating item for host with:\nhostid='{hostid}'\nhostName='{hostName}'"\
                f"\nitemName='{itemName}'\ninterfaceid='{interfaceid}'\n\nFATAL ERROR: {error}")
            return

        # send request to create
        answer = self.send_json_request(query)
        try:
            itemid = answer["result"]["itemids"][0]
        except BaseException as error:
            text = f"Can't create item after creatig host with query params:\n\n"
            for param in query['params']:
                text += "'{}': {}\n".format(
                    param,
                    f"{query['params'][param]}" if type(query['params'][param]) == int else f"'{query['params'][param]}'"
                )
            text +=" Error: {error}\n\n Answer from server: {answer}"
            MAIN._fatal_error(text)
            return
        else:
            return itemid

    
    def create_json_trigger(self, hostid: str, hostName: str, triggerName: str, trigger: dict, interfaceid=""):
        """Creates item with given structure."""
        # creating query
        try:
            hostid = str(hostid)
            hostName = str(hostName)
            interfaceid = str(interfaceid)

            query = {
                "jsonrpc": "2.0",
                "method": "trigger.create",
                "params": {
                    "description": str(triggerName),
                    "expression": str(trigger['expression']).replace(
                        "%hostid%", hostid).replace(
                        "%hostName%", hostName).replace(
                        "%interfaceid%", interfaceid),
                },
                "auth": self.authKey,
                "id": 1
            }
            # str optional params
            for param in [
                'comments',
                'url',
                'recovery_expression',
                'correlation_tag',
            ]:
                if param in trigger:
                    query['params'][param] = str(trigger[param]).replace(
                        "%hostid%", hostid).replace(
                        "%hostName%", hostName).replace(
                        "%interfaceid%", interfaceid)
            # int optional params
            for param in [
                'priority',
                'status',
                'type',
                'recovery_mode',
                'correlation_mode',
                'manual_close',
            ]:
                if param in trigger:
                    query['params'][param] = int(trigger[param])
            # "tags" array param
            if "tags" in trigger:
                tags = []
                for tag in trigger['tags']:
                    tags.append(
                        {
                            "tag": str(tag["tag"]),
                            "value": str(tag["value"]).replace(
                                "%hostid%", hostid).replace(
                                "%hostName%", hostName).replace(
                                "%interfaceid%", interfaceid)
                        }
                    )
                query['params']['tags'] = tags
        except BaseException as error:
            MAIN._fatal_error(f"Can't create query with given values for creating trigger for host with:\nhostid='{hostid}'"\
                f"\nhostName='{hostName}'\ntriggerName='{triggerName}'\ninterfaceid='{interfaceid}'\n\nFATAL ERROR: {error}")
            return

        # send request to create
        answer = self.send_json_request(query)
        try:
            triggerid = answer["result"]["triggerids"][0]
        except BaseException as error:
            text = f"Can't create trigger after creatig item with query params:\n\n"
            for param in query['params']:
                text += "'{}': {}\n".format(
                    param,
                    f"{query['params'][param]}" if type(query['params'][param]) == int else f"'{query['params'][param]}'"
                )
            text += f"\n Error: {error}\n\n Answer from server: {answer}"
            MAIN._fatal_error(text)
            return
        else:
            return triggerid        


    def delete_json_hosts(self, list_, _fatal_error=True):
        """Delete hosts from Zabbix by ID-list."""
        if len(list_) == 0:
            return True

        query = {
            "jsonrpc": "2.0",
            "method": "host.delete",
            "params": list_,
            "auth": self.authKey,
            "id": 1
        }
        answer = self.send_json_request(query)

        if "result" not in answer:
            text = f"Can't delete {len(list_)} host(s)\n answer['result'] error: {answer}"
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False
        
        if "hostids" not in answer["result"]:
            text = f"Can't delete {len(list_)} host(s)\n answer['result']['hostids'] error: {answer}"
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False

        if answer["result"]["hostids"] != list_:
            text = f"Can't delete {len(list_)} host(s)\n answer['result']['hostids'] == list_ error: {answer}"
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False
        return True

    
    def clear_trigger_dependencies(self, triggerids):
        """Clear all dependencies for each trigger in given list."""
        query = {
            "jsonrpc": "2.0",
            "method": "trigger.deleteDependencies",
            "params": [],
            "auth": self.authKey,
            "id": 1
        }
        if type(triggerids) == str:
            query['params'].append({'triggerid': triggerids})
        else:
            for triggerid in triggerids:
                query['params'].append({'triggerid': triggerid})
        answer = self.send_json_request(query)
        try:
            triggerids = answer["result"]["triggerids"]
        except BaseException as error:
            text = f"Can't clear all dependencies of triggers with query params:\n\n"
            for param in query['params']:
                text += "'{}': {}\n".format(
                    param,
                    f"{query['params'][param]}" if type(query['params'][param]) == int else f"'{query['params'][param]}'"
                )
            text += f"\n Error: {error}\n\n Answer from server: {answer}"
            MAIN._fatal_error(text)
            return

    
    def create_trigger_dependencies(self, dependencies):
        """Create dependencies for trigger(s)."""
        query = {
            "jsonrpc": "2.0",
            "method": "trigger.adddependencies",
            "params": dependencies,
            "auth": self.authKey,
            "id": 1
        }
        answer = self.send_json_request(query)
        try:
            triggerids = answer["result"]["triggerids"]
        except BaseException as error:
            text = f"Can't create dependencies of triggers with query params:\n\n"
            for param in query['params']:
                if type(query['params']) == dict:
                    text += "'{}': {}\n".format(
                        param,
                        f"{query['params'][param]}" if type(query['params'][param]) == int else f"'{query['params'][param]}'"
                    )
                elif type(query['params']) == list:
                    text += "'{}'\n".format(param)
                else:
                    text += "'{}'\n".format(param)
            text += f"\n Error: {error}\n\n Answer from server: {answer}"
            MAIN._fatal_error(text)
            return


    def send_json_request(self, query, server="DEFAULT", headers="DEFAULT", _fatal_error=True):
        """Send post request to the server in json format.

        params:
            query - json-query,
            server = 'DEFAULT' (default - self.JSONConfig["server"])
            headers = 'DEFAULT' (default - self.JSONConfig["headers"])
            _fatal_error = True (True - if fatal, False - return False if error)

        returns json-answer from server if success, and False if _fatal_error = False (else - close program)

        """
        if server == "DEFAULT":
            server = self.JSONConfig["server"]
        if headers == "DEFAULT":
            headers = self.JSONConfig["headers"]

        try:
            ans = requests.post(server, json=query, headers=headers)
        except BaseException as error:
            text = f"""Can't send post-query to server '{server}'\n requests.post error: '{error}'.\nQuery params:\n\n"""
            for param in query['params']:
                text += "'{}': {}\n".format(
                    param,
                    f"{query['params'][param]}" if type(query['params'][param]) == int else f"'{query['params'][param]}'"
                )

            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False
        try:
            ans = ans.json()
        except ValueError as error:
            text = f"""Can't decode post answer as json\n ans.json error: '{error}'.\nQuery params:\n\n"""
            for param in query['params']:
                text += "'{}': {}\n".format(
                    param,
                    f"{query['params'][param]}" if type(query['params'][param]) == int else f"'{query['params'][param]}'"
                )

            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False

        return(ans)