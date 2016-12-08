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

        # add rate sheets

        auth.add_permission(reseller_group_id, 'create', db.client)
    else:
        admin_group_id = admin_group.id

    # make the first user admin
    first_user = myrecord = db(db.auth_user).select().first()
    if first_user != None:
        auth.add_membership(admin_group_id, first_user.id)


def give_client_owner_permissions(form):
    client_id = form.vars.id
    db.user_client.insert(user_id=auth.user_id, client_id = client_id)
    group_id = auth.id_group('user_%s' % auth.user_id)

    auth.add_permission(group_id, 'read', db.client, client_id)
    auth.add_permission(group_id, 'select', db.client, client_id)
    auth.add_permission(group_id, 'update', db.client, client_id)
    auth.add_permission(group_id, 'delete', db.client, client_id)


if myconf.get('app.first_run'):
    initialize_permissions()
