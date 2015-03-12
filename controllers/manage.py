# coding: utf8
# try something like
from components import *

def gen_error(txt): return dict(err = DIV(B(T('Error')) + ': ' + txt + '!',_class='alert alert-danger'))

@auth.requires_membership('Admin')
def index(): return dict(message="hello from usuario.py")

@auth.requires_membership('Admin')
def data():
    response.view = 'generic.html'
    table = request.args(0)
    if not table in db.tables(): redirect(URL('error'))
    grid = SQLFORM.smartgrid(db[table],args=request.args[:1], exportclasses=exportOptions,showbuttontext=False,)
    return dict(grid=grid)

@auth.requires_membership('Admin')
def user():
    response.view = 'generic.html'
    db.auth_user.email.comment = '@usp.br ' + T('and') + ' @iqsc.usp.br ' + T('users may login with their e-mail password')
    db.auth_user.password.comment = T('for such cases, input any password as it will be overwrited on first login')
    grid = SQLFORM.smartgrid(db.auth_user, user_signature=False, exportclasses=exportOptions,showbuttontext=False,
                             linked_tables=['auth_membership', 'auth_event', 'enrollment', 'submission','submitted_artifact'])
    return dict(grid=grid)

@auth.requires_membership('Admin')
def group():
    response.view = 'generic.html'
    grid = SQLFORM.smartgrid(db.auth_group, user_signature=False, showbuttontext=False,
                             linked_tables=['auth_membership'])
    return dict(grid=grid)

@auth.requires_membership('Admin')
def program():
    response.view = 'generic.html'
    grid = SQLFORM.smartgrid(db.program, user_signature=False, exportclasses=exportOptions, showbuttontext=False)
    return dict(grid=grid)

@auth.requires_membership('Admin')
def enrollment():
    response.view = 'generic.html'
    grid = SQLFORM.grid(db.enrollment, user_signature=False, exportclasses=exportOptions, showbuttontext=False,
                        links=[dict(header=T('Status'),body=enrollment_status)],
                        onupdate=lambda f: build_action_menu(response.menu, True))
    return dict(grid=grid)

@auth.requires_membership('Admin')
def pending_enrollment():
    response.view = 'generic.html'
    db.enrollment.advisor.required = True
    if 'edit' in request.args:
        db.enrollment.is_active.comment = T('Mark here to enable this enrollment')
        db.enrollment.advisor.comment = T('An Advisor is required to validate an enrollment')
        db.enrollment.reviewer.comment = T('Accepted reports are assigned to default reviewer')

    grid = SQLFORM.grid(((db.enrollment.is_active == False) & (db.enrollment.end_date == None)) | (db.enrollment.advisor == None), user_signature=False, exportclasses=exportOptions, showbuttontext=False,
                        links=[dict(header=T('Status'),body=enrollment_status)],
                        searchable=False, create=False,
                        onupdate=lambda f: build_action_menu(response.menu, True))
    return dict(grid=grid)

@auth.requires_membership('Admin')
def document_type():
    db.artifact, db.submission
    response.view = 'generic.html'
    grid = SQLFORM.smartgrid(db.document_type, user_signature=False, exportclasses=exportOptions, showbuttontext=False,
                             links=([dict(header=T('Form'),body=lambda r:
                                         A(I(_class="icon icon-tasks") + ' ' +
                                           (T('Edit') if True else T('Add')),
                                           _href=URL('manage', 'form', args=[r.id]))
                                         )] if 'document_type' not in request.args  else [])
                             )
    return dict(grid=grid)

def login():
    return dict()

@auth.requires_membership('Admin')
def submission():
    response.view = 'generic.html'
    actions={}
    actions[0]=lambda r: A(I('', _class="icon icon-eye-open") + ' ' + T("View Submission"), _href=URL('report','view', args=r), _class='btn btn-mini')
    actions[current.status['accepted']]=lambda r: A(I('', _class="icon icon-user") + ' ' + T("Assign Reviewer"), _href=URL('report','view', args=r), _class='btn btn-mini')

    db.submission.status.represent = lambda id, r: current.status_details[id].render() + I(' (' + str(id) + ')')
    grid = SQLFORM.smartgrid(db.submission, user_signature=False, exportclasses=exportOptions, showbuttontext=False,
                        links=[dict(header=T('Action'),body=lambda r: actions.get(r.status, actions[0])(r.id))]
                             )
    session.return_to = current.url_return(request)
    return dict(grid=grid)

def form():
    doc_type = db.document_type(int(request.args(0))) or None
    if not doc_type: return gen_error(T('Parameter not found'))

    if request.post_vars['formData']:
        doc_type.update_record(review_form = request.post_vars['formData']);
        response.flash = T('Form Saved')

    return locals()

@auth.requires_membership('Admin')
def references():
    response.view = 'generic.html'
    grid = SQLFORM.grid(db.auth_user.id == None, left=db.auth_user.on(db.auth_user.id==db.enrollment.student), fields=[db.enrollment.id, db.enrollment.student, db.auth_user.id], exportclasses=exportOptions)
    return dict(grid=grid, title=T("Broken references"))
