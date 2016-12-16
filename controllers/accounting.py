import StringIO
from weasyprint import HTML
from datetime import datetime, timedelta

@auth.requires(auth.has_membership(group_id='admin') or auth.has_membership('client'))
def invoices():
    client_id=request.args(0) or redirect('default', 'index')
    client = db.client[client_id] or redirect('default', 'index')
    if not auth.has_membership(group_id='admin') and db((db.user_client.client_id == client_id) & (db.user_client.user_id == auth.user_id)).isempty():
        redirect(URL('user', 'not_autorized'))
    invoices = db(db.invoice.client == client_id).select()
    now = datetime.now()

    invoice_id = request.args(1)
    if invoice_id:
        form = crud.update(db.invoice, invoice_id, next=URL('accounting', 'invoices', args=client.id))
    else:
        form = SQLFORM.factory(
            Field('start_date', 'datetime', default=datetime(now.year, now.month, 1, 0, 0, 0)),
            Field('end_date', 'datetime', default=datetime(now.year, now.month, now.day, 0, 0, 0)),
            formstyle='table3cols'
        )
    return dict(form=form, client=client, invoices=invoices)

def invoice():
    invoice_uuid = request.args(0) or redirect('default', 'index')
    invoice = db(db.invoice.uuid == invoice_uuid).select().first()
    to_be_paid_date = invoice.created_on + timedelta(days=(invoice.client.payment_period or 1))
    return dict(invoice=invoice, to_be_paid_date=to_be_paid_date)

def pdf_me():
    s = StringIO.StringIO()
    HTML(request.env.http_referer).write_pdf(s)
    response.headers['Content-Type'] = 'application/pdf'
    return s.getvalue()
