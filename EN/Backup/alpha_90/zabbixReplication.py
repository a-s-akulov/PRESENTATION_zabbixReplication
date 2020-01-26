import os
import sys
import requests
import pyodbc
from datetime import datetime

# NOTE:

# Роутер (IPSec)= 15
# Камера, камера(кабинет), счетчики(камера), иногда еще и призма = 19
# WAN1 = 16
# WAN2 = 17
# (Счетчики (BATKOM), Broadcast, VOIP, WI_FI, Справка, терминал (банк)) - по идее не должно быть, KKT (в основном они) = 34 - тут фарш!!

# FOR TESTS:
# JSONConfig = {
#             "server": "http://192.168.3.80/zabbix/api_jsonrpc.php",
#             "login": "Admin",
#             "password": "zabbix",
#             "headers": {"Content-Type": "application/json-rpc"},
#             }; \
# query = {
#                    "jsonrpc": "2.0",
#                     "method": "user.login",
#                     "params": {
#                         "user": JSONConfig["login"],
#                         "password": JSONConfig["password"]
#                     },
#                     "id": 0,
#                     "auth": None
#                 }; \
# ans = requests.post(JSONConfig["server"], json=query, headers=JSONConfig["headers"]).json(); \
# jid = ans["result"]
# for s in ans["result"]:
#     print(s)

# name = Shop + GroupName + host

class ZabbixReplication():
    """Replication zabbix server with other database.

    Autor: akulov.a
    Organization website: www.chitai-gorod.du

    def autoReplication - start automaticaly replication

    """
    def __init__(self):
        self.logfileName = ""
        self.logging = False

        # Groups: ZabbixGroup = WorkspaceGroups
        self.GROUPS = {
            '15': [8], # IPSec = [Роутер]
            '19': [6, 19, 16], # Камеры = [Камера, Камера (кабинет), Счетчики]
            '16': [14], # WAN1 = WAN1
            '17': [21], # WAN2 = WAN2
            '34': [20], # В основном - ККТ
        }



    # START PROGRAM
    def auto_replication(self):
        """Automaticaly data replicate zabbix server with other database."""
        print(f"Autor: akulov.a\nProgram is entended for data replication from SQL server to Zabbix\n\n\n")
        self.log_init()
        SQL.get_sql_data()
        JSON.get_json_data()

        # Create an list of hosts for delete
        self.get_list_delete()

        # Delete hosts from Zabbix (exclude duplicates)
        if len(self.deleteHosts) != 0:
            self._katprint(">>> Deleting uncorrect hosts from Zabbix (exclude duplicates)...")
            list_ = [JSON.jsonHosts[s][0] for s in self.deleteHosts]

            # DELETING HOSTS FROM ZABBIX!!!!
            JSON.delete_json_hosts(list_)
            for s in self.deleteHosts:
                del(JSON.jsonHosts[s])
            self._katprint("> Uncorrect hosts successfully deleted\n")
        else:
            self._katprint(">>> No uncorrect hosts detected (exclude duplicates)\n")

        # Delete duplicate hosts
        if len(JSON.duplicates) != 0:
            self._katprint(">>> Deleting duplicate hosts from Zabbix...")

            # DELETING HOSTS FROM ZABBIX!!!!
            JSON.delete_json_hosts(JSON.duplicates)

            ips = set()
            for s in JSON.jsonHosts:
                host = JSON.jsonHosts[s]
                hostid = host[0]
                if (hostid in JSON.duplicates):
                    ips.add(s)

            for s in ips:
                del(JSON.jsonHosts[s])

            self._katprint("> Duplicate hosts successfully deleted\n")
        else:
            self._katprint(">>> No duplicate hosts detected\n")


        # ADD TO ZABBIX
        self._katprint(">>> Adding hosts from SQL to Zabbix...")
        availableGrps = []
        added = 0
        for x in self.GROUPS:
            availableGrps.extend(self.GROUPS[x])

        for s in SQL.sqlHosts:
            if s in JSON.jsonHosts:
                continue

            sqlData = SQL.sqlHosts[s]
            sqlShopid = sqlData[0]
            sqlGroup = sqlData[1]
            sqlName = f"{SQL.sqlShops[sqlShopid]} - {SQL.sqlHostTypes[sqlGroup]} - {s}"

            if sqlGroup not in availableGrps:
                continue

            jsonGroup = self.find_group_json(sqlGroup)

            # ADD HOST TO ZABBIX!!!
            JSON.add_json_host(jsonGroup, s, sqlName)
            self._katprint(f"> Host added. IP: '{s}', Group: {jsonGroup}, Name: '{sqlName}'")
            added += 1
        self._katprint(f"\n > Operation succesfully completed!\n > Added {added} hosts.\n")

        # FINALLY ALL OPERATIONS DONE, GO SLEEP
        self._katprint("\n\n===> Replication successfully completed, system shutdown.")
        input()
    

    # MAIN FNCS
    def get_list_delete(self):
        """Check if data from Zabbix is correct.

        Crates list 'self.deleteHosts' of uncorrect hosts

        """
        self._katprint(">>> Calculating list of hosts for delete from Zabbix...")
        self.deleteHosts = list()
        for s in JSON.jsonHosts:
            jsonData = JSON.jsonHosts[s]
            jsonHostid = jsonData[0]
            jsonGroup = jsonData[1]
            jsonName = jsonData[2]

            if s not in SQL.sqlHosts:
                self.deleteHosts.append(s)
                continue
            
            sqlData = SQL.sqlHosts[s]
            sqlShopid = sqlData[0]
            sqlGroup = sqlData[1]
            sqlName = f"{SQL.sqlShops[sqlShopid]} - {SQL.sqlHostTypes[sqlGroup]} - {s}"

            # Duplicates are deletes after self.deleteHosts list - this condition is for eliminating errors
            if jsonHostid in JSON.duplicates:
                continue
            
            if jsonGroup not in self.GROUPS:
                self._fatal_error(f"Can't calculate delete list\n jsonGroup not in self.GROUPS!\n JSON data = '{s}': {jsonData}")
                return

            if sqlGroup not in self.GROUPS[jsonGroup]:
                self.deleteHosts.append(s)
                continue

            if jsonName != sqlName:
                self.deleteHosts.append(s)
                continue
        self._katprint(f"> Delete list successfully calculated\n > Hosts for delete count (exclude duplicates): {len(self.deleteHosts)}\n")
    
    
    def find_group_json(self, sqlGroup):
        """Returns jsonGroup from self.GROUPS by one of sqlGroup."""
        jsonGroup = -1
        for idx, x in enumerate(self.GROUPS.values()):
            if sqlGroup in x:
                jsonGroup = list(self.GROUPS.keys())[idx]
                break
        return jsonGroup



    # OTHER FNCS
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
        self.logfileName = f"\\{time.replace(':', '_' )}.log"
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
                file_ = open(file_name, "a")
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
                file_ = open(file_name, "w")
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
        text = f"[ERROR] {text}"
        if self.logging:
            self._katprint(text)
        else:
            print(text)

        print() # KATTEMP
        input() # KATTEMP
        sys.exit(0)





class FncsJSON():
    """JSON module."""
    def __init__(self):
        """Params initialization."""
        self.jsonHosts = {}
        self.duplicates = []
        self.authKey = -1

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



class FncsSQL():
    """SQL module."""
    def __init__(self):
        self.sqlHosts = {}
        self.sqlShops = {}
        self.sqlHostTypes = {}

        self.SQLConfig = {
            "driver": r"{SQL Server}",
            "server": r"mailserver\newbooksql",
            "database": "ServiceDesk",
            "UID": "",
            "password": "",
            "Trusted_Connection": "yes",
            }


    def get_sql_data(self):
        """Returns dict of data from SQL server."""
        MAIN._katprint(f">>> Connecting to SQL server...")
        # CONNECT.
        try:
            conn = pyodbc.connect( f'Driver={self.SQLConfig["driver"]}; Server={self.SQLConfig["server"]}; Database={self.SQLConfig["database"]};' \
                f'UID={self.SQLConfig["UID"]}; PWD={self.SQLConfig["password"]}; Trusted_Connection={self.SQLConfig["Trusted_Connection"]};')
        except pyodbc.OperationalError as error:
            MAIN._fatal_error(f"""Can't connect with '{self.SQLConfig['server']}'.\n pyodbc.connect error: '{error}'.""")
            return
        except pyodbc.InterfaceError as error:
            MAIN._fatal_error(f"""Can't connect with '{self.SQLConfig['server']}'.\n pyodbc.connect error: '{error}'.""")
            return
        except pyodbc.ProgrammingError as error:
            MAIN._fatal_error(f"""Can't connect with '{self.SQLConfig['server']}'.\n pyodbc.connect error: '{error}'.""")
            return
        else:
            MAIN._katprint(f"> Successfully connected with '{self.SQLConfig['server']}'\n")
        
        try:
            cur = conn.cursor()
        except pyodbc.ProgrammingError as error:
            MAIN._fatal_error(f"""Can't create cursor at server: '{self.SQLConfig['server']}' and database: '{self.SQLConfig['database']}'.\n conn.cursor error: '{error}'.""")
            return

        self.sqlHosts = {}
        self.sqlShops = {}
        self.sqlHostTypes = {}
        MAIN._katprint(f">>> Starting to execute SQL requests...")

        # SHOPS
        query = "SELECT PT_ID, PT_FULLNAME FROM dbo.PARTNERS where TP_ID != 10"
        self.send_sql_request(cur, query, self.sqlShops, 2)

        # HOSTS
        cursor = object()
        query = "SELECT IP_ADRESS, PT_ID, HOST_TYPE FROM dbo.IPADRESES"
        self.send_sql_request(cur, query, cursor, 4)
        while True:
            try:
                row = cur.fetchone()
            except pyodbc.ProgrammingError as error:
                text = f"Can't execute query '{query}'.\n cur.fetchone error: '{error}'."
                MAIN._fatal_error(text)
                return
            if not row:
                break
            if row[0] in self.sqlHosts:
                MAIN._fatal_error("Duplicate IP-address detected! Use workspace_findDuplicateIp.exe at root of this program to fix it")
                return

            if row[1] in self.sqlShops:
                self.sqlHosts[row[0].strip()] = row[1:]

        # hostTypes
        query = "SELECT * FROM dbo.HOSTTYPES"
        self.send_sql_request(cur, query, self.sqlHostTypes, 2)

        MAIN._katprint(f"> All requests successfully completed")
        try:
            conn.close()
        except pyodbc.ProgrammingError as error:
            MAIN._katprint(f" Can't close connection with '{self.SQLConfig['server']}'.\n conn.close error: '{error}'.\n\n")
        else:
            MAIN._katprint(f"> Connection with '{self.SQLConfig['server']}' successfully closed\n")


    def send_sql_request(self, cur, query, variable, mode, _fatal_error=True):
        """Send request to SQL server and returns getted data to 'variable'.
        
        cur = cursor at server, getted with conn.cursor()
        query = SQL query. example: 'SELECT * from dbo.MyTable WHERE someColumn = 1'
        variable = variable to return the answer
        mode = format of reterned answer:
                        0 - [(all elements)]
                        1 - [(element0)[0], (element1)[0], etc...]
                        2 - {element0[0]: element0[1], element1[0]: element1[1], etc...}
                        3 - {element0[0]: element0[1:], element1[0]: element1[1:], etc...}
                        4 - object, prepared for .fetchone
        _fatal_error = is any error fataly for program?
                        True - print an error, wait for press Enter and close the program
                        False - print an error and just returns False

        If operatin successfull - return True
        
        """
        try:
            cur.execute(query)
        except pyodbc.ProgrammingError as error:
            text = f"Can't execute query '{query}'.\n cur.execute error: '{error}'."
            if _fatal_error:
                MAIN._fatal_error(text)
            else:
                MAIN._katprint(f"[SQL] {text}'\n")
            return False

        else:
            # If we need only cursor with executed query, wich ready for .fetchone (mode 4)
            if mode == 4:
                variable = cur
                return True

            # Other modes
            while True:
                try:
                    row = cur.fetchone()
                except pyodbc.ProgrammingError as error:
                    text = f"Can't execute query '{query}'.\n cur.fetchone error: '{error}'."
                    if _fatal_error:
                        MAIN._fatal_error(text)
                    else:
                        MAIN._katprint(f"[SQL] {text}")
                    return False

                if not row:
                    break

                if mode == 0:
                    variable.append(row)
                elif mode == 1:
                    variable.append(row[0])
                elif mode == 2:
                    variable[row[0]] = row[1]
                elif mode == 3:
                    variable[row[0]] = row[1:]

            return True




if __name__ == "__main__":
    MAIN = ZabbixReplication()
    JSON = FncsJSON()
    SQL = FncsSQL()
    MAIN.auto_replication()