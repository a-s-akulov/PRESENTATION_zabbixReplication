class FncsJSON():
    """JSON module."""
    def __init__(self, parent, jsonModule):
        """Params initialization."""
        global MAIN
        global requests
        MAIN = parent
        requests = jsonModule

        self.jsonHosts = {}
        self.duplicates = []
        self.authKey = -1

        # ZABBIX CONFIG PARAMS
        self.JSONConfig = {
            "server": "http://192.168.3.80/zabbix/api_jsonrpc.php",
            "login": "Admin",
            "password": "zabbix",
            "headers": {"Content-Type": "application/json-rpc"},
            }



    def get_json_data(self):
        """Get hosts list from zabbix server to self.jsonHosts"""
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
        query = {
                   "jsonrpc": "2.0",
                    "method": "host.get",
                    "params": {
                        "output": ["host", "name"],
                        "selectInterfaces": ["ip"],
                        "selectGroups": []
                    },
                    "id": 1,
                    "auth": self.authKey
                }
        answer = self.send_json_request(query)
        if "result" in answer:
            for x in answer["result"]:
                ip = x["interfaces"][0]["ip"]
                hostid = x["hostid"]
                group = x["groups"][0]["groupid"]
                name = x["name"]

                # if already exists - add to duplicate list this and first and continue to next step of FOR
                if ip in self.jsonHosts:
                    self.duplicates.append(hostid)
                    first = self.jsonHosts[ip]
                    if first[0] not in self.duplicates:
                        self.duplicates.append(first[0])
                    continue

                self.jsonHosts[ip] = [hostid, group, name]
            MAIN._katprint(f"""> Data successfully received\n > Duplicates detected: {len(self.duplicates)}\n > Hosts detected: {len(self.jsonHosts)}\n""")

        else:
            MAIN._fatal_error(f"Server don't returns an answer with 'result' data. Taken data:\n\n{answer}")
            return


    def add_json_host(self, group, ip, name, _fatal_error=True):
        """Creates host at Zabbix by group(int or str), ip (str) and name(str)."""
        query = {
            "jsonrpc": "2.0",
            "method": "host.create",
            "params": {
                "host": ip,
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
                        "groupid": str(group)
                    }
                ],
                "name": name
            },
            "auth": self.authKey,
            "id": 1
        }

        answer = self.send_json_request(query)
        try:
            hostid = answer["result"]["hostids"][0]
        except BaseException as error:
            text = f"Can't create host with params:\n\n Name: '{name}'\n IP: '{ip}'\n groupid: {group}\n\n "\
                f"hostid = answer['result']['hostids'][0] error: {error}\n\n Fnswer from server: {answer}"
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False
        
        self.jsonHosts[ip] = [hostid, group, name]


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
            text = f"""Can't send post-query to server '{server}'\n requests.post error: '{error}'."""
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False
        try:
            ans = ans.json()
        except ValueError as error:
            text = f"""Can't decode post answer as json\n ans.json error: '{error}'."""
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[JSON] {text}'\n")
            return False

        return(ans)