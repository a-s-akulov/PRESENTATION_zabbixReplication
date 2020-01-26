class ShowAllGroups():
    """Print all groups from Zabbix server with groupid for each."""
    def __init__(self):
        """Params initialization."""
        self.authKey = -1

        # ZABBIX CONFIG PARAMS
        self.JSONConfig = {
            "server": "http://192.168.3.80/zabbix/api_jsonrpc.php",
            "login": "Admin",
            "password": "zabbix",
            "headers": {"Content-Type": "application/json-rpc"},
            }

        
    def showList(self):
        """Main fnc - Print all groups from Zabbix server with groupid for each."""
        try:
            import requests
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
                "method": "hostgroup.get",
                "params": {
                    "output": ["groupid", "name"]
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

            print(f" List of groups at Zabbix server '{self.JSONConfig['server']}':\n")
            ans.sort(key=lambda x: int(x["groupid"]))
            for x in ans:
                print(str(x)[1:-1])
            input(f"\n Work is done. Press ENTER to exit")

        except BaseException as error:
            input(f"\n An error has occurred when program works. Error:\n\n{error}\n\n Press ENTER to exit")



if __name__ == "__main__":
    MAIN = ShowAllGroups()
    MAIN.showList()