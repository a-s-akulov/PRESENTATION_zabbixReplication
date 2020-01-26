{
    'triggerid': r'19232',
    'description': r'Unavailable by ICMP ping',
    'expression': r'{38048}=0',
    'comments': r'Last value: {ITEM.LASTVALUE1}.\nLast three attempts returned timeout.  Please check device connectivity.',
    'url': r'',
    'recovery_expression': r'',
    'correlation_tag': r'',
    'priority': r'4',
    'status': r'0',
    'type': r'0',
    'recovery_mode': r'0',
    'correlation_mode': r'0',
    'manual_close': r'0',

    'tags': [
    ],


    'dependencies': [
    ],

},


{
    'triggerid': r'19233',
    'description': r'High ICMP ping loss',
    'expression': r'{21460}>{$ICMP_LOSS_WARN} and {21460}<100',
    'comments': r'Last value: {ITEM.LASTVALUE1}.',
    'url': r'',
    'recovery_expression': r'',
    'correlation_tag': r'',
    'priority': r'2',
    'status': r'1',
    'type': r'0',
    'recovery_mode': r'0',
    'correlation_mode': r'0',
    'manual_close': r'0',

    'tags': [
    ],


    'dependencies': [
        {
            "triggerid": "19232",
            "description": r"Unavailable by ICMP ping"
        },
    ],

},


{
    'triggerid': r'19234',
    'description': r'High ICMP ping response time',
    'expression': r'{21461}>{$ICMP_RESPONSE_TIME_WARN}',
    'comments': r'Last value: {ITEM.LASTVALUE1}.',
    'url': r'',
    'recovery_expression': r'',
    'correlation_tag': r'',
    'priority': r'2',
    'status': r'1',
    'type': r'0',
    'recovery_mode': r'0',
    'correlation_mode': r'0',
    'manual_close': r'0',

    'tags': [
    ],


    'dependencies': [
        {
            "triggerid": "19232",
            "description": r"Unavailable by ICMP ping"
        },
        {
            "triggerid": "19233",
            "description": r"High ICMP ping loss"
        },
    ],

},