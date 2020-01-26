# PRESENTATION_zabbixReplication

This is my 7th development on Python.

This time it is a program for replicating data between an SQL database and a Zabbix monitoring service.

The fact is that my company has quite a few stores, each of which has cameras, computers, and
routers whose availability must be monitored. To do this, they are all transferred to Zabbix, which, in the event of any accident
informs technical support that a particular host is not available.

But the problem is that there are more shops, and some hosts that have been around for a long time, from time to time
change their IP ardes, or even delete them. It turns out that in each such case you have to climb
in Zabbix and with your hands either add or delete these hosts, which is very inconvenient.

It is for solving this problem that my program is intended.

As with the previous ones, all confidential data from the screenshots were cut out, and I also note that
she receives all relevant information from a database.
For the program to work with your system, you will have to take care of the file EN\Source\my_modules\my_sql.py


The program allows you to quite variably configure replication parameters, but there are still limitations.

For example, it proceeds from the fact that only 2 groups can be added to the added host: the “service” group and the group,
which shows what type of host (for example, the "camera" group).

Configuration is allowed (for each of the Zabbix groups separately):

- Snapping to one or more templates
- Binding a specific group in Zabbix to one or more host types from an SQL database
- Connecting a proxy server for monitoring
- Linking to service groups by time zones (for example, if it's already night somewhere and the store closes,
then Zabbix puts this host into maintenance mode and does not give an alert if it is unavailable
- Creating one or more data items
- Create one or more triggers based on data elements
- Creating dependencies between triggers


More information about this can be found in the documentation, which I plan to do soon.


Used modules:

    os,
    sys,
    requests,
    pyodbc,
    time,
    datetime
