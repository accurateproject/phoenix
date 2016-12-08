

@auth.requires_membership('admin')
def manage_users():
    users = db(db.auth_user).select()
    all_resellers = db(db.reseller.status == 'enabled').select()
    all_clients = db(db.client.status == 'enabled').select()
    users_resellers = __get_user_resellers()
    users_clients = __get_user_clients()
    return locals()

@auth.requires_membership('admin')
def _toggle_disabled():
    user = db.auth_user[request.args(0)] or redirect('default', 'index')
    registration_key = 'disabled'
    if user.registration_key in ['disabled', 'blocked', 'pending']:
        registration_key = ''
    user.update_record(registration_key=registration_key)
    class_suffix = 'ok' if user.registration_key in ('disabled', 'blocked', 'pending') else 'remove'
    return SPAN(_class="glyphicon glyphicon-" + class_suffix)

@auth.requires_membership('admin')
def _toggle_admin():
    user_id = request.args(0) or redirect('default', 'index')
    if user_id == str(auth.user_id):
        return "don't de-admin yourself"
    if auth.has_membership(user_id=user_id, role='admin'):
        auth.del_membership('admin', user_id)
    else:
        auth.add_membership('admin', user_id)
    class_suffix = 'ok' if auth.has_membership(user_id=user_id, role='admin') else 'remove'
    return SPAN(_class="glyphicon glyphicon-"+ class_suffix)

@auth.requires_membership('admin')
def _user_resellers():
    new_reseller_list = request.vars['resellers[]'] or []
    if not isinstance(new_reseller_list, list): # make it a list
        new_reseller_list = [new_reseller_list]
    user_id = long(request.args(0)) or redirect('default', 'index')
    users_resellers = __get_user_resellers(user_id)

    # remove old links
    if user_id in users_resellers:
        for old_reseller_id in users_resellers[user_id]:
            if str(old_reseller_id) not in new_reseller_list:
                db((db.user_reseller.user_id == user_id) & (db.user_reseller.reseller_id == old_reseller_id)).delete()
    # add new links
    for reseller_id in new_reseller_list:
        db.user_reseller.update_or_insert((db.user_reseller.user_id == user_id) & (db.user_reseller.reseller_id == reseller_id),
            user_id=user_id, reseller_id=reseller_id)
    if new_reseller_list:
        auth.add_membership('reseller', user_id)
    else:
         auth.del_membership('reseller', user_id)
    return 'ok'

@auth.requires_membership('admin')
def _user_clients():
    new_client_list = request.vars['clients[]'] or []
    if not isinstance(new_client_list, list): # make it a list
        new_client_list = [new_client_list]
    user_id = long(request.args(0)) or redirect('default', 'index')
    group_id = auth.id_group('user_%s' % user_id)

    # remove old links
    users_clients = __get_user_clients(user_id)
    if user_id in users_clients:
        for old_client_id in users_clients[user_id]:
            if str(old_client_id) not in new_client_list:
                db((db.user_client.user_id == user_id) & (db.user_client.client_id == old_client_id)).delete()
                # remove the old clients right
                auth.del_permission(group_id, 'read', db.client, old_client_id)
                auth.del_permission(group_id, 'update', db.client, old_client_id)
                auth.del_permission(group_id, 'delete', db.client, old_client_id)
    # add new links
    for client_id in new_client_list:
        db.user_client.update_or_insert((db.user_client.user_id == user_id) & (db.user_client.client_id == client_id),
            user_id=user_id, client_id=client_id)
        auth.add_permission(group_id, 'read', db.client, client_id)
        auth.add_permission(group_id, 'update', db.client, client_id)
        auth.add_permission(group_id, 'delete', db.client, client_id)
    if new_client_list:
        auth.add_membership('client', user_id)
    else:
        auth.del_membership('client', user_id)
    return 'ok'
