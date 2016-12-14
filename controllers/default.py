# -*- coding: utf-8 -*-

from gluon.tools import Crud
crud = Crud(db)
crud.settings.auth = auth
crud.settings.formstyle = 'table3cols' #or 'table2cols' or 'divs' or 'ul'

@auth.requires_login()
def index():
    if not auth.has_membership('admin') and not auth.has_membership('reseller') and auth.has_membership('client'):
        redirect(URL('default', 'clients'))
    return dict()

@auth.requires_membership('admin')
def resellers():
    form = crud.update(db.reseller, request.args(0), onaccept=give_reseller_owner_permissions)
    query = auth.accessible_query('read', db.reseller, auth.user.id)
    resellers = db(query).select()
    return dict(form=form, resellers=resellers)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('reseller') or auth.has_membership('client'))
def clients():
    form = None
    if auth.has_membership('admin') or auth.has_membership('reseller'):
        form = crud.update(db.client, request.args(0), onaccept=give_client_owner_permissions)
    query = auth.accessible_query('read', db.client, auth.user.id)
    clients = db(query).select()
    return dict(form=form, clients=clients)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rate_sheets():
    client_id=request.args(0) or redirect('index')
    client = db.client[client_id] or redirect('index')
    if not auth.has_membership(group_id='admin') and db((db.user_client.client_id == client_id) & (db.user_client.user_id == auth.user_id)).isempty():
        redirect(URL('user', 'not_autorized'))
    db.rate_sheet.client.default = client.id
    db.rate_sheet.client.readable = False
    db.rate_sheet.client.writable = False
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
        rate_shee_reader = csv.reader(form.vars.data.file, delimiter=',', quotechar='"')
        for row in rate_shee_reader:
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
    db.stats.tenants.default = [client.reseller.name]
    db.stats.accounts.default = [client.name]
    db.stats.client.default = client.id
    form = crud.update(db.stats, request.args(1), next=URL('default', 'stats', args=client.id))
    stats = db((db.user_client.user_id == auth.user_id) & (db.stats.client == client.id)).select(
                         join=db.user_client.on(db.stats.client == db.user_client.client_id),
                         groupby=db.stats.id)
    return dict(form=form, client=client, stats=stats)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def triggers():
    pass

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def actions():
    pass



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
