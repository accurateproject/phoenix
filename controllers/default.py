# -*- coding: utf-8 -*-
import accurate

@auth.requires_login()
def index():
    if auth.has_membership('admin'):
        redirect(URL('default', 'resellers'))
    if not auth.has_membership('admin') and (auth.has_membership('reseller') or auth.has_membership('client')):
        redirect(URL('default', 'my_clients'))
    return dict()

@auth.requires_membership('admin')
def resellers():
    if request.args(0): # update
        db.reseller.unique_code.readable = False
        db.reseller.unique_code.writable = False
    form = crud.update(db.reseller, request.args(0), onaccept=give_reseller_owner_permissions)
    query = auth.accessible_query('read', db.reseller, auth.user_id)
    resellers = db(query).select()
    return dict(form=form, resellers=resellers)

@auth.requires(auth.has_membership('admin') or auth.has_membership('reseller'))
def clients():
    show_form = True
    reseller_id = request.args(0) or redirect('index')
    if not accessible_reseller(reseller_id):
        redirect(URL('user', 'not_autorized'))
    db.client.reseller.default = reseller_id
    db.client.nb_prefix.requires=IS_NOT_IN_DB(db(db.client.reseller==reseller_id), 'client.nb_prefix', error_message=T('reseller has already a client with this prefix'))
    if request.vars['edit']:
        db.client.unique_code.readable = False
        db.client.unique_code.writable = False
    onaccept = give_client_owner_permissions if auth.has_membership('reseller') else None
    form = crud.update(db.client, request.vars['edit'], next=URL('default', 'clients', args=reseller_id), onaccept=onaccept)

    clients = db(db.client.reseller == reseller_id).select()
    return dict(form=form, show_form=show_form, clients=clients)

@auth.requires(auth.has_membership('client'))
def my_clients():
    show_form = False
    client_id = request.vars['edit']
    if client_id:
        show_form = True
        db.client.unique_code.readable = False
        db.client.unique_code.writable = False
        form = crud.update(db.client, client_id, next=URL('default', 'my_clients'))
    else:
        form = None
    query = auth.accessible_query('read', db.client, auth.user_id)
    clients = db(query).select()
    response.view = 'default/clients.html'
    return dict(form=form, show_form=show_form, clients=clients)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rate_sheets():
    client_id=request.args(0) or redirect('index')
    client = db.client[client_id] or redirect('index')
    if not accessible_client(client_id):
        redirect(URL('user', 'not_autorized'))
    db.rate_sheet.client.default = client.id
    if request.args(1): # update
        db.rate_sheet.unique_code.readable = False
        db.rate_sheet.unique_code.writable = False
    form = crud.update(db.rate_sheet, request.args(1), next=URL('default', 'rate_sheets', args=client.id))
    rate_sheets = db(db.rate_sheet.client == client.id).select()
    return dict(form=form, rate_sheets=rate_sheets, client=client)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rate_sheet_import():
    import csv
    from dateutil.parser import parse
    rate_sheet_id = request.args(0) or redirect('index')
    rate_sheet = db.rate_sheet[rate_sheet_id]
    __check_rate_sheet(rate_sheet)

    db.rate.sheet.default = rate_sheet_id
    form = FORM(INPUT(_type='file', _name='data'), INPUT(_type='submit'))
    if form.process().accepted:
        rate_sheet_reader = csv.reader(form.vars.data.file, delimiter=',', quotechar='"')
        for row in rate_sheet_reader:
            if row[0] == 'Code': # header
                continue
            db.rate.update_or_insert((db.rate.code == row[0]) & (db.rate.sheet == rate_sheet_id),
                                     code = row[0],
                                     code_name = row[1],
                                     rate = float(row[2]),
                                     effective_date = parse(row[3]), #01/15/2015 00:00:00 +0000
                                     min_increment = int(row[4]))
        redirect(URL('default', 'rates', args=rate_sheet_id))
    return dict(form=form)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rates():
    rate_sheet_id = request.args(0) or redirect('index')
    rate_sheet = db.rate_sheet[rate_sheet_id]
    __check_rate_sheet(rate_sheet)
    db.rate.sheet.default = rate_sheet_id
    form = crud.update(db.rate, request.args(1))
    rates = db(db.rate.sheet == rate_sheet_id).select()
    return dict(form=form, rate_sheet=rate_sheet, rates=rates)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def stats():
    client_id = request.args(0) or redirect('index')
    client = db.client[client_id] or redirect(URL('default', 'index'))
    stats_id = request.args(1)
    if stats_id is not None:
        stats = db.stats[stats_id]
        __check_stats(stats)
    db.stats.tenants.default = [client.unique_code]
    db.stats.accounts.default = [client.unique_code]
    db.stats.client.default = client.id
    form = crud.update(db.stats, request.args(1), next=URL('default', 'stats', args=client.id))
    stats = db(db.stats.client == client.id).select()
    return dict(form=form, client=client, stats=stats)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def triggers():
    client_id = request.args(0) or redirect('index')
    client = db.client[client_id] or redirect(URL('default', 'index'))
    trigger_id = request.args(1)
    if trigger_id is not None:
        trigger = db.action_trigger[trigger_id]
        __check_trigger(trigger)
    db.action_trigger.client.default = client.id
    form = crud.update(db.action_trigger, request.args(1), next=URL('default', 'triggers', args=client.id))
    triggers = db(db.action_trigger.client == client.id).select()
    return dict(form=form, client=client, triggers=triggers)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def actions():
    client_id = request.args(0) or redirect('index')
    client = db.client[client_id] or redirect(URL('default', 'index'))
    action_id = request.args(1)
    if action_id is not None:
        action = db.act[action_id]
        __check_action(action)
    db.act.client.default = client.id
    form = crud.update(db.act, request.args(1), next=URL('default', 'actions', args=client.id))
    actions = db(db.act.client == client.id).select()
    return dict(form=form, client=client, actions=actions)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
