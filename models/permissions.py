def initialize_permissions():
    # create groups
    admin_group = db(db.auth_group.role =='admin').select().first()
    if not admin_group:
        admin_group_id = auth.add_group('admin', 'application level administrator')
        reseller_group_id = auth.add_group('reseller', 'application level administrator')
        client_group_id = auth.add_group('client', 'application level administrator')

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

        auth.add_permission(admin_group_id, 'create', db.rate)
        auth.add_permission(admin_group_id, 'select', db.rate)
        auth.add_permission(admin_group_id, 'read', db.rate)
        auth.add_permission(admin_group_id, 'update', db.rate)
        auth.add_permission(admin_group_id, 'delete', db.rate)

        auth.add_permission(reseller_group_id, 'create', db.client)
        auth.add_permission(reseller_group_id, 'select', db.client)
        auth.add_permission(client_group_id, 'create', db.rate)
        auth.add_permission(client_group_id, 'select', db.rate)
    else:
        admin_group_id = admin_group.id

    # make the first user admin
    first_user = myrecord = db(db.auth_user).select().first()
    if first_user != None:
        auth.add_membership(admin_group_id, first_user.id)


def give_client_owner_permission(form):
    client_id = form.vars.id
    group_id = auth.id_group('user_%s' % auth.user.id)
    auth.add_permission(group_id, 'read', db.client)
    auth.add_permission(group_id, 'update', db.client, client_id)
    auth.add_permission(group_id, 'delete', db.client, client_id)


def give_rate_owner_permission(form):
    rate_id = form.vars.id
    group_id = auth.id_group('user_%s' % auth.user.id)
    auth.add_permission(group_id, 'read', db.rate)
    auth.add_permission(group_id, 'update', db.rate, rate_id)
    auth.add_permission(group_id, 'delete', db.rate, rate_id)

if myconf.get('app.first_run'):
    initialize_permissions()
