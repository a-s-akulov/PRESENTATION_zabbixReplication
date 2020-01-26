{
    'triggerid': r'20102',
    'description': r'Unavailable by ICMP ping',
    'expression': r'{30144}=0',
    'comments': r'Last value: {ITEM.LASTVALUE1}.\nLast three attempts returned timeout.  Please check device connectivity.',
    'url': r'',
    'recovery_expression': r'',
    'correlation_tag': r'',
    'priority': r'4',
    'status': r'1',
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
    'triggerid': r'20103',
    'description': r'High ICMP ping loss',
    'expression': r'{22330}>{$ICMP_LOSS_WARN} and {22330}<100',
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
            "triggerid": "20102",
            "description": r"Unavailable by ICMP ping"
        },
    ],

},


{
    'triggerid': r'20104',
    'description': r'High ICMP ping response time',
    'expression': r'{22331}>{$ICMP_RESPONSE_TIME_WARN}',
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
            "triggerid": "20102",
            "description": r"Unavailable by ICMP ping"
        },
        {
            "triggerid": "20103",
            "description": r"High ICMP ping loss"
        },
    ],

},


{
    'triggerid': r'24186',
    'description': r'Web acces',
    'expression': r'{35796}=1',
    'comments': r'',
    'url': r'',
    'recovery_expression': r'',
    'correlation_tag': r'',
    'priority': r'3',
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