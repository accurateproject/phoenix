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
    r = call('SetTpDestinationRate', {'Tenant':tenant, 'Tag':'DR_STANDARD', 'Bindings':bindings})
    results['DestinationRates'].append(r)

    results['RatingPlans'] = []
    r = call('SetTpRatingPlan', {'Tenant':tenant, 'Tag':'RP_STANDARD', 'Bindings':
                                 [{'DestinationRatesTag':'DR_STANDARD', 'TimingTag':'*any', 'Weight':10}]})
    results['RatingPlans'].append(r)

    results['RatingProfiles'] = []
    direction = '*out' #if rs.direction == 'outbound' else '*in'
    r = call('SetTpRatingProfile', {'Tenant':tenant, 'Direction':direction, 'Category':'call', 'Subject':client_name, 'Activations':
                                    [{'ActivationTime':'2012-01-01T00:00:00Z', "RatingPlanTag":"RP_STANDARD"}]})
    results['RatingProfiles'].append(r)

    response = ''
    for key, result_list in  results.iteritems():
        response += key + '<br>'
        r = ''
        for result in result_list:
            print result
            if result['result'] != 'OK':
                r += 'result: %s error: %s <br>' % (result['result'], result['error'])
        if len(r) == 0:
            r = 'OK<br>'
        response += r
    return response

def activate_tpid(tpid):
    r = call('LoadTariffPlanFromStorDb', {'TPid': tpid, 'FlushDb': False, 'DryRun': False, 'Validate':True})
    result = tpid + ' activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    return result

def account_update(client):
    tenant = client.unique_code #rs.client.reseller.unique_code
    client_name = client.unique_code

    r = call('SetAccount', {"Tenant":tenant, "Account":client_name, "AllowNegative":True})
    result = 'Account activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    query = '{'
    if client.nb_prefix:
        query += "'Destination':{'$crepl':['^%(prefix)s(\\\\d+)','${1}']}," % dict(prefix=client.nb_prefix)
    query += '''
'sip_from_host':{'$in':%(gateways)s},
'Account':{'$usr':'%(client)s'},
'Tenant':{'$usr':'%(tenant)s'},
'Subject':{'$usr':'%(client)s'},
'direction':{'$usr': 'outbound'}''' % dict(gateways=client.reseller.gateways, client=client_name, tenant=tenant)
    query += '}'

    r = call('UsersV1.UpdateUser', {"Tenant":tenant, "Name":client_name, "Weight":10, "Query":query})
    result += 'User activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    return result

def stats_to_tp(client, actions, triggers, stats):
    result = 'Actions activation<br>'
    partial_result = 'OK<br>'
    action_dict = {}
    for action in actions:
        action_tag = action.name.replace(' ', '_')
        if action_tag not in action_dict:
            action_dict[action_tag] = []
        action_dict[action_tag].append({
            'Identifier': '*'+action.action_type,
        })
    for action_tag, action_body in action_dict.iteritems():
        r = call('SetTpActions', {'TPid': client.unique_code + "_stats", 'ActionsId': action_tag, "Actions": action_body})
        if r['result'] != 'OK':
            partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])
            break
    result += partial_result

    result += 'Trigger activation<br>'
    partial_result = 'OK<br>'
    trigger_dict = {}
    for trigger in triggers:
        trigger_tag = trigger.name.replace(' ', '_')
        if trigger_tag not in trigger_dict:
            trigger_dict[trigger_tag] = []
        trigger_dict[trigger_tag].append({
            'ThresholdType': '*'+trigger.threshold_type,
	    'ThresholdValue': trigger.threshold_value,
	    'Recurrent': trigger.recurrent,
	    'MinSleep': trigger.min_sleep,
            'MinQueuedItems': trigger.min_queued_items,
	    'ActionsId': trigger.act.name,
        })
    for trigger_tag, trigger_body in trigger_dict.iteritems():
        r = call('SetTpActionTriggers', {'TPid': client.name + "_stats", 'ActionTriggersId': trigger_tag, "ActionTriggers": trigger_body})
        if r['result'] != 'OK':
            partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])
            break
    result += partial_result

    result += 'Stats activation<br>'
    partial_result = 'OK<br>'
    for st in stats:
        r = call('SetTpCdrStats', {'TPid': client.name + "_stats", 'CdrStatsId': st.name, "CdrStats": [{'QueueLength': str(st.queue_length), 'TimeWindow': str(st.time_window), 'SaveInterval': str(st.save_interval), 'Metrics': ';'.join(st.metrics),
        'SetupInterval': str(st.setup_interval), 'TORs': ';'.join(st.tors), 'CdrHosts': ';'.join(st.cdr_hosts), 'CdrSources': ';'.join(st.cdr_sources),
        'ReqTypes': ';'.join(st.req_types), 'Directions': ';'.join(st.directions), 'Tenants': ';'.join(st.tenants), 'Categories': ';'.join(st.categories),
        'Accounts': ';'.join(st.accounts), 'Subjects': ';'.join(st.subjects), 'DestinationIds': ';'.join(st.destination_ids),
        'PddInterval': st.pdd_interval, 'UsageInterval': st.usage_interval, 'Suppliers': ';'.join(st.suppliers), 'DisconnectCauses': ';'.join(st.disconnect_causes),
        'MediationRunIds': ';'.join(st.mediation_run_ids), 'RatedAccounts': ';'.join(st.rated_accounts),
        'RatedSubject': ';'.join(st.rated_subjects), 'CostInterval': st.cost_interval, 'ActionTriggers': ';'.join(st.triggers)}]})
        if r['result'] != 'OK':
            partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])
            break
    result += partial_result

    return result

def reload_stats(stats):
    result = 'Stats realod<br>'
    partial_result = 'OK<br>'
    # reload
    r = call('CDRStatsV1.ReloadQueues', {'StatsQueueIds':[st.name for st in stats]})
    if r['result'] != 'OK':
        partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])

    #reset
    r = call('CDRStatsV1.ResetQueues', {'StatsQueueIds':[st.name for st in stats]})
    if r['result'] != 'OK':
        partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])

    result += partial_result


    return result
