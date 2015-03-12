from components import Enrollment

@auth.requires_login()
def reports():
    actions={}
    actions['view']=lambda r: A(I('', _class="icon icon-eye-open") + ' ' + T("View Submission"), _href=URL('report','view', args=r), _class='btn btn-mini')
    actions['none']=lambda r: A('', _class="icon icon-empty")
    ###
    #enrollments_student = dict([(r.id, Enrollment(r.id)) for r in db((db.enrollment.student == auth.user.id)).select()])
    #session.enrollments_student=enrollments_student
    rows = db((db.submission.enrollment == db.enrollment.id) & (db.enrollment.advisor == auth.user.id)
              ).select()

    session.return_url = URL('advisor', 'reports')
    return locals()

@auth.requires_login()
def submission():
    redirect(URL('advisor','reports'))
    #Esse controlador estava muito lento, nao foi possivel identificar o motivo, por hora, usamos o controlador acima
    response.view = 'generic.html'
    actions={}
    actions[0]=lambda r: A(I('', _class="icon icon-eye-open") + ' ' + T("View Submission"), _href=URL('report','view', args=r), _class='btn btn-mini')

    db.submission.status.represent = lambda id, r: current.status_details[id].render() + I(' (' + str(id) + ')')
    query = (db.submission.enrollment == db.enrollment.id) & (db.enrollment.advisor == auth.user_id)
    db.submission.reviewer.readable = False; db.enrollment.advisor.readable = False
    grid = SQLFORM.grid(query, user_signature=False, exportclasses=exportOptions, showbuttontext=False,
                        editable=False, deletable=False, details=False, create=False,
                        fields = [db.enrollment.student, db.enrollment.program,
                                  db.submission.id, db.submission.document_type, db.submission.status,
                                  db.submission.submission_date],
                        links=[dict(header=T('Action'),body=lambda r: actions.get(r.submission.status, actions[0])(r.submission.id))]
                             )
    session.return_to = current.url_return(request)
    return dict(grid=grid, title=T('Advisor Reports Listing'))
