import StringIO
from weasyprint import HTML
from datetime import datetime, timedelta, date
import time
import json
import accurate
import uuid

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def invoices():
    client_id=request.args(0) or redirect('default', 'index')
    client = db.client[client_id] or redirect('default', 'index')
    if not accessible_client(client_id):
        redirect(URL('user', 'not_autorized'))
    invoices = db(db.invoice.client == client_id).select()
    now = datetime.now()

    invoice_id = request.args(1)
    if invoice_id:
        form = crud.update(db.invoice, invoice_id, next=URL('accounting', 'invoices', args=client.id))
    else:
        form = SQLFORM.factory(
            Field('start_time', 'datetime', default=datetime(now.year, now.month, 1, 0, 0, 0)),
            Field('end_time', 'datetime', default=datetime(now.year, now.month, now.day, 0, 0, 0)),
            formstyle='table3cols'
        )
        if form.process().accepted:
            invoice_uuid = str(uuid.uuid4())
            db.invoice.insert(
                statement_no = '%s/%s'%(date.today().strftime('%Y%m%d'), ('%10.f' % time.time())[4:]),
                client = client.id,
                due_date = datetime.now() + timedelta(days=client.payment_period),
                uuid = invoice_uuid,
                start_time = form.vars.start_time,
                end_time = form.vars.end_time,
            )
            redirect(URL('accounting', 'invoice', args=invoice_uuid))
        elif form.errors:
            response.flash = 'form has errors'
    return dict(form=form, client=client, invoices=invoices)

def invoice():
    invoice_uuid = request.args(0) or redirect('default', 'index')
    invoice = db(db.invoice.uuid == invoice_uuid).select().first()
    to_be_paid_date = invoice.created_on + timedelta(days=(invoice.client.payment_period or 1))

    # take only a page of cdrs at a time
    page = 0
    items_per_page=100
    params = {
        "run_ids": ["*default"],
        "tenants": [invoice.client.reseller.unique_code],
        "accounts": [invoice.client.unique_code],
        "answer_time_start": invoice.start_time.isoformat(),
        "answer_time_end": invoice.end_time.isoformat(),
        'limit': items_per_page+1,
        'offset': 0,
    }

    codes = {}

    if invoice.body:
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

def pdf_me():
    s = StringIO.StringIO()
    HTML(request.env.http_referer).write_pdf(s)
    response.headers['Content-Type'] = 'application/pdf'
    return s.getvalue()
