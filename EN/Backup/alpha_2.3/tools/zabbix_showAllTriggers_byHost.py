try:
    import requests
    import os
    import pyperclip
except BaseException as error:
    input(f"\n An error has occurred when the program tried to import some module. Error:\n\n{error}\n\n Press ENTER to exit")
    exit()

class ShowAllTriggers():
    """Print all triggers from Zabbix server with triggerid for each."""
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

        self.get_triggerId()


    def get_triggerId(self):
        self.HOST = input("Enter hostId to show triggers: ")
        try: 
            int(self.HOST)
        except:
            print("Uncorrect hostId! hostId - is a number (examle: 25979)\n")
            self.get_triggerId()
            return
        else:
            print("\n")

        
    def showList(self):
        """Main fnc - Print all triggers from Zabbix server with triggerid for each."""
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
                "method": "trigger.get",
                "params": {
                    "hostids": self.HOST,
                    "output": [
                        'triggerid',
                        'description',
                        'expression',
                        'comments',
                        'url',
                        'recovery_expression',
                        'correlation_tag',
                        'priority',
                        'status',
                        'type',
                        'recovery_mode',
                        'correlation_mode',
                        'manual_close',
                    ],
                    "selectDependencies": ["triggerid", "description"],
                    "selectTags": "extend",
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

            print(f" List of triggers at Zabbix server '{self.JSONConfig['server']}':\n")
            ans.sort(key=lambda x: int(x["triggerid"]))
            str_ = ""
            for x in ans:
                str_ += "{"
                for x2 in x:
                    if x2 == "tags":
                        str_ += f"\n\n    '{x2}': ["
                        for tag in x[x2]:
                            str_ += \
                                f'\n        {{' + \
                                f'\n            "tag": "{tag["tag"]}",' + \
                                f'\n            "value": r"{tag["value"]}"' + \
                                f'\n        }},'
                        str_ += "\n    ],\n"

                    elif x2 == "dependencies":
                        str_ += f"\n\n    '{x2}': ["
                        for dep in x[x2]:
                            str_ += \
                                f'\n        {{' + \
                                f'\n            "triggerid": "{dep["triggerid"]}",    # CAUTION! UNIQUE PARAM!' + \
                                f'\n            "description": r"{dep["description"]}"' + \
                                f'\n        }},'
                        str_ += '\n    ],\n'
                    
                    elif x2 in ('expression','triggerid'):
                        str_ += f"\n    '{x2}': r'{x[x2]}',    # CAUTION! UNIQUE PARAM!"

                    else:
                        str_ += f"\n    '{x2}': r'{x[x2]}',"
                str_ += "\n},"
                str_ += "\n\n\n"

            print(str_)
            copy = input("Copy data to clipboard? (y = yes, other = no): ")
            if copy == "y":
                pyperclip.copy(str_.strip())
                print("\nData copied to clipboard\n")
            else:
                print("\nCopying canceled\n")
            input(f"\n Work is done. Press ENTER to exit")

        except BaseException as error:
            input(f"\n An error has occurred when program works. Error:\n\n{error}\n\n Press ENTER to exit")



if __name__ == "__main__":
    MAIN = ShowAllTriggers()
    MAIN.showList()