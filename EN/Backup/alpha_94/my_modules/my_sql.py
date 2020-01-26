class FncsSQL():
    """SQL module."""
    def __init__(self, parent, sqlModule):
        """Params initialization."""
        global MAIN
        global pyodbc
        MAIN = parent
        pyodbc = sqlModule

        self.sqlHosts = {}
        self.sqlShops = {}
        self.sqlHostTypes = {}

        # SQL CONFIG PARAMS
        self.SQLConfig = {
            "driver": r"{SQL Server}",
            "server": r"mailserver\newbooksql",
            "database": "ServiceDesk",
            "UID": "",
            "password": "",
            "Trusted_Connection": "yes", # USE WINDOWS NT AUTHENTIFICATION
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
                MAIN._fatal_error(r"Duplicate IP-address detected! Use workspace_findDuplicateIp.exe at tools\ directory to fix it")
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