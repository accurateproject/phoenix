@auth.requires_membership('admin')
def manage_users():
    users = db(db.auth_user).select()
    all_resellers = db(db.reseller.status == 'enabled').select()
    all_clients = db(db.client.status == 'enabled').select()
    return locals()

@auth.requires_membership('admin')
def _toggle_disabled():
    user = db.auth_user[request.args(0)] or redirect('index')
    registration_key = 'disabled'
    if user.registration_key in ['disabled', 'blocked', 'pending']:
        registration_key = ''
    user.update_record(registration_key=registration_key)
    class_suffix = 'ok' if user.registration_key in ('disabled', 'blocked', 'pending') else 'remove'
    return SPAN(_class="glyphicon glyphicon-" + class_suffix)

@auth.requires_membership('admin')
def _toggle_admin():
    user_id = request.args(0) or redirect('index')
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
    user = db.auth_user[request.args(0)] or redirect('index')
    user.update_record(resellers = new_reseller_list)
    if user.resellers:
        auth.add_membership('reseller', user.id)
    else:
         auth.del_membership('reseller', user.id)
    return 'ok'

@auth.requires_membership('admin')
def _user_clients():
    new_client_list = request.vars['clients[]'] or []
    user = db.auth_user[request.args(0)] or redirect('index')
    group_id = auth.id_group('user_%s' % user.id)
    if user.clients:
        for old_client_id in user.clients:
            if str(old_client_id) not in new_client_list:
                # remove the old clients right
                auth.del_permission(group_id, 'read', db.client, old_client_id)
                auth.del_permission(group_id, 'update', db.client, old_client_id)
                auth.del_permission(group_id, 'delete', db.client, old_client_id)
    user.update_record(clients = new_client_list)
    if user.clients:
        auth.add_membership('client', user.id)
        for client_id in user.clients:
            auth.add_permission(group_id, 'read', db.client, client_id)
            auth.add_permission(group_id, 'update', db.client, client_id)
            auth.add_permission(group_id, 'delete', db.client, client_id)
    else:
        auth.del_membership('client', user.id)
    return 'ok'
