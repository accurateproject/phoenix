import sys
import random
import requests
from gluon.contrib.appconfig import AppConfig
from gluon import current

myconf = AppConfig(reload=False)

def upper_under(text):
    return text.upper().replace(' ', '_')

def call(method, *args):
    method = 'ApiV1.' + method if '.' not in method else method
    try:
        r = requests.post(myconf.get('accurate.server'),
            json = {'id':random.randint(1, sys.maxint), 'method': method, 'params':args})
    except requests.exceptions.ConnectionError as e:
        return e
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return e
    try:
        response = r.json()
    except ValueError as e:
        return e
    return response


def rate_sheet_to_tp(rs, rs_rates):
    destinations = []
    rates = []
    tenant = rs.client.unique_code
    client_name = rs.client.unique_code
    rs_name = upper_under(rs.name)
    rs_id = '_%s_%s_' % (rs.unique_code, rs.direction)
    for rate in rs_rates:
        rate.code_name = upper_under(rate.code_name)
        destinations.append({'Tenant':tenant, 'Code':rate.code, 'Tag':rate.code_name})
        rates.append({'Tenant':tenant, 'Tag':'R'+rate.code, 'Slots':
                      [{'Rate':rate.rate, 'RateUnit':'60s', 'RateIncrement':str(rate['min_increment']) + 's'}]})

    results = {}
    results['Destinations'] = []
    for dest in destinations:
        r = call('SetTpDestination', dest)
        results['Destinations'].append(r)

    results['Rates'] = []
    for rate in rates:
        r = call('SetTpRate', rate)
        results['Rates'].append(r)

    results['DestinationRates'] = []
    bindings=[]
    for dest in destinations:
        bindings.append({'DestinationCode':dest['Code'], 'RatesTag':'R'+dest['Code'], 'RoundingMethod':'*middle', 'RoundingDecimals':6})
    r = call('SetTpDestinationRate', {'Tenant':tenant, 'Tag':'DR_STANDARD'+rs_id, 'Bindings':bindings})
    results['DestinationRates'].append(r)

    results['RatingPlans'] = []
    r = call('SetTpRatingPlan', {'Tenant':tenant, 'Tag':'RP_STANDARD'+rs_id, 'Bindings':
                                 [{'DestinationRatesTag':'DR_STANDARD'+rs_id, 'TimingTag':'*any', 'Weight':10}]})
    results['RatingPlans'].append(r)

    results['RatingProfiles'] = []
    direction = '*out' #if rs.direction == 'outbound' else '*in'
    category = 'call_out' if rs.direction == 'outbound' else 'call_in'
    r = call('SetTpRatingProfile', {'Tenant':tenant, 'Direction':direction, 'Category':category, 'Subject':client_name, 'Activations':
                                    [{'ActivationTime':'2012-01-01T00:00:00Z', "RatingPlanTag":"RP_STANDARD"+rs_id}]})
    results['RatingProfiles'].append(r)

    response = ''
    for key, result_list in  results.iteritems():
        response += key + '<br>'
        r = ''
        for result in result_list:
            if result['result'] != 'OK':
                r += 'result: %s error: %s <br>' % (result['result'], result['error'])
        if len(r) == 0:
            r = 'OK<br>'
        response += r
    r = call('ReloadCache', {"Tenant":tenant})
    response += 'Cache reload<br>'
    if r['result'] != 'OK':
        response = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        response += 'OK<br>'
    return response

def account_update(client):
    tenant = client.unique_code #rs.client.reseller.unique_code
    client_name = client.unique_code
    r = call('SetAccount', {"Tenant":tenant, "Account":client_name+"_out", "AllowNegative":True, "Disabled":client.status == 'disabled'})
    result = 'Account outbound activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    r = call('SetAccount', {"Tenant":tenant, "Account":client_name+"_in", "AllowNegative":True, "Disabled":client.status == 'disabled'})
    result = 'Account inbound activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'


    query = '{'
    if client.nb_prefix:
        query += "'Destination':{'$crepl':['^%(prefix)s(\\\\d+)','${1}']}," % dict(prefix=client.nb_prefix)
    query += ''' 'sip_from_host':{'$in':%(gateways)s}, 'Account':{'$usr':'%(client)s_out'}, 'Tenant':{'$usr':'%(tenant)s'}, 'Category':{'$usr':'call_out'}, 'Subject':{'$usr':'%(client)s'}'''\
             % dict(gateways=client.reseller.gateways, client=client_name, tenant=tenant)
    query += '}'
    r = call('UsersV1.UpdateUser', {"Tenant":tenant, "Name":client_name+"_out", "Weight":20, "Query":query})
    result += 'User outbound activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    query = '{'
    if client.nb_prefix:
        query += "'Destination':{'$crepl':['^%(prefix)s(\\\\d+)','${1}']}," % dict(prefix=client.nb_prefix)
    query += ''' 'sip_to_host':{'$in':%(gateways)s}, 'Account':{'$usr':'%(client)s_in'}, 'Tenant':{'$usr':'%(tenant)s'}, 'Category':{'$usr':'call_in'}, 'Subject':{'$usr':'%(client)s'}'''\
             % dict(gateways=client.reseller.gateways, client=client_name, tenant=tenant)
    query += '}'
    r = call('UsersV1.UpdateUser', {"Tenant":tenant, "Name":client_name+"_in", "Weight":10, "Query":query})
    result += 'User inbound activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'

    r = call('UsersV1.ReloadUsers', {"Tenant":tenant})
    result += 'User reload<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    return result

def account_disable(client):
    tenant = client.unique_code #rs.client.reseller.unique_code
    client_name = client.unique_code

    r = call('SetAccount', {"Tenant":tenant, "Account":client_name+"_out", "Disabled":True})
    result = 'Account activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    r = call('SetAccount', {"Tenant":tenant, "Account":client_name+"_in", "Disabled":True})
    result = 'Account activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    return result

def monitor_to_tp(monitor, db):
    tenant = monitor.client.unique_code

    monitor_name = monitor.unique_code
    action_name = "act_"+monitor_name
    trigger_name = "tr_"+monitor_name

    result = 'Monitor activation<br>'
    partial_result = 'OK<br>'
    if monitor.triggered_action == "notify":
        r = call('SetTpActionGroup', {'Tenant':tenant, 'Tag':action_name, 'Actions':[
            {'Action': '*log'},
            {'Action': '*call_url_async', 'Params':'url'}
        ]})

    if r['result'] != 'OK':
        partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    result += partial_result

    partial_result = 'OK<br>'
    min_sleep = monitor.min_sleep.strip()
    r = call('SetTpActionTrigger', {'Tenant': tenant, 'Tag': trigger_name, 'Triggers': [
       {
            'ThresholdType': '*'+monitor.threshold_type,
	    'ThresholdValue': monitor.threshold_value,
	    'Recurrent': min_sleep != '',
	    'MinSleep': min_sleep,
            'MinQueuedItems': 100,
	    'ActionsTag': action_name,
            'Weight': 10,
        }
    ]})
    if r['result'] != 'OK':
        partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    result += partial_result

    filter = "{'RunID':'*default'}"
    if monitor.monitor_filter:
        filter = monitor.monitor_filter
    partial_result = 'OK<br>'
    r = call('SetTpCdrStats', {
        'Tenant': tenant,
        'Tag': monitor_name,
        'QueueLength': monitor.queue_length,
        'TimeWindow': monitor.time_window,
        'SaveInterval': '30s',
        'Metrics': monitor.metrics,
        'Filter': filter,
        'ActionTriggerTags': [trigger_name],
        'Disabled': monitor.status == 'disabled',
    })
    if r['result'] != 'OK':
        partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    result += partial_result

    result += 'Stats realod<br>'
    partial_result = 'OK<br>'
    # reload
    r = call('CDRStatsV1.ReloadQueues', {'Tenant':tenant, 'IDs':[monitor_name]})
    if r['result'] != 'OK':
        partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])

    #reset
    r = call('CDRStatsV1.ResetQueues', {'Tenant':tenant, 'IDs':[monitor_name]})
    if r['result'] != 'OK':
        partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])

    result += partial_result


    return result
