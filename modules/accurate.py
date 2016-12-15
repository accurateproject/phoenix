import sys
import random
import requests
from gluon.contrib.appconfig import AppConfig
from gluon import current


myconf = AppConfig(reload=False)

def upper_under(text):
    return text.upper().replace(' ', '_')

def call(method, *args):
    method = 'ApierV2.' + method if '.' not in method else method
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
    destinations = {}
    rates = {}
    reseller_name = upper_under(rs.client.reseller.name)
    client_name = upper_under(rs.client.name)
    rs_name = upper_under(rs.name)
    for rate in rs_rates:
        rate.code_name = upper_under(rate.code_name)
        if rate.code_name not in destinations:
            destinations[rate.code_name] = []
        if rate.code not in destinations[rate.code_name]:
            destinations[rate.code_name].append(rate.code)
        rate_id = client_name + "_RT_" + rate.code_name
        rates[rate_id] = {"rate": rate.rate, "min_increment": rate.min_increment, }

    results = {}
    results['Destinations'] = []
    for dest_id, prefixes in destinations.iteritems():
        r = call('SetTPDestination', {'TPid': rs_name + "_tp", 'DestinationId': dest_id, 'Prefixes': prefixes})
        results['Destinations'].append(r)

    results['Rates'] = []
    for rate_id, rate in rates.iteritems():
        r = call('SetTPRate', {'TPid': rs_name + "_tp", 'RateId': rate_id,
                'RateSlots': [{'Rate': rate['rate'], 'RateUnit': '60s', 'RateIncrement': str(rate['min_increment']) + 's', 'GroupIntervalStart': '0s'}]})
        results['Rates'].append(r)

    results['DestinationRates'] = []
    for dest_id in destinations:
        r = call('SetTPDestinationRate', {'TPid': rs_name + "_tp", 'DestinationRateId': client_name + '_DR_' + dest_id,
                'DestinationRates': [{'DestinationId': dest_id, 'RateId': client_name + '_RT_'+dest_id, 'RoundingMethod': '*up', 'RoundingDecimals': 6, 'MaxCost':0, 'MaxCostStrategy':''}]})
        results['DestinationRates'].append(r)

    results['RatingPlans'] = []
    rating_plan_bindings = []
    for dest_id in destinations:
        rating_plan_bindings.append({'DestinationRatesId': client_name + '_DR_' + dest_id, 'TimingId': '*any', 'Weight': 10})
    r = call('SetTPRatingPlan', {'TPid': rs_name + "_tp", 'RatingPlanId': client_name + '_RP_' + rs_name, 'RatingPlanBindings': rating_plan_bindings})
    results['RatingPlans'].append(r)

    results['RatingProfiles'] = []
    direction = '*out' #if rs.direction == 'outbound' else '*in'
    r = call('SetTPRatingProfile', {'TPid': rs_name + "_tp", 'LoadId': current.request.now.strftime('%d%b%Y_%H:%M:%S'),
            'Direction': direction, 'Tenant': reseller_name,  'Category': 'call', 'Subject': client_name,
            'RatingPlanActivations': [{'RatingPlanId': client_name + '_RP_' + rs_name, 'ActivationTime': '2010-01-01T00:00:00Z', 'FallbackSubjects': '', 'CdrStatQueueIds':''}]})
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
    return response

def activate_tpid(tpid):
    r = call('LoadTariffPlanFromStorDb', {'TPid': tpid, 'FlushDb': False, 'DryRun': False, 'Validate':True})
    result = tpid + ' activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    return result

def account_to_tp(rs):
    reseller_name = upper_under(rs.client.reseller.name)
    client_name = upper_under(rs.client.name)
    rs_name = upper_under(rs.name)
    r = call('SetTPAccountActions', {'TPid': rs_name + "_acc", 'LoadId': current.request.now.strftime('%d%b%Y_%H:%M:%S'),
            'Tenant': reseller_name, 'Account': client_name, 'ActionPlanId': '', 'ActionTriggersId': '', 'AllowNegative': True, 'Disabled':False})
    result = 'Account activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    else:
        result += 'OK<br>'
    r = call('SetTPUser', {'TPid': rs_name + "_acc", 'Tenant': reseller_name, 'UserName': rs.client.name, 'Masked': False, 'Weight': 10,
                           'Profile':[
                               {'AttrName': 'Account', 'AttrValue': client_name},
                               {'AttrName': 'Subject', 'AttrValue': client_name},
                               {'AttrName': 'Destination', 'AttrValue': 'process:~destination:s/^%s(\d+)/${1}/(^%s)' % (rs.client.nb_prefix, rs.client.nb_prefix)},
                               {'AttrName': 'sip_from_host', 'AttrValue': 'filter: %s' % ';'.join(rs.client.reseller.gateways)},
                               {'AttrName': 'direction', 'AttrValue': rs.direction},
                           ],
    })
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
        r = call('SetTPActions', {'TPid': client.name + "_stats", 'ActionsId': action_tag, "Actions": action_body})
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
        r = call('SetTPActionTriggers', {'TPid': client.name + "_stats", 'ActionTriggersId': trigger_tag, "ActionTriggers": trigger_body})
        if r['result'] != 'OK':
            partial_result = 'result: %s error: %s <br>' % (r['result'], r['error'])
            break
    result += partial_result

    result += 'Stats activation<br>'
    partial_result = 'OK<br>'
    for st in stats:
        r = call('SetTPCdrStats', {'TPid': client.name + "_stats", 'CdrStatsId': st.name, "CdrStats": [{'QueueLength': str(st.queue_length), 'TimeWindow': str(st.time_window), 'SaveInterval': str(st.save_interval), 'Metrics': ';'.join(st.metrics),
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

    #r = call('SetTPUser', {'TPid': rs.name + "_acc", 'Tenant': rs.client.reseller.name, 'UserName': rs.client.name, 'Masked': False, 'Weight': 10,
    #                       'Profile':[
    #                           {'AttrName': 'Account', 'AttrValue': rs.client.name},
    #                           {'AttrName': 'Subject', 'AttrValue': 'process:~subject:s/^%s(\d+)/${1}/' % rs.client.nb_prefix},
    #                           {'AttrName': 'Destination', 'AttrValue': 'process:~destination:s/^%s(\d+)/${1}/(^%s)' % (rs.client.nb_prefix, rs.client.nb_prefix)},
    #                           {'AttrName': 'sip_from_host', 'AttrValue': 'filter: %s' % ';'.join(rs.client.reseller.gateways)},
    #                           {'AttrName': 'direction', 'AttrValue': rs.direction},
    #                       ],
    #})
    #result += 'User activation<br>'
    #if r['result'] != 'OK':
    #    result = 'result: %s error: %s <br>' % (r['result'], r['error'])
    #else:
    #    result += 'OK<br>'
    return result
