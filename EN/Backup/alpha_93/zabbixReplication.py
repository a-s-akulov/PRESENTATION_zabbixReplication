try:
    import os
    import sys
    import requests
    import pyodbc
    from datetime import datetime
except BaseException as error:
    input(f"\n An error has occurred when the program tried to import some module. Error:\n\n{error}\n\n Press ENTER to exit")
    exit()

try:
    import my_modules
except BaseException as error:
    input(f"\n An error has occurred when the program tried to import some module from 'my_modules' directory. Error:\n\n{error}\n\n Press ENTER to exit")
    sys.exit(0)

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




if __name__ == "__main__":
    MAIN = ZabbixReplication()
    SQL = my_modules.FncsSQL(MAIN, pyodbc)
    JSON = my_modules.FncsJSON(MAIN, requests)
    MAIN.auto_replication()