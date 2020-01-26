import pyodbc
import sys

class WorkspaceFindRepetitions():
    """Check to match of IP-adresses in Workspace database."""
    def start(self):
        """Start of the rogram."""
        repetitions = set()
        all_ip = set()

        # CONNECT.
        print(f" >>> Connecting to 'mailserver\\newbooksql' SQL server...")
        try:
            conn = pyodbc.connect(r'Driver={SQL Server};Server=mailserver\newbooksql;Database=ServiceDesk;Trusted_Connection=yes;')
        except pyodbc.OperationalError as error:
            self._fatal_error(f"""Can't connect with 'mailserver\\newbooksql'.\n pyodbc.connect error: '{error}'.""")
            return
        except pyodbc.InterfaceError as error:
            self._fatal_error(f"""Can't connect with 'mailserver\\newbooksql'.\n pyodbc.connect error: '{error}'.""")
            return
        except pyodbc.ProgrammingError as error:
            self._fatal_error(f"""Can't connect with 'mailserver\\newbooksql'.\n pyodbc.connect error: '{error}'.""")
            return
        else:
            print(f" > Successfully connected with 'mailserver\\newbooksql'\n")
        
        try:
            cur = conn.cursor()
        except pyodbc.ProgrammingError as error:
            self._fatal_error(f"""Can't create cursor at server: 'mailserver\\newbooksql' and database: 'ServiceDesk'.\n conn.cursor error: '{error}'.""")
            return

        # GET DATA.
        print(" >>> Getting data from SQL server...")
        query = "SELECT IP_ADRESS FROM dbo.IPADRESES"
        try:
            cur.execute(query)
        except pyodbc.ProgrammingError as error:
            self._fatal_error(f"Can't execute query '{query}'.\n cur.execute error: '{error}'.")

        while True:
            try:
                row = cur.fetchone()
            except pyodbc.ProgrammingError as error:
                self._fatal_error(f"Can't execute query '{query}'.\n cur.fetchone error: '{error}'.")

            if not row:
                break
            if row[0] in all_ip:
                repetitions.add(row[0])
            else:
                all_ip.add(row[0])
        print(" > Successfully collected data from server\n\n")

        # CHECK FOR MATCHES 
        if len(repetitions) == 0:
            try:
                conn.close()
            except:
                pass
            print(" Duplicate IP-addresses not found!\n Press Enter to exit.")
            input()
            sys.exit(0)
        else:
            print(" >>> Start working:")

        # START WORKING.
        for idx, s in enumerate(repetitions):
            print()
            query = f"SELECT IP_ADRESS, PT_ID FROM dbo.IPADRESES where IP_ADRESS = '{s}'"
            targets = []

            try:
                cur.execute(query)
            except pyodbc.ProgrammingError as error:
                self._fatal_error(f"Can't execute query '{query}'.\n cur.execute error: '{error}'.")

            while True:
                try:
                    row = cur.fetchone()
                except pyodbc.ProgrammingError as error:
                    self._fatal_error(f"Can't execute query '{query}'.\n cur.fetchone error: '{error}'.")
                if not row:
                    break
                targets.append(row)

            for idx2, x in enumerate(targets):
                print(f"    {idx2 + 1}. IP: {x[0]} || ShopId: {x[1]}")
            print(f" > Shown: {idx + 1} from {len(repetitions)}\n")
            input("Press Enter to continue.")


        try:
            conn.close()
        except:
            pass
        print(f"\n\n====> Work is finished! Press Enter to exit. <====")
        input()

    def _fatal_error(self, text):
        """Print an error and exit."""
        print(f" [ERROR] {text}\n")
        input()
        sys.exit(0)


if __name__ == "__main__":
    main = WorkspaceFindRepetitions()
    main.start()