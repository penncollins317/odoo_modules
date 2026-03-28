TRANSACTION_STATUS_MAPPING = {
    'pending': ('WAIT_BUYER_PAY',),
    'done': ('TRADE_SUCCESS', 'TRADE_FINISHED'),
    'canceled': ('TRADE_CLOSED',),
}

STATUS_MAPPING = {
    'WAIT_BUYER_PAY': 'pending',
    'TRADE_SUCCESS': 'done',
    'TRADE_FINISHED': 'done',
    'TRADE_CLOSED': 'canceled',
}