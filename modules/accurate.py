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
        return dict(error=str(e))
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return dict(error=str(e))
    try:
        response = r.json()
    except ValueError as e:
        return dict(error=str(e))
    return response


def err(r):
    if u'error' in r:
        return r[u'error']
    return ''

def rate_sheet_to_tp(rs, rs_rates):
    destinations = []
    rates = []
    tenant = rs.client.unique_code
    client_name = rs.client.unique_code
    rs_name = upper_under(rs.name)
    rs_id = '_out' if rs.direction == 'outbound' else '_in'
    for rate in rs_rates:
        rate.code_name = upper_under(rate.code_name)
        destinations.append({'Tenant':tenant, 'Code':rate.code, 'Tag':rate.code_name})
        rates.append({'Tenant':tenant, 'Tag':'R'+rate.code, 'Slots':
                      [{'Rate':rate.rate, 'RateUnit':'60s', 'RateIncrement':str(rate['min_increment']) + 's'}]})


    for dest in destinations:
        r = call('SetTpDestination', dest)
        if err(r): return err(r)

    for rate in rates:
        r = call('SetTpRate', rate)
        if err(r): return err(r)

    bindings=[]
    for dest in destinations:
        bindings.append({'DestinationCode':dest['Code'], 'RatesTag':'R'+dest['Code'], 'RoundingMethod':'*middle', 'RoundingDecimals':6})
    r = call('SetTpDestinationRate', {'Tenant':tenant, 'Tag':'DR_STANDARD'+rs_id, 'Bindings':bindings})
    if err(r): return err(r)

    r = call('SetTpRatingPlan', {'Tenant':tenant, 'Tag':'RP_STANDARD'+rs_id, 'Bindings':
                                 [{'DestinationRatesTag':'1DR_STANDARD'+rs_id, 'TimingTag':'*any', 'Weight':10}]})
    if err(r): return err(r)

    direction = '*out' #if rs.direction == 'outbound' else '*in'
    category = 'call_out' if rs.direction == 'outbound' else 'call_in'
    r = call('SetTpRatingProfile', {'Tenant':tenant, 'Direction':direction, 'Category':category, 'Subject':client_name, 'Activations':
                                    [{'ActivationTime':'2012-01-01T00:00:00Z', "RatingPlanTag":"RP_STANDARD"+rs_id}]})
    if err(r): return err(r)

    r = call('ReloadCache', {"Tenant":tenant})
    if err(r): return err(r)
    return 'rate sheet activated successfully'

def account_update(client):
    tenant = client.unique_code  # rs.client.reseller.unique_code
    client_name = client.unique_code
    r = call('SimpleAccountSet', {"Tenant":tenant, "Account":client_name, "Disabled":client.status == 'disabled'})
    if err(r): return err(r)

    if client.status == 'disabled':
        return 'account update successfully'

    query = '{'
    if client.nb_prefix:
        query += "'Destination':{'$crepl':['^%(prefix)s(\\\\d+)','${1}']}," % dict(prefix=client.nb_prefix)
    query += ''' 'sip_from_host':{'$in':%(gateways)s}, 'Account':{'$usr':'%(client)s'}, 'Tenant':{'$usr':'%(tenant)s'}, 'Category':{'$usr':'call_out'}, 'Subject':{'$usr':'%(client)s'}'''\
             % dict(gateways=client.reseller.gateways, client=client_name, tenant=tenant)
    query += '}'
    r = call('UsersV1.UpdateUser', {"Tenant":tenant, "Name":client_name+"_out", "Weight":20, "Query":query})
    if err(r): return err(r)
    query = '{'
    if client.nb_prefix:
        query += "'Destination':{'$crepl':['^%(prefix)s(\\\\d+)','${1}']}," % dict(prefix=client.nb_prefix)
    query += ''' 'sip_to_host':{'$in':%(gateways)s}, 'Account':{'$usr':'%(client)s'}, 'Tenant':{'$usr':'%(tenant)s'}, 'Category':{'$usr':'call_in'}, 'Subject':{'$usr':'%(client)s'}'''\
             % dict(gateways=client.reseller.gateways, client=client_name, tenant=tenant)
    query += '}'
    r = call('UsersV1.UpdateUser', {"Tenant":tenant, "Name":client_name+"_in", "Weight":10, "Query":query})
    if err(r): return err(r)

    result = users_reload(tenant)
    return result or 'account updated successfully'

def account_remove(client):
    tenant = client.unique_code  # rs.client.reseller.unique_code
    client_name = client.unique_code

    r = call('RemoveTpAllTenant', {'Tenant':tenant})
    if err(r): return err(r)
    # reload users
    users_reload()
    # reload monitors
    monitors_reload()
    # reload accounts
    accounts_reload()

    return 'account removed successfully'


def monitor_update(monitor):
    tenant = monitor.client.unique_code

    monitor_name = monitor.unique_code
    action_name = "act_"+monitor_name
    trigger_name = "tr_"+monitor_name


    if monitor.triggered_action == "notify":
        r = call('SetTpActionGroup', {'Tenant':tenant, 'Tag':action_name, 'Actions':[
            {'Action': '*log'},
            {'Action': '*call_url_async', 'Params':'url'}
        ]})
        if err(r): return err(r)

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
    if err(r): return err(r)


    filter = "{'RunID':'*default'}"
    if monitor.monitor_filter:
        filter = monitor.monitor_filter
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
    if err(r): return err(r)

    result = monitors_reload(monitor.client.unique_code, monitor.unique_code)
    return result or 'monitor updated successfully'

def monitor_remove(monitor):
    tenant = monitor.client.unique_code

    monitor_name = monitor.unique_code
    action_name = "act_"+monitor_name
    trigger_name = "tr_"+monitor_name

    # remove cdrstats
    r = call('CDRStatsV1.RemoveQueue', {'Tenant':tenant, 'IDs':[monitor_name]})
    if err(r): return err(r)

    # remove action trigger
    r = call('RemoveActionTriggers', {'Tenant':tenant, 'GroupIDs':[trigger_name]})
    if err(r): return err(r)
    # remove action
    r = call('RemoveActionGroups', {'Tenant':tenant, 'GroupIDs':[action_name]})
    if err(r): return err(r)

    result = monitors_reload()
    return 'monitor removed successfully'


def users_reload(tenant=None):
    r = call('UsersV1.ReloadUsers', {"Tenant":tenant})
    if err(r): return err(r)

def accounts_reload(tenant=None):
    r = call('SimpleAccountsReload', {"Tenant":tenant})
    if err(r): return err(r)

def monitors_reload(tenant=None, name=None, reset=False):
    # reload
    r = call('CDRStatsV1.ReloadQueues', {'Tenant':tenant, 'IDs':[name]})
    if err(r): return err(r)

    if not reset: return 'monitor reloaded successfully'
    #reset
    r = call('CDRStatsV1.ResetQueues', {'Tenant':tenant, 'IDs':[name]})
    if err(r): return err(r)
    return 'monitor reloaded successfully'
