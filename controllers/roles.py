users_and_groups = db((db.auth_user.id == db.auth_membership.user_id) & (db.auth_group.id == db.auth_membership.group_id))

def __get_groups(id=None):
    groups = {}
    uags = users_and_groups if id is None else users_and_groups(db.auth_user.id == id)
    for uag in uags.select():
        if uag.auth_user.id not in groups:
            groups[uag.auth_user.id] = []
        groups[uag.auth_user.id].append(uag.auth_group.role)
    return groups

@auth.requires_membership('admin')
def manage_users():
    users = db(db.auth_user).select()
    groups = __get_groups()
    return locals()


@auth.requires_membership('admin')
def manage_user():
    user_id = request.args(0) or redirect('index')
    user = db.auth_user[user_id] or redirect('index')
    groups = __get_groups(user_id)
    return dict(user=user, groups=groups)
