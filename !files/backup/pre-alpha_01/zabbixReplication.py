import os
import sys
import requests
import time
import pyodbc
from datetime import datetime

class ZabbixReplication():
    """Replication zabbix server with other database.

    Autor: akulov.a
    Organization website: www.chitai-gorod.du

    def autoReplication - start automaticaly replication

    """
    def __init__(self):
        self.logfileName = ""
        self.logging = False

        self.zabbixConfig = {
            "server": "http://192.168.3.80/zabbix/zabbix/api_jsonrpc.php",
            "login": "Zabbix",
            "password": "admin",
            }


        self.zabbixData = {
            "hosts": [],
        }

    # START PROGRAM
    def auto_replication(self):
        """Automaticaly data replicate zabbix server with other database."""
        print(f"Autor: akulov.a\nProgram is entended for data replication from SQL server to Zabbix\n\n\n")
        self.log_init()
        SQL.get_sql_data()

        input()



    # MAIN FNCS
    





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

        print()
        input()
        sys.exit(0)





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
                self.sqlHosts[row[0]] = row[1:]

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
    SQL = FncsSQL()
    MAIN.auto_replication()