# -*- coding: utf-8 -*-

from gluon.tools import Crud
crud = Crud(db)
crud.settings.auth = auth
crud.settings.formstyle = 'table3cols' #or 'table2cols' or 'divs' or 'ul'

@auth.requires_login()
def index():
    return dict()

@auth.requires_membership('admin')
def resellers():
    form = crud.update(db.reseller, request.args(0), onaccept=give_reseller_owner_permissions)
    query = auth.accessible_query('read', db.reseller, auth.user.id)
    resellers = db(query).select()
    return dict(form=form, resellers=resellers)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('reseller'))
def clients():
    form = crud.update(db.client, request.args(0), onaccept=give_client_owner_permissions)
    query = auth.accessible_query('read', db.client, auth.user.id)
    clients = db(query).select()
    return dict(form=form, clients=clients)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rate_sheets():
    form = crud.update(db.rate_sheet, request.args(0))
    rate_sheets = db(db.user_client.user_id == auth.user_id).select(
                         join=db.user_client.on(db.rate_sheet.client == db.user_client.client_id),
                         groupby=db.rate_sheet.id)
    return dict(form=form, rate_sheets=rate_sheets)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def client_rate_sheets():
    client_id=request.args(0) or redirect('index')
    client = db.client[client_id] or redirect('index')
    if not auth.has_membership(group_id='admin') and db((db.user_client.client_id == client_id) & (db.user_client.user_id == auth.user_id)).isempty():
        redirect(URL('user', 'not_autorized'))
    db.rate_sheet.client.default = client_id
    db.rate_sheet.client.readable = False
    db.rate_sheet.client.writable = False
    form = crud.update(db.rate_sheet, request.args(1))
    rate_sheets = db(db.rate_sheet.client == client_id).select()
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
