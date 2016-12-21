# -*- coding: utf-8 -*-
import uuid

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# app configuration made easy. Look inside private/appconfig.ini
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
myconf = AppConfig(reload=False)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(myconf.get('db.uri'),
             pool_size=myconf.get('db.pool_size'),
             migrate_enabled=myconf.get('db.migrate'),
             check_reserved=['all'],
             lazy_tables=True
    )
    session.connect(request, response, cookie_key=myconf.get('app.cookie_key'), compression_level=9)
    from gluon.custom_import import track_changes; track_changes(True)
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = ['*'] if request.is_local else []
# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

from gluon.tools import Auth, Service, PluginManager

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=myconf.get('host.names'))
#service = Service()
#plugins = PluginManager()

def check_client_prefix_uniqueness(form):
    edited_client_id = request.vars['edit']
    reseller = db.reseller[request.vars['reseller_id']]
    if not reseller:
        #something very wrong here, no point going further
        return
    rows = db((db.client.id != edited_client_id) & (db.client.reseller == db.reseller.id)).select(db.client.nb_prefix, db.reseller.gateways)
    existing_pairs = {}
    for row in rows:
        for gw in row.reseller.gateways:
            if gw not in existing_pairs:
                existing_pairs[gw] = []
            existing_pairs[gw].append(row.client.nb_prefix)

    nb_prefix = form.vars['nb_prefix']
    for gw in reseller.gateways:
        if gw in existing_pairs:
            for existing_prefix in existing_pairs[gw]:
                if nb_prefix.startswith(existing_prefix) or existing_prefix.startswith(nb_prefix):
                    form.errors.nb_prefix = T('prefix %s in coflict with existing %s') % (nb_prefix, existing_prefix)
                    return


def check_reseller_gateways(form):
    if len(form.vars.gateways) == 0:
        form.errors.gateways = T('please eneter at least one gateway')
    gws = form.vars.gateways if isinstance(form.vars.gateways, list) else [form.vars.gateways]
    for gw in gws:
        value, error = IS_IPV4()(gw)
        if error:
            form.errors.gateways = error
            return



from gluon.tools import Crud
crud = Crud(db)
crud.settings.auth = auth
crud.settings.formstyle = 'table3cols' #or 'table2cols' or 'divs' or 'ul'
crud.settings.create_onvalidation.client.append(check_client_prefix_uniqueness)
crud.settings.update_onvalidation.client.append(check_client_prefix_uniqueness)
crud.settings.create_onvalidation.reseller.append(check_reseller_gateways)
crud.settings.update_onvalidation.reseller.append(check_reseller_gateways)

# -------------------------------------------------------------------------
# create all tables needed by auth if not custom tables
# -------------------------------------------------------------------------
auth.define_tables(username=False, signature=True)

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = True
auth.settings.reset_password_requires_verification = True

# -------------------------------------------------------------------------
# other settings
# -------------------------------------------------------------------------
db._common_fields.append(auth.signature)

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)



db.define_table(
    'reseller',
    Field('name', 'string', unique=True, required=True, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'reseller.name')]),
    Field('unique_code', 'string',  required=True, unique=True, length=4, requires=[IS_MATCH('^\w{2,4}$'), IS_NOT_IN_DB(db, 'reseller.unique_code')], comment=T('internal unique identifyer (4 alpha-numeric characters)')),
    Field('currency', 'string', default='USD'),
    Field('status', 'string', requires=IS_IN_SET(('enabled', 'disabled')), default='enabled'),
    Field('gateways', 'list:string'),
    Field('address', 'text', length=1000),
    Field('tax_id', 'string'),
    Field('reg_id', 'string'),
    format='%(name)s'
)

db.define_table(
    'client',
    Field('name', 'string', unique=True, required=True, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'client.name')]),
    Field('unique_code', 'string',  required=True, unique=True, length=4, requires=[IS_MATCH('^\w{2,4}$'), IS_NOT_IN_DB(db, 'client.unique_code')], comment=T('internal unique identifyer (4 alpha-numeric characters)')),
    Field('reseller', 'reference reseller', readable=False, writable=False),
    Field('currency', 'string', default='USD'),
    Field('time_zone', 'string', default='Local'),
    Field('nb_prefix', 'string'),
    Field('status', 'string', requires=IS_IN_SET(('enabled', 'disabled')), default='enabled'),
    Field('active_rate_sheet', 'reference rate_sheet', readable=False, writable=False),
    Field('address', 'text', length=1000),
    Field('invoice_period', 'integer', required=True, default=1, requires=IS_IN_SET([i for i in range(1,60)]), widget=SQLFORM.widgets.options.widget),
    Field('payment_period', 'integer', required=True, default=1, requires=IS_IN_SET([i for i in range(1,60)]), widget=SQLFORM.widgets.options.widget),
    Field('tax_id', 'string'),
    Field('reg_id', 'string'),
    format='%(name)s'
)


db.define_table(
    'rate_sheet',
    Field('client', 'reference client', comment=T('select the client'), readable=False, writable=False),
    Field('name', 'string', unique=True, required=True, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'rate_sheet.name')]),
    Field('unique_code', 'string', required=True, unique=True, length=4, requires=[IS_MATCH('^\w{2,4}$'), IS_NOT_IN_DB(db, 'client.unique_code')], comment=T('internal unique identifyer (4 alpha-numeric characters)')),
    Field('effective_date', 'datetime', default=request.now),
    Field('direction', requires=IS_IN_SET(('outbound', 'inbound')), default='outbound'),
    Field('status', 'string', requires=IS_IN_SET(('enabled', 'disabled')), default='enabled'),
    format='%(name)s'
)


db.define_table(
    'rate',
    Field('sheet', 'reference rate_sheet', writable=False, readable=False),
    Field('code', 'string', required=True,  requires=IS_NOT_EMPTY()),
    Field('code_name', 'string', required=True, requires=IS_NOT_EMPTY()),
    Field('rate', 'double', required=True, requires=IS_NOT_EMPTY()),
    Field('min_increment', 'integer', default=1, comment=T('min debit duration in seconds')),
    Field('effective_date', 'datetime', default=request.now),
    format='%(code_name)s_%(code)s'
)

#ActionsId[0],Action[1],ExtraParameters[2],Filter[3],BalanceId[4],BalanceType[5],Directions[6],Categories[7],DestinationIds[8],RatingSubject[9],SharedGroup[10],ExpiryTime[11],TimingIds[12],Units[13],BalanceWeight[14],BalanceBlocker[15],BalanceDisabled[16],Weight[17]
db.define_table(
    'act',
    Field('client', 'reference client', required=True, readable=False, writable=False),
    Field('name', 'string', unique=False, required=True, requires=IS_NOT_EMPTY()),
    Field('action_type', 'string', default='log', requires=IS_IN_SET(('log',))),
    format='%(name)s'
)

#Tag[0],UniqueId[1],ThresholdType[2],ThresholdValue[3],Recurrent[4],MinSleep[5],ExpiryTime[6],ActivationTime[7],BalanceTag[8],BalanceType[9],BalanceDirections[10],BalanceCategories[11],BalanceDestinationIds[12],BalanceRatingSubject[13],BalanceSharedGroup[14],BalanceExpiryTime[15],BalanceTimingIds[16],BalanceWeight[17],BalanceBlocker[18],BalanceDisabled[19],StatsMinQueuedItems[20],ActionsId[21],Weight[22]
db.define_table(
    'action_trigger',
    Field('client', 'reference client', required=True, readable=False, writable=False),
    Field('name', 'string', unique=False, required=True, requires=IS_NOT_EMPTY()),
    Field('threshold_type', 'string', requires=IS_IN_SET(('min_asr', 'max_asr', 'min_acd', 'max_acd', 'min_tcd', 'max_tcd', 'min_acc', 'max_acc', 'min_tcc', 'max_tcc', 'min_ddc', 'max_ddc'))),
    Field('threshold_value', 'double'),
    Field('recurrent', 'boolean'),
    Field('min_sleep', 'string'),
    Field('min_queued_items', 'integer'),
    Field('act', 'reference act', required=True),
    format='%(name)s'
)

db.define_table(
    'stats',
    Field('client', 'reference client', required=True, readable=False, writable=False),
    Field('name', 'string', unique=True, required=True, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'stats.name')]),
    Field('queue_length', 'integer', required=True),
    Field('time_window', 'string', comment=T('cdr time window (s/m/h)')),
    Field('save_interval', 'string', default="60s", comment=T('save interval (s/m/h)')),
    Field('metrics', 'list:string', requires=IS_IN_SET(('ASR', 'ACD', 'TCD', 'ACC', 'TCC', 'PDD', 'DDC'), multiple=True)),
    Field('setup_interval', 'string', comment=T('cdr setup interval (start;end)')),
    Field('tors', 'list:string'),
    Field('cdr_hosts', 'list:string'),
    Field('cdr_sources', 'list:string'),
    Field('req_types', 'list:string'),
    Field('directions', 'list:string'),
    Field('tenants', 'list:string', readable=False, writable=False),
    Field('categories', 'list:string'),
    Field('accounts', 'list:string', readable=False, writable=False),
    Field('subjects', 'list:string'),
    Field('destination_ids', 'list:string'),
    Field('pdd_interval', 'string'),
    Field('usage_interval', 'string'),
    Field('suppliers', 'list:string'),
    Field('disconnect_causes', 'list:string'),
    Field('mediation_run_ids', 'list:string'),
    Field('rated_accounts', 'list:string'),
    Field('rated_subjects', 'list:string'),
    Field('cost_interval', 'string'),
    Field('triggers', 'list:string'),
    format='%(name)s'
)

db.define_table(
    'invoice',
    Field('statement_no', 'string', required=True, requires=IS_NOT_EMPTY()),
    Field('uuid', 'string', readable=False, writable=False, default=lambda:str(uuid.uuid4())),
    Field('from_client', 'reference client', required=True, readable=False, writable=False),
    Field('to_client', 'reference client', required=True, readable=False, writable=False),
    Field('status', 'string', requires=IS_IN_SET(('enabled', 'disabled', 'paid')), default='enabled'),
    Field('start_time', 'datetime'),
    Field('end_time', 'datetime'),
    Field('due_date', 'datetime'),
    Field('body', 'text', readable=False, writable=False),
    Field('hard_copy', 'upload'),
    format='%(statement_no)s'
)

#db.action_trigger.act.requires = IS_IN_DB(db(
#    (db.act.client == db.user_client.client_id) &
#    (auth.user_id == db.user_client.user_id)), db.act.id, '%(name)s')
