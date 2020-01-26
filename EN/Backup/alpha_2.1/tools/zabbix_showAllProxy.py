try:
    import requests
    import os
except BaseException as error:
    input(f"\n An error has occurred when the program tried to import some module. Error:\n\n{error}\n\n Press ENTER to exit")
    exit()

class ShowAllProxy():
    """Print all proxy from Zabbix server with proxyid for each."""
    def __init__(self):
        """Params initialization."""
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
                print(f"""Can't use user environment variable 'MyZabbix_{s}' - returned '{str(self.JSONConfig[s])}'\n\n""")
                input(" Press ENTER to exit")
                exit()

        
    def showList(self):
        """Main fnc - Print all proxy from Zabbix server with proxyid for each."""
        try:
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

            ans = requests.post(self.JSONConfig["server"], json=query, headers=self.JSONConfig["headers"]).json()
            try:
                authId = ans["result"]
            except:
                input(f"\n An error has occurred when the program tried to get result from server. Error answer:\n\n{ans['error']}\n\n Press ENTER to exit")
                return

            query = {
                "jsonrpc": "2.0",
                "method": "proxy.get",
                "params": {
                    "output": ["proxyid", "host"]
                },
                "auth": authId,
                "id": 1
            }

            ans = requests.post(self.JSONConfig["server"], json=query, headers=self.JSONConfig["headers"]).json()
            try:
                ans = ans["result"]
            except:
                input(f"\n An error has occurred when the program tried to get result from server. Error answer:\n\n{ans['error']}\n\n Press ENTER to exit")
                return

            print(f" List of proxy at Zabbix server '{self.JSONConfig['server']}':\n")
            ans.sort(key=lambda x: int(x["proxyid"]))
            for x in ans:
                print(str(x)[1:-1])
            input(f"\n Work is done. Press ENTER to exit")

        except BaseException as error:
            input(f"\n An error has occurred when program works. Error:\n\n{error}\n\n Press ENTER to exit")



if __name__ == "__main__":
    MAIN = ShowAllProxy()
    MAIN.showList()