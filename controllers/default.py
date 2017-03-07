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
    form = crud.update(db.reseller, request.args(0), onaccept=give_reseller_owner_permissions, next=URL('default', 'resellers'))
    query = auth.accessible_query('read', db.reseller, auth.user_id)
    resellers = db(query).select()
    return dict(form=form, resellers=resellers)

@auth.requires(auth.has_membership('admin') or auth.has_membership('reseller'))
def clients():
    reseller_id = request.args(0) or redirect('index')
    if not accessible_reseller(reseller_id):
        redirect(URL('user', 'not_autorized'))
    db.client.reseller.default = reseller_id
    db.client.nb_prefix.requires=IS_NOT_IN_DB(db(db.client.reseller==reseller_id), 'client.nb_prefix', error_message=T('reseller has already a client with this prefix'))
    onaccept = give_client_owner_permissions if auth.has_membership('reseller') else None
    form = crud.update(db.client, request.vars['edit'], next=URL('default', 'clients', args=reseller_id), onaccept=onaccept)
    clients = db(db.client.reseller == reseller_id).select()
    return dict(form=form, show_form=True, clients=clients)

@auth.requires(auth.has_membership('reseller') or auth.has_membership('client'))
def my_clients():
    show_form = False
    client_id = request.vars['edit']
    if client_id:
        show_form = True
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
    form = crud.update(db.rate_sheet, request.args(1), next=URL('default', 'rate_sheets', args=client.id))
    rate_sheets = db(db.rate_sheet.client == client.id).select()
    return dict(form=form, rate_sheets=rate_sheets, client=client)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rate_sheet_import():
    rate_sheet_id = request.args(0) or redirect('index')
    rate_sheet = db.rate_sheet[rate_sheet_id]
    __check_rate_sheet(rate_sheet)

    db.rate.sheet.default = rate_sheet_id
    form = FORM(INPUT(_type='file', _name='data'), INPUT(_type='submit'))
    if form.process().accepted:
        lines = []
        for line in form.vars.data.file:
            lines.append(line)
        rate_sheet.update_record(tmp_import = '\n'.join(lines))
        redirect(URL('default', 'rate_sheet_matcher', vars=dict(line=lines[0], rate_sheet_id=rate_sheet_id)))
    return dict(form=form)

def rate_sheet_matcher():
    line = request.vars.line.strip()
    rate_sheet_id = request.vars.rate_sheet_id
    line = line.split(',')
    return dict(line=line, rate_sheet_id=rate_sheet_id)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rate_sheet_parse():
    import csv
    from dateutil.parser import parse
    from StringIO import StringIO

    rate_sheet_id = request.vars.rate_sheet_id
    rate_sheet = db.rate_sheet[rate_sheet_id] or redirect('index')
    data = StringIO(rate_sheet.tmp_import)
    rate_sheet.update_record(tmp_import = '')
    rate_sheet_reader = csv.reader(data, delimiter=',', quotechar='"')
    code_id, name_id, rate_id, effective_date_id, increment_id = -1, -1, -1, -1, -1
    def conv_int(s):
        try:
            x = int(s)
            return x
        except ValueError:
            return -1
    for key, value in request.vars.iteritems():
        if value == 'code': code_id = conv_int(key)
        if value == 'name': name_id = conv_int(key)
        if value == 'rate': rate_id = conv_int(key)
        if value == 'effective_date': effective_date_id = conv_int(key)
        if value == 'increment': increment_id = conv_int(key)

    for row in rate_sheet_reader:
        if len(row) == 0: continue
        code = row[code_id] if code_id != -1 else 'undefined'
        name = row[name_id] if name_id != -1 else 'undefined'
        rate = float(row[rate_id]) if rate_id != -1 else -1
        effective_date = parse(row[effective_date_id]) if effective_date_id != -1 else request.now #01/15/2015 00:00:00 +0000
        increment = conv_int(row[increment_id]) if increment_id != -1 else 1
        db.rate.update_or_insert((db.rate.code == code) & (db.rate.sheet == rate_sheet_id),
                                 sheet = rate_sheet_id,
                                 code = code,
                                 code_name = name,
                                 rate = float(rate),
                                 effective_date = effective_date,
                                 min_increment = increment)
    redirect(URL('default', 'rates', args=rate_sheet_id))


@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rates():
    rate_sheet_id = request.args(0) or redirect('index')
    rate_sheet = db.rate_sheet[rate_sheet_id]
    __check_rate_sheet(rate_sheet)
    db.rate.sheet.default = rate_sheet_id
    form = crud.update(db.rate, request.args(1), next=URL('default', 'rates', args=rate_sheet_id))
    rates = db(db.rate.sheet == rate_sheet_id).select()
    return dict(form=form, rate_sheet=rate_sheet, rates=rates)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def monitor():
    client_id = request.args(0) or redirect('index')
    client = db.client[client_id] or redirect('index')
    monitor_id = request.args(1)
    if monitor_id is not None:
        monitor = db.monitor[monitor_id]
        __check_monitor(monitor)
    db.monitor.client.default = client.id
    form = crud.update(db.monitor, request.args(1), next=URL('default', 'monitor', args=client.id))
    monitors = db(db.monitor.client == client.id).select()
    return dict(form=form, client=client, monitors=monitors)

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
