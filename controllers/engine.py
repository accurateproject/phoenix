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
    response += accurate.activate_rate_sheet(rate_sheet)

    rate_sheet.client.active_rate_sheet = rate_sheet.id
    rate_sheet.client.update_record()
    return response
