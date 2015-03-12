from gluon.custom_import import track_changes; track_changes(True) #reload modules on change
from gluon.tools import Auth
from gluon import current
from gluon.contrib.login_methods.email_auth import email_auth
from string import replace

import datetime

exportOptions=dict(
            csv_with_hidden_cols=False,
            xml=False,
            html=False,
            csv=False,
            json=False,
            tsv_with_hidden_cols=False,
            tsv=False)

response.generic_patterns = ['*']

#Define your DB connection string here
db = DAL('mysql://',pool_size=10,check_reserved=['all'], migrate=False,lazy_tables=True)
current.db = db #allow db access in modules via current

auth = Auth(db, signature=False)
#auth.messages.label_username="E-mail"
auth.settings.create_user_groups = False

def email_auth_usp(user, password):
    a = email_auth("smtp.usp.br:587", "", False)
    user = replace(user,"@usp.br","")
    return a(user, password)

auth.settings.login_methods.append(email_auth_usp)

auth.settings.extra_fields['auth_user']= []
auth.settings.actions_disabled=['register','change_password','request_reset_password','retrieve_username']
auth.define_tables(signature=False)

db.auth_user._format='%(first_name)s %(last_name)s'
db.auth_user._singular = T('User')

mail = auth.settings.mailer
mail.settings.server = 'smtp.usp.br:587'
mail.settings.sender = 'servico@iqsc.usp.br'
mail.settings.login = 'servico@iqsc.usp.br:od4qvji5'
current.mail = mail

current.admin = auth.has_membership(role='Admin')
current.advisor = auth.has_membership(role='Advisor')
current.auth = auth
current.url_return = lambda req: URL(req.controller, req.function, args=req.args, vars=req.vars)

represent_name=lambda id, r=0: '%s %s' % (db.auth_user(id).first_name, db.auth_user(id).last_name) if db.auth_user(id) else T('None')

db.define_table(
    'program',
    Field('name', length=20, label=T('Program')),
    Field('duration', 'integer', label=T('Duration')),
    singular=T('Program'),
    plural=T('Programs'),
    format='%(name)s'
)

advisors_only_query = db((db.auth_group.id == db.auth_membership.group_id) & (db.auth_group.role ==  'Advisor') & (db.auth_membership.user_id == db.auth_user.id));
req_advisors = IS_NULL_OR(IS_IN_DB (advisors_only_query,'auth_user.id','%(first_name)s %(last_name)s',zero=T('Not applicable')));
posgrad_program = IS_IN_DB (db, 'program.id', zero=T('Must choose'));

#represent=lambda id: '%s %s' % (db.auth_user(id).first_name, db.auth_user(id).last_name)
#represent=lambda id, r: db.program(id).name)

def auth_user_delete_hook(s):
    for f in s.select():
        db(db.enrollment.student == f.id).delete()
        db(db.enrollment.advisor == f.id).delete()
        db(db.enrollment.reviewer == f.id).update(reviewer=None)
db.auth_user._after_delete.append(auth_user_delete_hook)


db.define_table(
    'enrollment',
    Field('student', 'reference auth_user', label=T('Student'), required=True),
    Field('advisor', 'reference auth_user', required=True, label=T('Advisor'), requires=req_advisors, represent=represent_name),
    Field('reviewer', 'reference auth_user', required=False, label=T('Default Reviewer'), requires=req_advisors, represent=represent_name),
    Field('program', 'reference program', label=T('Program'), required=True),
    Field('start_date', type='date', label=T('Start Date')),
    Field('end_date', type='date', label=T('End Date')),
    Field('work_title', length=200, label=T('Work Title')),
    Field('work_abstract', 'text', label=T('Abstract')),
    Field('project_document', 'upload', label=T('Project Document'),
          requires=IS_EMPTY_OR(IS_UPLOAD_FILENAME(extension="(pdf|doc|docx)")), required=False, autodelete=True),
    Field('is_active', 'boolean', label=T('Active'), default=False),
    Field('max_date', type='date', label=T('Max Date'), compute=lambda r: (r.start_date + datetime.timedelta(db.program(r.program).duration*365/12)) if r.start_date else None),
    singular=T('Enrollment'),
    plural=T('Enrollments'),
    format=lambda r: r.program.name + ' - ' + (r.advisor.first_name if r.advisor else T('None'))+ '/' + r.student.first_name
)
def enrollment_update_hook(s,f):
    ids = [r.id for r in s.select()]
    for id in ids:
        enrollment = db.enrollment(id)
        users = []
        if enrollment.advisor: users.append(enrollment.advisor)
        if enrollment.student: users.append(enrollment.student)
        for user in users:
            if user.email:
                mail.send(to=[user.email], bcc=['report@mailinator.com'],
                          subject=response.title + ': ' + T('Enrollment information updated'),
                          reply_to='spgr@iqsc.usp.br',
                          message=response.render("mail/student_enrollment.html", locals())
                      )

db.enrollment._after_update.append(enrollment_update_hook)
def enrollment_delete_hook(s):
    for f in s.select():
        db(db.submission.enrollment == f.id).delete()
db.enrollment._after_delete.append(enrollment_delete_hook)

relative_date_set = {'ingress': T('Date of Ingress'), 'calendar': T('School Calendar')}
db.define_table(
    'document_type',
    Field('name', length=40, label=T('Document Type')),
    Field('is_active', 'boolean', label=T('Active')),
    Field('program', 'reference program', label=T('Program'), required=True),
    Field('description', 'text', label=T('Type Description')),
    Field('relative_date', label=T('Relative Date'), required=True,
          requires=IS_IN_SET(relative_date_set, zero=T('Choose')),
          represent=lambda value, row: relative_date_set.get(value,None)),
    Field('period', 'integer', label=T('Period (months)'), required=True, default=0, requires=IS_INT_IN_RANGE(0, 65)),
    Field('tolerance', 'integer', label=T('Tolerance (days)'), required=True, default=0, requires=IS_INT_IN_RANGE(-360, 360)),
    Field('recurrent', 'boolean', label=T('Recurrent')),
    Field('review_form', 'json', label=T('Review Form'), readable=False, writable=False),
    singular=T('Document Type'),
    plural=T('Document Types'),
    format='%(name)s'
)

db.define_table(
    'artifact',
    Field('document_type', 'reference document_type', label=T('Document Type'), required=True),
    Field('name', length=40, label=T('Artifact Name'), required=True),
    Field('recommended_content', 'text', label=T('Recommended Content'), required=True),
    Field('file_types', 'list:string', label=T('File Types'), requires=IS_IN_SET(sorted([
                              ('txt', T('Text Files') + ' (txt)'),
                              ('pdf', T('Adobe PDF') + ' (pdf)'),
                              ('jpg,jpeg,png,gif', T('Image Files') + '(jpg,jpeg,png,gif)'),
                              ('doc,docx', T('Microsoft Word') + ' (doc/docx)')
                              ]), multiple=True)),
    Field('required', 'boolean', label=T('Required')),
    Field('multiple', 'boolean', label=T('Allow Multiple')),
    singular=T('Artifact'),
    plural=T('Artifacts'),
    format='%(name)s'
)

db.define_table(
    'submission_status',
    Field('name', 'string', length=20, required=True, label=T('Status')),
    Field('description', 'string', label=T('Description')),
    Field('requires', 'string', label=T('action')),
    Field('icon', 'string', length=20, label=T('Icon')),
    Field('who', 'string', length=20, label=T('Who')),
    format=lambda r: T(r.name)
)

validate_status_set = dict((st,T(current.status_details[st]['name'])) for st in current.status_details)
db.define_table(
    'submission',
    Field('enrollment', 'reference enrollment', label=T('Enrollment'), required=True),
    Field('document_type', 'reference document_type', label=T('Document Type'), required=True),
    Field('submission_date', 'datetime', label=T('Submission Date'), required=True),
    #Field('closed', 'boolean', label=T('Closed'), default=False),
    Field('status', 'integer', label=T('Status'), default=1, required=True,
          requires=IS_IN_SET(validate_status_set, zero=T('Choose')),
          represent=lambda value, row:
              (str(value) if value else '0') + ' - ' + str(validate_status_set.get(value,T('undefined')))),
    Field('reviewer', 'reference auth_user', label=T('Reviewer'), requires=req_advisors, represent=represent_name),
    Field('review_form', 'json', label=T('Review Form'), readable=False, writable=False),
    singular=T('Submission'),
    plural=T('Submissions'),
    format=lambda r: r.document_type.name + '/' + str(r.submission_date.date())
)
def submission_delete_hook(s):
    for f in s.select():
        db(db.submission_log.submission == f.id).delete()
        db(db.submitted_artifact.submission == f.id).delete()
db.submission._after_delete.append(submission_delete_hook)

db.define_table(
    'submission_log',
    Field('author', 'reference auth_user', label=('Author'), default=auth.user_id),
    Field('role', 'string', label=('Role')),
    Field('submission', 'reference submission', label=('Submission')),
    Field('automatic', label=('Auto-generated'), compute=lambda r: r.author == None ),
    Field('event_date', 'datetime', label=T('Event Date'), required=True, default=request.now),
    Field('content_text', 'text', required=True, label=T('Comment')),
    Field('status', 'integer', label=('Status')),
    singular=T('Submission Log'),
    plural=T('Submission Logs'),
    format=lambda r: str(r.event_date) + '/' + r.author if not r.automatic else T('Auto')
)
def submission_log_hook(f,id):
    log = db.submission_log(id)
    status = current.status_details[f['status']].data if f.get('status') else None
    if not status: return

    users = []
    if status['who'] == 'Advisor':
        users = [log.submission.enrollment.advisor]
    elif status['who'] == 'Student':
        users = [log.submission.enrollment.student]
    elif not status['who']:
        users = [log.submission.enrollment.advisor,
                 log.submission.enrollment.student]

    for user in users:
        if user.email:
            mail.send(to=[user.email], bcc=['report@mailinator.com'],
                      subject=response.title + ': ' + T('Submission status changed'),
                      reply_to='spgr@iqsc.usp.br',
                      message=response.render("mail/status.html", locals())
                  )

db.submission_log._after_insert.append(submission_log_hook)

db.define_table(
    'submitted_artifact',
    Field('submission', 'reference submission', label=T('Submission'), required=True),
    Field('artifact', 'reference artifact', label=T('Artifact'), required=True),
    Field('item_no', 'integer', default=1, label=T('Item')),
    Field('item_version', 'integer', default=1, label=T('Version')),
    Field('item_file', 'upload', label=T('File'), required=True, requires=IS_LENGTH(2097152, 1024), autodelete=True),
    Field('item_date', 'datetime', label=T('Submission Date'), required=True),
    singular=T('Submitted Artifact'),
    plural=T('Submitted Artifacts')
)
