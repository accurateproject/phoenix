import sys
import random
import requests
from gluon.contrib.appconfig import AppConfig
from gluon import current


myconf = AppConfig(reload=False)

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
    for rate in rs_rates:
        rate.code_name = rate.code_name.replace(' ', '_')
        if rate.code_name not in destinations:
            destinations[rate.code_name] = []
        if rate.code not in destinations[rate.code_name]:
            destinations[rate.code_name].append(rate.code)
        rate_id = "RT_" + rate.code_name
        rates[rate_id] = {"rate": rate.rate, "min_increment": rate.min_increment, }

    results = {}
    results['Destinations'] = []
    for dest_id, prefixes in destinations.iteritems():
        r = call('SetTPDestination', {'TPid': rs.name, 'DestinationId': dest_id, 'Prefixes': prefixes})
        results['Destinations'].append(r)

    results['Rates'] = []
    for rate_id, rate in rates.iteritems():
        r = call('SetTPRate', {'TPid': rs.name, 'RateId': rate_id,
                'RateSlots': [{'Rate': rate['rate'], 'RateUnit': '60s', 'RateIncrement': str(rate['min_increment']) + 's', 'GroupIntervalStart': '0s'}]})
        results['Rates'].append(r)

    results['DestinationRates'] = []
    for dest_id in destinations:
        r = call('SetTPDestinationRate', {'TPid': rs.name, 'DestinationRateId': 'DR_' + dest_id,
                'DestinationRates': [{'DestinationId': dest_id, 'RateId': 'RT_'+dest_id, 'RoundingMethod': '*up', 'RoundingDecimals': 6, 'MaxCost':0, 'MaxCostStrategy':''}]})
        results['DestinationRates'].append(r)

    results['RatingPlans'] = []
    rating_plan_bindings = []
    for dest_id in destinations:
        rating_plan_bindings.append({'DestinationRatesId': 'DR_' + dest_id, 'TimingId': '*any', 'Weight': 10})
    r = call('SetTPRatingPlan', {'TPid': rs.name, 'RatingPlanId': 'RP_' + rs.client.name, 'RatingPlanBindings': rating_plan_bindings})
    results['RatingPlans'].append(r)

    results['RatingProfiles'] = []
    direction = '*out' if rs.direction == 'outbound' else '*in'
    r = call('SetTPRatingProfile', {'TPid': rs.name, 'LoadId': current.request.now.strftime('%d%b%Y_%H:%M:%S'), 'Direction': direction, 'Tenant': rs.client.name,  'Category': 'call', 'Subject': '*any',
            'RatingPlanActivations': [{'RatingPlanId': 'RP_' + rs.client.name, 'ActivationTime': '2010-01-01T00:00:00Z', 'FallbackSubjects': '', 'CdrStatQueueIds':''}]})
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

def activate_rate_sheet(rs):
    r = call('LoadTariffPlanFromStorDb', {'TPid': rs.name, 'FlushDb': False, 'DryRun': False, 'Validate':True})
    result = 'Activation<br>'
    if r['result'] != 'OK':
        result = 'result: %s error: %s <br>' % (result['result'], result['error'])
    else:
        result += 'OK<br>'
    return result

def activate_client():
    pass
