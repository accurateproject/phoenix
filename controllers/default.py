# -*- coding: utf-8 -*-

from gluon.tools import Crud
crud = Crud(db)
crud.settings.auth = auth

@auth.requires_login()
def index():
    return dict()

@auth.requires_membership('admin')
def resellers():
    form = crud.create(db.reseller, onaccept=give_reseller_owner_permissions)
    query = auth.accessible_query('read', db.reseller, auth.user.id)
    resellers = db(query).select()
    return dict(form=form, resellers=resellers)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('reseller'))
def clients():
    form = crud.create(db.client, onaccept=give_client_owner_permissions)
    query = auth.accessible_query('read', db.client, auth.user.id)
    clients = db(query).select()
    return dict(form=form, clients=clients)

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def rate_sheets():
    form = SQLFORM.factory(db.rate_sheet)
    # form process
    user = db.auth_user[auth.user_id]
    rate_sheets = db(db.rate_sheet.client.belongs(user.clients)).select()
    return dict(form=form, rate_sheets=rate_sheets)


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
