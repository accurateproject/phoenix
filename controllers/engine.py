import accurate

def status():
    return raccurate.call("Responder.Status")

def accounts():
    return accurate.call("GetAccounts",  dict(tenant = 'Generator'))

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def activate_rate_sheet():
    rate_sheet_id = request.args(0) or redirect('index')
    rate_sheet = db.rate_sheet[rate_sheet_id]
    __check_rate_sheet(rate_sheet)
    rs_rates = db(db.rate.sheet == rate_sheet.id).select()

    response = accurate.rate_sheet_to_tp(rate_sheet, rs_rates)
    response +=  accurate.account_to_tp(rate_sheet)
    response +=  accurate.activate_tpid(rate_sheet.name + "_tp")
    response +=  accurate.activate_tpid(rate_sheet.name + "_acc")

    rate_sheet.client.active_rate_sheet = rate_sheet.id
    rate_sheet.client.update_record()
    return response


@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def activate_stats():
    client_id = request.args(0) or redirect('index')
    client = db.client[client_id]
    if not auth.has_membership(group_id='admin') and db((db.user_client.client_id == client.id) & (db.user_client.user_id == auth.user_id)).isempty():
        redirect(URL('user', 'not_autorized'))

    stats = db(db.stats.client == client_id).select()
    response = accurate.stats_to_tp(client, stats)
    response +=  accurate.activate_tpid(client.name + "_stats")

    return response
