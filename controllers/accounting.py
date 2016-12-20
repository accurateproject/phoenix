import StringIO
from weasyprint import HTML
from datetime import datetime, timedelta, date
import time
import json
import accurate
import uuid

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def invoices():
    client_id=request.args(0) or redirect(URL('default', 'index'))
    client = db.client[client_id] or redirect(URL('default', 'index'))
    if not accessible_client(client_id):
        redirect(URL('user', 'not_autorized'))
    invoices = db((db.invoice.from_client == client_id) |
                  (db.invoice.to_client == client_id)).select()

    invoices_to_me, invoices_from_me = [],[]
    for invoice in invoices:
        if invoice.to_client == client.id:
            invoices_to_me.append(invoice)
        if invoice.from_client == client.id:
            invoices_from_me.append(invoice)

    now = datetime.now()

    invoice_id = request.args(1)
    possible_clients = db((db.client.reseller == client.reseller) &
        (db.client.id != client.id)).select(db.client.id, db.client.unique_code, db.client.name)
    possible_clients_list = [(row.id, row.name) for row in possible_clients]
    if invoice_id:
        form = crud.update(db.invoice, invoice_id, next=URL('accounting', 'invoices', args=client.id))
    else:
        form = SQLFORM.factory(
            Field('start_time', 'datetime', default=datetime(now.year, now.month, 1, 0, 0, 0)),
            Field('end_time', 'datetime', default=datetime(now.year, now.month, now.day, 0, 0, 0)),
            Field('to_client', 'string', requires=IS_IN_SET(possible_clients_list)),
            formstyle='table3cols'
        )
        if form.process().accepted:
            invoice_uuid = str(uuid.uuid4())
            db.invoice.insert(
                statement_no = '%s/%s'%(date.today().strftime('%Y%m%d'), ('%10.f' % time.time())[4:]),
                from_client = client.id,
                to_client = form.vars.to_client,
                due_date = datetime.now() + timedelta(days=client.payment_period),
                uuid = invoice_uuid,
                start_time = form.vars.start_time,
                end_time = form.vars.end_time,
            )
            redirect(URL('accounting', 'invoice', args=invoice_uuid))
        elif form.errors:
            response.flash = 'form has errors'
    return dict(form=form, client=client, invoices_to_me=invoices_to_me, invoices_from_me=invoices_from_me)

def invoice():
    invoice_uuid = request.args(0) or redirect(URL('default', 'index'))
    invoice = db(db.invoice.uuid == invoice_uuid).select().first()
    if not invoice:
        raise HTTP(404, "Not found")
    to_be_paid_date = invoice.created_on + timedelta(days=(invoice.to_client.payment_period or 1))

    # take only a page of cdrs at a time
    page = 0
    items_per_page=100
    params = {
        "run_ids": ["*default"],
        "tenants": [invoice.to_client.reseller.unique_code],
        "accounts": [invoice.to_client.unique_code],
        "answer_time_start": invoice.start_time.isoformat(),
        "answer_time_end": invoice.end_time.isoformat(),
        'limit': items_per_page+1,
        'offset': 0,
    }

    codes = {}

    if invoice.body or request.vars['force']:
        body = json.loads(invoice.body)
    else:
        while True:
            cdrs = []
            r = accurate.call("GetCdrs",  params)

            if r['error']:
                response.flash = r['error']
                return dict(invoice=invoice, to_be_paid_date=to_be_paid_date, body=body)
            else:
                cdrs = r['result']

            for cdr in cdrs:
                cdr = json.loads(cdr['CostDetails'])
                if len(cdr['Timespans']) == 0 or cdr['Cost'] <= 0:
                    continue # should it be logged?
                prefix = cdr['Timespans'][0]['MatchedPrefix']
                if prefix not in codes:
                    codes[prefix] = {'dest_id': '', 'rate': 0, 'calls': 0, 'seconds': 0, 'cost': 0}
                codes[prefix]['dest_id'] = cdr['Timespans'][0]['MatchedDestId']
                codes[prefix]['rate'] = cdr['Timespans'][0]['RateInterval']['Rating']['Rates'][0]['Value']
                codes[prefix]['calls'] += 1
                codes[prefix]['seconds'] += cdr['RatedUsage']
                codes[prefix]['cost'] += cdr['Cost']
            page += 1
            params['offset'] = page*items_per_page
            if len(cdrs) <= items_per_page:
                break
        total = 0
        for code, scdr in codes.iteritems():
            total += scdr['cost']
        body = dict(total = total, codes = codes)
    invoice.update_record(body=json.dumps(body))

    return dict(invoice=invoice, to_be_paid_date=to_be_paid_date, body=body)

def invoice_pdf():
    invoice_uuid = request.args(0) or redirect(URL('default', 'index'))
    stream = StringIO.StringIO()
    HTML(URL('accounting', 'invoice', args=invoice_uuid, scheme=True, host=True)).write_pdf(stream)
    response.headers['Content-Type'] = 'application/pdf'
    return stream.getvalue()
