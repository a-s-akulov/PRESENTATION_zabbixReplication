try:
    import requests
    import os
    import pyperclip
except BaseException as error:
    input(f"\n An error has occurred when the program tried to import some module. Error:\n\n{error}\n\n Press ENTER to exit")
    exit()

class ShowAllItems():
    """Print all items from Zabbix server with itemid for each."""
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

        self.get_itemId()


    def get_itemId(self):
        self.HOST = input("Enter hostId to show items: ")
        try: 
            int(self.HOST)
        except:
            print("Uncorrect hostId! hostId - is a number (examle: 25979)\n")
            self.get_itemId()
            return
        else:
            print("\n")

        
    def showList(self):
        """Main fnc - Print all items from Zabbix server with itemid for each."""
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
                "method": "item.get",
                "params": {
                    "hostids": self.HOST,
                    "output": [
                        "name",
                        'description',
                        "key_",
                        "url",
                        "type",
                        "value_type",
                        "delay",
                        "hostid",
                        "interfaceid",
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
                        'units',
                        'username',
                        'valuemapid',                 
                        'allow_traps',
                        'authtype',
                        'follow_redirects',
                        'history',
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
                        'trends',
                        'verify_host',
                        'verify_peer',
                    ],
                    "selectApplications": ["applicationid"],
                    "selectPreprocessing": ["type", "params"]
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

            print(f" List of items at Zabbix server '{self.JSONConfig['server']}':\n")
            ans.sort(key=lambda x: int(x["itemid"]))
            str_ = ""
            for x in ans:
                str_ += "{"
                for x2 in x:
                    if x2 == "applications":
                        str_ += f"\n\n    '{x2}': ["
                        for app in x[x2]:
                            str_ += \
                                f"\n        '{app['applicationid']}',"
                        str_ += "\n    ],\n"

                    elif x2 == "preprocessing":
                        str_ += f"\n\n    '{x2}': ["
                        for prep in x[x2]:
                            str_ += \
                                f'\n        {{' + \
                                f'\n            "type": "{prep["type"]}",' + \
                                f'\n            "params": r"{prep["params"]}"' + \
                                f'\n        }},'
                        str_ += '\n    ],\n'
                    
                    elif x2 == "query_fields":
                        str_ += f"\n\n    '{x2}': ["
                        for qf in x[x2]:
                            for key in qf.keys():
                                str_ += \
                                    f'\n        {{' + \
                                    f'\n            "{key}": r"{qf["key"]}",' + \
                                    f'\n        }},'
                        str_ += '\n    ],\n'
                    
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
    MAIN = ShowAllItems()
    MAIN.showList()