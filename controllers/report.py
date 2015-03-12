from components import Enrollment
from components import build_action_menu
import components
from collections import OrderedDict
from datetime import datetime
import uuid

@auth.requires_login()
def view():
    submission = db.submission(int(request.args(0))) or None
    if not submission: gen_error(T('Parameter not found'))
    report = components.create_report(submission)

    #Advisor accept/reject code
    if submission.enrollment.advisor == auth.user.id:
        if request.vars['accept'] == response.session_id: report.accept(True)
        if request.vars['reject'] == response.session_id: report.accept(False)
        build_action_menu(response.menu, True)

    assign_form = SQLFORM(db.submission, submission, fields = ['reviewer'], showid=False,
                          buttons=[BUTTON(I('', _class="icon icon-white icon-" + current.status_details[current.status['assigned']]['icon']) + ' ' + T("Assign Reviewer"), _class='btn btn-success')])

    #Assign reviewer form code
    def validate_assign(f):
        if not f.vars.reviewer: f.errors.reviewer = T('Choose a reviewer')
        elif long(f.vars.reviewer) == submission.enrollment.advisor: f.errors.reviewer = T('Advisor and Reviewer must not be the same person')
    if assign_form.process(onvalidation=validate_assign, dbio=False).accepted:
       report.assign(db.auth_user(assign_form.vars.reviewer))
       response.flash = T('Reviewer Assigned')
       build_action_menu(response.menu, True)

    #Review form submission storage
    if request.post_vars['formData'] and report.submission.status == current.status["assigned"] and report.submission.reviewer == auth.user_id:
        if report.evaluate(request.post_vars['formData']):
            response.flash = T('Form Saved')
            build_action_menu(response.menu, True)
        else: response.flash = T('Error')

    #Admin approval or reproval
    if request.post_vars['formData'] and request.post_vars['veredict'] and report.submission.status == current.status["evaluated"] and current.admin:
        if report.veredict(request.post_vars['veredict'] == 'approved', request.post_vars['formData']):
            response.flash = T('Form Saved')
            build_action_menu(response.menu, True)
        else: response.flash = T('Error')

    return locals()

@auth.requires_login()
def submit():
    enrollment = session.enrollments_student[int(request.args(0))] or None
    enrollment.refresh();
    report = enrollment.reports[int(request.args(1))] or None
    if not (enrollment and report): redirect(URL('error'))

    if not report.submission and request.vars['open']:
        enrollment.new_submission(report.document_type)
        redirect(URL('report', 'submit', args=session.current_submission, vars={'s':uuid.uuid1()}))

    session.current_submission = request.args

    submission = report.submission or None
    artifacts = report.artifacts

    closed = report.submission.status not in [current.status['new'], current.status['rejected']] if report.submission else False
    missing = None
    if request.vars['close']:
        missing = [a for a in artifacts if a.required and not a.submitted_artifact]
        if not closed and not missing:
            report.submit()
            redirect(URL('user', 'reports', vars={'s':uuid.uuid1()}))

    return locals()

def delete_artifact():
    s = db.submitted_artifact(request.vars['artifact_id'])
    if s:
        filename, filedescriptor = db.submitted_artifact.item_file.retrieve(s.item_file)
        s.delete_record()
        db.submission_log.insert(
            submission=s.submission.id, role='Student', content_text='Del: ' + filename)
        return response.json({'status': 'success'})
    else:
        return response.json({'status': 'fail'})

def submit_artifact():
    response.view = 'generic_ordered.html'
    submission = db.submission(request.args(0)) or None
    if not submission: return gen_error(T('Missing') + ' ' + T('Submission'))
    artifact = db.artifact(request.args(1)) or None
    if not artifact: return gen_error(T('Missing') + ' ' + T('Artifact'))

    ##FORM CREATION
    form = SQLFORM(db.submitted_artifact, fields=['item_file'])
    form.vars.submission = submission.id
    form.vars.artifact = artifact.id
    form.vars.item_date = datetime.now()
    form.custom.widget.item_file['requires'] = IS_UPLOAD_FILENAME(
        extension='(' + '|'.join(','.join(artifact.file_types).split(',')) + ')', error_message=T('Invalid File Type'))
    if session.current_submission:
        form.add_button(T('Back'), URL('report', 'submit', args=session.current_submission, vars={'s':uuid.uuid1()}))
    if form.process().accepted:
        db.submission_log.insert(submission=submission.id, role='Student', content_text='Upload: ' + request.vars.item_file.filename)
        session.enrollments_student[submission.enrollment].refresh()
        redirect(URL('report', 'submit', args=session.current_submission, vars={'s':uuid.uuid1()}))
    result = OrderedDict()
    result[len(result)]=H3(artifact.name)
    result[len(result)]=PRE(artifact.recommended_content)
    result[len(result)]=H4(T('Allowed File Types'))
    for t in artifact.file_types:
        result[len(result)]=LI(t)
    result[len(result)]=form
    return result

def submit_comment():
    submission = db.submission(request.args(0)) or None
    if not submission: return gen_error(T('Missing') + ' ' + T('Submission'))
     ##FORM CREATION
    form = SQLFORM(db.submission_log, fields=['content_text'])

    if auth.user.id == submission.enrollment.advisor.id: form.vars.role = 'Advisor'
    elif auth.user.id == submission.enrollment.student.id: form.vars.role = 'Student'
    elif submission.reviewer and auth.user.id == submission.reviewer.id: form.vars.role = 'Reviewer'
    else: form.vars.role = 'Admin'

    form.vars.submission = submission.id
    if form.process().accepted:
        redirect(request.env.http_referer, client_side=True)
        #redirect(URL('report', 'submit', args=session.current_submission, vars={'s':uuid.uuid1()}, extension=False), client_side=True)
        return dict(d=H2(T('Comment Posted!'), _class="alert alert-info"))
    return dict(form=form)

def comments():
    submission = db.submission(request.args(0)) or None
    if not submission: return gen_error(T('Missing') + ' ' + T('Submission'))
    return locals()

def form():
    submission = db.submission(request.args(0)) or None
    if not submission: return gen_error(T('Missing') + ' ' + T('Submission'))
    doc_type = submission.document_type
    return locals()
