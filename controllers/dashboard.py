import accurate

@auth.requires(auth.has_membership(group_id='admin'))
def status():
    session.forget(response)
    return accurate.call("Responder.Status", dict(ShowBytes=True))

@auth.requires(auth.has_membership(group_id='admin'))
def index():
    return dict()
