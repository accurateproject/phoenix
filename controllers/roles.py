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
    if user.registration_key in ['disabled', 'blocked']:
        registration_key = ''
    user.update_record(registration_key=registration_key)
    return user.registration_key in ['disabled', 'blocked']

@auth.requires_membership('admin')
def _toggle_admin():
    user_id = request.args(0) or redirect('index')
    if auth.has_membership(user_id=user_id, role='admin'):
        auth.del_membership('admin', user_id)
    else:
        auth.add_membership('admin', user_id)
    return auth.has_membership(user_id=user_id, role='admin')

@auth.requires_membership('admin')
def _user_resellers():
    user = db.auth_user[request.args(0)] or redirect('index')
    user.update_record(resellers = request.vars['resellers[]'])
    return 'ok'

@auth.requires_membership('admin')
def _user_clients():
    user = db.auth_user[request.args(0)] or redirect('index')
    user.update_record(clients = request.vars['clients[]'])
    return 'ok'
