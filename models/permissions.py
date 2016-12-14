def initialize_permissions():
    # create groups
    admin_group = db(db.auth_group.role =='admin').select().first()
    if not admin_group:
        admin_group_id = auth.add_group('admin', 'application level administrator')
        reseller_group_id = auth.add_group('reseller', 'application level administrator')
        client_group_id = auth.add_group('client', 'application level administrator')
    else:
        admin_group_id = admin_group.id
        reseller_group_id = db(db.auth_group.role =='reseller').select().first().id
        client_group_id = db(db.auth_group.role =='client').select().first().id


    # make the first user admin
    first_user = myrecord = db(db.auth_user).select().first()
    if first_user != None:
        auth.add_membership(admin_group_id, first_user.id)

    auth.add_permission(admin_group_id, 'create', db.reseller)
    auth.add_permission(admin_group_id, 'select', db.reseller)
    auth.add_permission(admin_group_id, 'read', db.reseller)
    auth.add_permission(admin_group_id, 'update', db.reseller)
    auth.add_permission(admin_group_id, 'delete', db.reseller)

    auth.add_permission(admin_group_id, 'create', db.client)
    auth.add_permission(admin_group_id, 'select', db.client)
    auth.add_permission(admin_group_id, 'read', db.client)
    auth.add_permission(admin_group_id, 'update', db.client)
    auth.add_permission(admin_group_id, 'delete', db.client)

    auth.add_permission(admin_group_id, 'create', db.rate_sheet)
    auth.add_permission(admin_group_id, 'select', db.rate_sheet)
    auth.add_permission(admin_group_id, 'read', db.rate_sheet)
    auth.add_permission(admin_group_id, 'update', db.rate_sheet)
    auth.add_permission(admin_group_id, 'delete', db.rate_sheet)

    auth.add_permission(admin_group_id, 'create', db.rate)
    auth.add_permission(admin_group_id, 'select', db.rate)
    auth.add_permission(admin_group_id, 'read', db.rate)
    auth.add_permission(admin_group_id, 'update', db.rate)
    auth.add_permission(admin_group_id, 'delete', db.rate)

    auth.add_permission(admin_group_id, 'create', db.stats)
    auth.add_permission(admin_group_id, 'select', db.stats)
    auth.add_permission(admin_group_id, 'read', db.stats)
    auth.add_permission(admin_group_id, 'update', db.stats)
    auth.add_permission(admin_group_id, 'delete', db.stats)

    auth.add_permission(admin_group_id, 'create', db.cc_trigger)
    auth.add_permission(admin_group_id, 'select', db.cc_trigger)
    auth.add_permission(admin_group_id, 'read', db.cc_trigger)
    auth.add_permission(admin_group_id, 'update', db.cc_trigger)
    auth.add_permission(admin_group_id, 'delete', db.cc_trigger)

    auth.add_permission(admin_group_id, 'create', db.cc_action)
    auth.add_permission(admin_group_id, 'select', db.cc_action)
    auth.add_permission(admin_group_id, 'read', db.cc_action)
    auth.add_permission(admin_group_id, 'update', db.cc_action)
    auth.add_permission(admin_group_id, 'delete', db.cc_action)

    auth.add_permission(client_group_id, 'create', db.rate_sheet)
    auth.add_permission(client_group_id, 'select', db.rate_sheet)
    auth.add_permission(client_group_id, 'read', db.rate_sheet)
    auth.add_permission(client_group_id, 'update', db.rate_sheet)
    auth.add_permission(client_group_id, 'delete', db.rate_sheet)

    auth.add_permission(client_group_id, 'create', db.rate)
    auth.add_permission(client_group_id, 'select', db.rate)
    auth.add_permission(client_group_id, 'read', db.rate)
    auth.add_permission(client_group_id, 'update', db.rate)
    auth.add_permission(client_group_id, 'delete', db.rate)

    auth.add_permission(client_group_id, 'create', db.stats)
    auth.add_permission(client_group_id, 'select', db.stats)
    auth.add_permission(client_group_id, 'read', db.stats)
    auth.add_permission(client_group_id, 'update', db.stats)
    auth.add_permission(client_group_id, 'delete', db.stats)

    auth.add_permission(client_group_id, 'create', db.cc_trigger)
    auth.add_permission(client_group_id, 'select', db.cc_trigger)
    auth.add_permission(client_group_id, 'read', db.cc_trigger)
    auth.add_permission(client_group_id, 'update', db.cc_trigger)
    auth.add_permission(client_group_id, 'delete', db.cc_trigger)

    auth.add_permission(client_group_id, 'create', db.cc_action)
    auth.add_permission(client_group_id, 'select', db.cc_action)
    auth.add_permission(client_group_id, 'read', db.cc_action)
    auth.add_permission(client_group_id, 'update', db.cc_action)
    auth.add_permission(client_group_id, 'delete', db.cc_action)

    auth.add_permission(reseller_group_id, 'create', db.client)

def give_reseller_owner_permissions(form):
    reseller_id = form.vars.id
    db.user_reseller.insert(user_id=auth.user_id, reseller_id = reseller_id)

def give_client_owner_permissions(form):
    client_id = form.vars.id
    db.user_client.insert(user_id=auth.user_id, client_id = client_id)
    group_id = auth.id_group('user_%s' % auth.user_id)

    auth.add_permission(group_id, 'read', db.client, client_id)
    auth.add_permission(group_id, 'select', db.client, client_id)
    auth.add_permission(group_id, 'update', db.client, client_id)
    auth.add_permission(group_id, 'delete', db.client, client_id)

def get_user_resellers(user_id=None):
    users_resellers = {}
    urs = users_and_resellers if not user_id else users_and_resellers(db.auth_user.id == user_id)
    for ur in urs.select():
        if ur.auth_user.id not in users_resellers:
            users_resellers[ur.auth_user.id]=[]
        users_resellers[ur.auth_user.id].append(ur.reseller.id)
    return users_resellers

def get_user_clients(user_id=None):
    users_clients = {}
    ucs = users_and_clients if not user_id else users_and_clients(db.auth_user.id == user_id)
    for uc in ucs.select():
        if uc.auth_user.id not in users_clients:
            users_clients[uc.auth_user.id]=[]
        users_clients[uc.auth_user.id].append(uc.client.id)
    return users_clients


if myconf.get('app.first_run'):
    initialize_permissions()
