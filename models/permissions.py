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

    auth.add_permission(admin_group_id, 'create', db.action_trigger)
    auth.add_permission(admin_group_id, 'select', db.action_trigger)
    auth.add_permission(admin_group_id, 'read', db.action_trigger)
    auth.add_permission(admin_group_id, 'update', db.action_trigger)
    auth.add_permission(admin_group_id, 'delete', db.action_trigger)

    auth.add_permission(admin_group_id, 'create', db.act)
    auth.add_permission(admin_group_id, 'select', db.act)
    auth.add_permission(admin_group_id, 'read', db.act)
    auth.add_permission(admin_group_id, 'update', db.act)
    auth.add_permission(admin_group_id, 'delete', db.act)

    auth.add_permission(admin_group_id, 'create', db.invoice)
    auth.add_permission(admin_group_id, 'select', db.invoice)
    auth.add_permission(admin_group_id, 'read', db.invoice)
    auth.add_permission(admin_group_id, 'update', db.invoice)
    auth.add_permission(admin_group_id, 'delete', db.invoice)

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

    auth.add_permission(client_group_id, 'create', db.action_trigger)
    auth.add_permission(client_group_id, 'select', db.action_trigger)
    auth.add_permission(client_group_id, 'read', db.action_trigger)
    auth.add_permission(client_group_id, 'update', db.action_trigger)
    auth.add_permission(client_group_id, 'delete', db.action_trigger)

    auth.add_permission(client_group_id, 'create', db.act)
    auth.add_permission(client_group_id, 'select', db.act)
    auth.add_permission(client_group_id, 'read', db.act)
    auth.add_permission(client_group_id, 'update', db.act)
    auth.add_permission(client_group_id, 'delete', db.act)

    auth.add_permission(client_group_id, 'create', db.invoice)
    auth.add_permission(client_group_id, 'select', db.invoice)
    auth.add_permission(client_group_id, 'read', db.invoice)
    auth.add_permission(client_group_id, 'update', db.invoice)
    auth.add_permission(client_group_id, 'delete', db.invoice)

    auth.add_permission(reseller_group_id, 'create', db.client)

if myconf.get('app.first_run'):
    initialize_permissions()

def give_reseller_owner_permissions(form):
    reseller_id = form.vars.id
    group_id = auth.id_group('user_%s' % auth.user_id)

    auth.add_permission(group_id, 'read', db.reseller, reseller_id)
    auth.add_permission(group_id, 'select', db.reseller, reseller_id)
    auth.add_permission(group_id, 'update', db.reseller, reseller_id)
    auth.add_permission(group_id, 'delete', db.reseller, reseller_id)

    # give rights for all reseller clients
    reselllers_clients = db(db.client.reseller == reseller_id).select(db.client.id)
    for client in reselllers_clients:
        client_id = client.id
        auth.add_permission(group_id, 'read', db.client, client_id)
        auth.add_permission(group_id, 'select', db.client, client_id)
        auth.add_permission(group_id, 'update', db.client, client_id)
        auth.add_permission(group_id, 'delete', db.client, client_id)

def give_client_owner_permissions(form):
    client_id = form.vars.id
    group_id = auth.id_group('user_%s' % auth.user_id)

    auth.add_permission(group_id, 'read', db.client, client_id)
    auth.add_permission(group_id, 'select', db.client, client_id)
    auth.add_permission(group_id, 'update', db.client, client_id)

def get_user_resellers(user_id=None):
    users_resellers = {}
    user_ids = [user_id]
    if not user_id:
        user_ids = db(db.auth_user.id > 0).select(db.auth_user.id)
        user_ids = [u.id for u in user_ids]

    for uid in user_ids:
        query = auth.accessible_query('read', db.reseller, uid)
        resellers = db(query).select(db.reseller.id)
        users_resellers[uid] = [r.id for r in resellers]
    return users_resellers

def get_user_clients(user_id=None):
    users_clients = {}
    user_ids = [user_id]
    if not user_id:
        user_ids = db(db.auth_user.id > 0).select(db.auth_user.id)
        user_ids = [u.id for u in user_ids]

    for uid in user_ids:
        query = auth.accessible_query('read', db.client, uid)
        clients = db(query).select(db.client.id)
        users_clients[uid] = [r.id for r in clients]
    return users_clients


def accessible_reseller(reseller_id):
    return not db((auth.accessible_query('read', db.reseller, auth.user_id)) & (db.reseller.id == reseller_id)).isempty()

def accessible_client(client_id):
    return not db((auth.accessible_query('read', db.client, auth.user_id)) & (db.client.id == client_id)).isempty()

def __check_rate_sheet(rate_sheet):
    if not rate_sheet:
        raise HTTP(404, "Not found")
    # check  it belongs to a client owned by the current user
    if db(auth.accessible_query('read', db.client, auth.user_id) &
          (db.client.id == db.rate_sheet.client) &
          (db.rate_sheet.id == rate_sheet.id)).isempty():
        raise HTTP(403, "Not authorized")

def __check_stats(stats):
    if not stats:
        raise HTTP(404, "Not found")
    # check  it belongs to a client owned by the current user
    if db(auth.accessible_query('read', db.client, auth.user_id) &
          (db.client.id == db.stats.client) &
          (db.stats.id == stats.id)).isempty():
        raise HTTP(403, "Not authorized")

def __check_trigger(trigger):
    if not trigger:
        raise HTTP(404, "Not found")
    # check  it belongs to a client owned by the current user
    if db(auth.accessible_query('read', db.client, auth.user_id) &
          (db.client.id == db.action_trigger.client) &
          (db.action_trigger.id == trigger.id)).isempty():
        raise HTTP(403, "Not authorized")

def __check_action(action):
    if not action:
        raise HTTP(404, "Not found")
    # check  it belongs to a client owned by the current user
    if db(auth.accessible_query('read', db.client, auth.user_id) &
          (db.client.id == db.act.client) &
          (db.act.id == action.id)).isempty():
        raise HTTP(403, "Not authorized")
