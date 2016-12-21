import accurate
import json
from collections import OrderedDict

def status():
    session.forget(response)
    return raccurate.call("Responder.Status")

def accounts():
    session.forget(response)
    return accurate.call("GetAccounts",  dict(tenant = 'R1'))

def queueids():
    session.forget(response)
    return accurate.call("CDRStatsV1.GetQueueIds")

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def metrics():
    session.forget(response)
    client_id = request.args(0)
    if not accessible_client(client_id):
        redirect(URL('user', 'not_autorized'))
    stats = db(db.stats.client == client_id).select(db.stats.name)
    metrics = {}
    for q in stats:
        r = accurate.call("CDRStatsV1.GetMetrics", dict(StatsQueueId = q.name))
        metrics[q.name] = r['error'] if r['error'] else r['result']

    return metrics

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def cdrs():
    client_id = request.args(0)
    if not accessible_client(client_id):
        redirect(URL('user', 'not_autorized'))
    client = db.client[client_id] or redirect(URL('user', 'not_autorized'))


    field_dict = OrderedDict()
    field_dict['cgr_ids'] = 'list:string'
    field_dict['not_cgr_ids'] = 'list:string'
    field_dict['origin_hosts'] = 'list:string'
    field_dict['not_origin_hosts'] = 'list:string'
    field_dict['sources'] = 'list:string'
    field_dict['not_sources'] = 'list:string'
    #field_dict['tors'] = 'list:string'
    #field_dict['not_tors'] = 'list:string'
    #field_dict['request_types'] = 'list:string'
    #field_dict['not_request_types'] = 'list:string'
    #field_dict['directions'] = 'list:string'
    #field_dict['not_directions'] = 'list:string'
    #field_dict['categories'] = 'list:string'
    #field_dict['not_categories'] = 'list:string'
    field_dict['destination_prefixes'] = 'list:string'
    field_dict['not_destination_prefixes'] = 'list:string'
    field_dict['suppliers'] = 'list:string'
    field_dict['not_suppliers'] = 'list:string'
    field_dict['disconnect_causes'] = 'list:string'
    field_dict['not_disconnect_causes'] = 'list:string'
    field_dict['costs'] = 'list:string'
    field_dict['not_costs'] = 'list:string'
    field_dict['extra_fields'] = 'string'
    field_dict['not_extra_fields'] = 'string'
    field_dict['order_id_start'] = 'integer'
    field_dict['order_id_end'] = 'integer'
    field_dict['setup_time_start'] = 'string'
    field_dict['setup_time_end'] = 'string'
    field_dict['answer_time_start'] = 'string'
    field_dict['answer_time_end'] = 'string'
    field_dict['created_at_start'] = 'string'
    field_dict['created_at_end'] = 'string'
    field_dict['updated_at_start'] = 'string'
    field_dict['updated_at_end'] = 'string'
    field_dict['min_usage'] = 'string'
    field_dict['max_usage'] = 'string'
    field_dict['min_pdd'] = 'string'
    field_dict['max_pdd'] = 'string'
    field_dict['min_cost'] = 'float'
    field_dict['max_cost'] = 'float'
    if auth.has_membership('admin'):
        field_dict['run_ids'] = 'list:string'
        field_dict['not_run_ids'] = 'list:string'
        field_dict['tenants'] = 'list:string'
        field_dict['not_tenants'] = 'list:string'
        field_dict['accounts'] = 'list:string'
        field_dict['not_accounts'] = 'list:string'
        field_dict['subjects'] = 'list:string'
        field_dict['not_subjects'] = 'list:string'

    params = {}
    fields = []
    for key, value in field_dict.iteritems():
        field = (key,value)
        fields.append(Field(*field))
    form=SQLFORM.factory(*fields, formstyle='bootstrap3_stacked')
    if form.process(keepvalues=True).accepted:
        for key, value in form.vars.iteritems():
            if field_dict[key] == 'list:string' and value != '':
                if isinstance(value, basestring):
                    params[key.replace('_','')] = [value]
                else:
                    params[key.replace('_','')] = value
                continue
            if key in ('extra_fields', 'not_extra_fields') and value != '':
                params[key.replace('_','')] = json.loads(value)
                continue
            if field_dict[key] in ('integer', 'float', 'string') and value != '':
                params[key.replace('_','')] = value
                continue
    elif form.errors:
        response.flash = 'form has errors'

    page = int(request.args(1)) if request.args(1) else 0
    items_per_page=myconf.get('accurate.items_per_page')

    params['offset'], params['limit'] = page*items_per_page, items_per_page+1

    if not auth.has_membership('admin'):
        params['tenants'] = [client.reseller.unique_code]
        params['accounts'] = [client.unique_code]
        params['subjects'] = [client.unique_code]

    cdrs = []
    r = accurate.call("GetCdrs",  params)

    if r['error']:
        response.flash = r['error']
    else:
        cdrs = r['result']

    # prepare the params for show
    if 'tenants' in params: del params['tenants']
    if 'subjects' in params: del params['subjects']
    if 'accounts' in params: del params['accounts']
    if 'limit' in params: del params['limit']
    if 'offset' in params: del params['offset']
    return dict(form=form, cdrs=cdrs, page=page, items_per_page=items_per_page, client=client, params=params)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def activate_rate_sheet():
    rate_sheet_id = request.args(0) or redirect('index')
    rate_sheet = db.rate_sheet[rate_sheet_id]
    __check_rate_sheet(rate_sheet)
    rs_rates = db(db.rate.sheet == rate_sheet.id).select()
    rs_name = accurate.upper_under(rate_sheet.name)

    resp = accurate.rate_sheet_to_tp(rate_sheet, rs_rates)
    resp +=  accurate.account_to_tp(rate_sheet)
    resp +=  accurate.activate_tpid(rs_name + "_tp")
    resp +=  accurate.activate_tpid(rs_name + "_acc")

    rate_sheet.client.active_rate_sheet = rate_sheet.id
    rate_sheet.client.update_record()
    session.flash = XML(resp)
    redirect(request.env.http_referer)


@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def activate_stats():
    client_id = request.args(0) or redirect('index')
    client = db.client[client_id]
    if not accessible_client(client_id):
        redirect(URL('user', 'not_autorized'))
    client_name = accurate.upper_under(client.name)

    actions = db(db.act.client == client_id).select()
    triggers = db(db.action_trigger.client == client_id).select()
    stats = db(db.stats.client == client_id).select()
    resp = accurate.stats_to_tp(client, actions, triggers, stats)
    resp +=  accurate.activate_tpid(client_name + "_stats")
    session.flash = XML(resp)
    redirect(request.env.http_referer)
