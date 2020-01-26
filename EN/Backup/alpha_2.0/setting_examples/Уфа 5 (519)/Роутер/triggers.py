
{
    'triggerid': r'16640',
    'description': r'Unavailable by ICMP ping',
    'expression': r'{31928}=0',
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
        {
            "triggerid": "19232",
            "description": r"Unavailable by ICMP ping"
        },
    ],

},


{
    'triggerid': r'16641',
    'description': r'High ICMP ping loss',
    'expression': r'{18865}>{$ICMP_LOSS_WARN} and {18865}<100',
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
            "triggerid": "16640",
            "description": r"Unavailable by ICMP ping"
        },
    ],

},


{
    'triggerid': r'16642',
    'description': r'High ICMP ping response time',
    'expression': r'{18866}>{$ICMP_RESPONSE_TIME_WARN}',
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
            "triggerid": "16640",
            "description": r"Unavailable by ICMP ping"
        },
        {
            "triggerid": "16641",
            "description": r"High ICMP ping loss"
        },
    ],

},