from components import *
import math

@auth.requires_login()
def overview():
    user=auth.user
    enrollments_advisor = db((db.enrollment.advisor == auth.user.id) & (db.enrollment.is_active == True)).select()
    if not (current.advisor or current.admin): redirect(URL('user','reports'))

    if current.admin:
        count_submission_id = db.submission.id.count()
        status_count = db(db.submission).select(db.submission.status, count_submission_id, groupby = db.submission.status)

    return locals()

@auth.requires_login()
def reports():
    enrollments_student = dict([(r.id, Enrollment(r.id)) for r in db((db.enrollment.student == auth.user.id) & (db.enrollment.is_active == True) & (db.enrollment.advisor != None)).select()])
    actions={}
    actions['submit']=lambda r: A(I('', _class="icon icon-share") + ' ' + T("Start Submission"), _href=URL('report','submit', args=r), _class='btn btn-mini')
    actions['edit']=lambda r: A(I('', _class="icon icon-edit") + ' ' + T("Edit Submission"), _href=URL('report','submit', args=r), _class='btn btn-mini')
    actions['view']=lambda r: A(I('', _class="icon icon-eye-open") + ' ' + T("View Submission"), _href=URL('report','view', args=[enrollments_student[r[0]].reports[r[1]].submission.id]), _class='btn btn-mini')
    actions['none']=lambda r: A('', _class="icon icon-empty")
    ###
    session.enrollments_student=enrollments_student
    if len(enrollments_student) == 0: redirect(URL('user','student_enrollments'))
    return locals()

@auth.requires_login()
def student_enrollments():
    request.view = 'generic.html'
    ret = dict();
    has_pending = not db((db.enrollment.is_active == False) &
                             (db.enrollment.end_date == None) &
                             (db.enrollment.student == auth.user_id)).count() > 0

    if 'edit' in request.args:
        db.enrollment.advisor.writable = False
        db.enrollment.program.writable = False
        db.enrollment.start_date.writable = False
    else:
        db.enrollment.advisor.comment = T('Leave it blank if not found or not assigned')
        db.enrollment.program.comment = T('Enrollment will remain pending until Admin approval')
        db.enrollment.work_title.comment = T('May be filled when available')
        db.enrollment.project_document.comment = T('May be filled when available') + " (doc/pdf)"

    db.enrollment.reviewer.readable = False
    db.enrollment.reviewer.writable = False
    db.enrollment.work_abstract.readable = False
    db.enrollment.student.readable = False
    db.enrollment.id.readable = False
    db.enrollment.end_date.writable = False
    db.enrollment.is_active.writable = False
    db.enrollment.is_active.readable = False
    db.enrollment.student.default = auth.user_id
    db.enrollment.student.writable = False
    enr = ((db.enrollment.student == auth.user_id))
    ret['grid'] = SQLFORM.grid(enr, create=has_pending, user_signature=False, exportclasses=exportOptions, showbuttontext=False,
                        deletable=False, editable=True, searchable=False,
                        links=[dict(header=T('Status'),body=enrollment_status)])
    if db((db.enrollment.student == auth.user_id) & (db.enrollment.is_active == True)).count() <= 0:
        ret['msg'] = DIV(T('No active enrollments found! Add a new enrollment or contact Admin for pending check'), _class="alert alert-danger")
    return ret

@auth.requires_login()
def list_reports():
    if len(request.args) == 0 or not request.args[0] in current.status:return gen_error(T('Incorrect Request'))
    status_id = current.status[request.args[0]]
    actions={}
    actions['view']=lambda r: A(I('', _class="icon icon-eye-open") + ' ' + T("View Submission"), _href=URL('report','view', args=r), _class='btn btn-mini')
    actions['view']=lambda r: A(I('', _class="icon icon-thumbs-up") + '/' + I('', _class="icon icon-thumbs-down") + ' ' + T("View and Decide"), _href=URL('report','view', args=r), _class='btn btn-mini')
    actions['evaluate']=lambda r: A(I('', _class="icon icon-tasks") + ' ' + T("Evaluate Submission"), _href=URL('report','view', args=r), _class='btn btn-mini')
    actions['verify']=lambda r: A(I('', _class="icon icon-check") + ' ' + T("Verify Evaluation"), _href=URL('report','view', args=r), _class='btn btn-mini')
    actions['assign']=lambda r: A(I('', _class="icon icon-user") + ' ' + T("Assign Reviewer"), _href=URL('report','view', args=r), _class='btn btn-mini')
    actions['none']=lambda r: A('', _class="icon icon-empty")

    if status_id == current.status['submitted']:
        rows = db((db.submission.enrollment == db.enrollment.id) & (db.enrollment.advisor == auth.user.id)
                  & (db.submission.status == status_id)).select()
        actions['default'] = actions['view']
    elif status_id == current.status['rejected']:
        rows = db((db.submission.enrollment == db.enrollment.id) & (db.submission.status == status_id)).select()
        actions['default'] = actions['none']
    elif status_id == current.status['accepted'] and current.admin:
        rows = db((db.submission.enrollment == db.enrollment.id) & (db.submission.status == status_id)).select()
        actions['default'] = actions['assign']
    elif status_id == current.status['assigned']:
        rows = db((db.submission.enrollment == db.enrollment.id) & (db.submission.reviewer == auth.user.id)
                  & (db.submission.status == status_id)).select()
        actions['default'] = actions['evaluate']
    elif status_id == current.status['evaluated']:
        rows = db((db.submission.enrollment == db.enrollment.id) & (db.submission.status == status_id)).select()
        actions['default'] = actions['verify']
    else:
        return gen_error(T('Incorrect Request'))

    session.return_to = URL('user', 'list_reports', args=request.args)
    return locals()

def import_users():
    request.view = 'generic.html'
    db.auth_membership.user_id.writable = False
    db.auth_membership.user_id.readable = False
    form = SQLFORM(db.auth_membership)
    form[0].insert(-1,TR(LABEL(T('Users')), TEXTAREA(_name='users')))

    if form.validate():
        response.flash = 'Validou'
        lines = form.vars.users.split('\n')
        errors = []
        users = []
        for line in lines:
            line = line.split()
            ind = [i for i, s in enumerate(line) if '@' in s]; ind = ind[0] if len(ind) == 1 else 1000
            if ind <= len(line):
                email = line[ind]
                del line[ind]
                div = int(math.ceil(len(line)/2))
                firstname = ' '.join(line[:div])
                lastname = ' '.join(line[div:])
                users.append({'first_name': firstname.title(), 'last_name': lastname.title(), 'email': email})

        for uid in db.auth_user.bulk_insert(users):
            db.auth_membership.insert(user_id=uid, group_id=form.vars.group_id)

        return dict(users = users)
    else:
        return dict(form=form);
