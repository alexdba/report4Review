#!/usr/bin/env python
# coding: utf8
from gluon import current
from gluon import *
import datetime
import calendar



def gen_error(txt): return dict(err = DIV(B(T('Error')) + ': ' + txt + '!',_class='alert alert-danger'))

def T(str):
    return current.T(str)

def enrollment_status(r):
    if not r.is_active and not r.end_date: return T('Pending')
    elif r.is_active and r.end_date: return T('Error')
    elif not r.is_active and r.end_date: return T('Finished')
    elif not r.advisor: return T('Pending')
    else: return T('Active')

def delta_description(delta, level=1):
    diff,y,m = abs(delta.days),0,0
    if diff <= 1:
        if delta.seconds < 3600: return `delta.seconds//60` + ' ' + T('Minutes') if delta.seconds//60 > 1 else T('Minute')
        else: return `delta.seconds//3600` + ' ' + T('Hours') if delta.seconds//3600 > 1 else T('Hour')
    if diff > 365: y,diff=(diff // 365),diff % 365
    if diff > 30:  m,diff=(diff // 30) ,diff % 30
    text = (`y` + ' ' + (T('Years') if y > 1 else T('Year'))) if y > 0 else ''
    if level == 1 and text: return text
    text+= ((', ' if y > 0 else '') + `m` + ' ' + (T('Months') if m > 1 else T('Month'))) if m > 0 else ''
    if level <= 2 and text: return text
    text+= ((' ' + T('and') + ' ') if y+m > 0 else '') + `diff` + ' ' + (T('Days') if diff > 1 else T('Day'))
    return text

def delta_or_date(pdate, limit=1):
    if (current.request.now-pdate).days < limit:
        return delta_description(current.request.now-pdate) + ' ' + T('Ago')
    else: return str(pdate)

def add_months(sourcedate,months,extra_days=0):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])
    return datetime.date(year,month,day) + datetime.timedelta(days=extra_days)

def create_report(sub):
    return Report(doc_type_id=sub.document_type,
                 deadline=sub.submission_date,
                 enrollment=None,
                 submission=sub)

class SubStatus:
    data = {}
    def __init__(self, id, name, description, requires, icon, who, label=''):
        self.data = {'id':id, 'name':name, 'description':description,
           'requires':requires, 'icon':icon, 'who':who,
           'label': ('label-'+label) if label else '' }
    def __str__(self):
        return self.data['name']
    def __repr__(self):
        return self.data['name']
    def __getitem__(self, key):
        return self.data[key]
    def get_description(self):
        if self.data['requires']:
            return T(self.data['description']) + ': ' + T(self.data['who']) + ' ' + T('may') + '  '  + T(self.data['requires'])
        else:
            return T(self.data['description'])
    def render(self,inline=False):
        txt = str(self)
        desc = self.get_description()
        content = SPAN(I('',_class="icon icon-" + self.data['icon'] +  " icon-white") +
                       T(txt), _class="label label-status " + self.data['label'], data={'original-title': desc})
        if inline:
            return content + SPAN(' ') + desc
        else:
            return content

class Report:
    name = 'Empty report'
    today = datetime.datetime.now()
    def __init__(self, doc_type_id, deadline, enrollment, submission=None, open_submission=False):
        self.document_type = current.db.document_type(doc_type_id)
        self.submission =  submission or None
        self.open_submission = open_submission
        self.name = self.document_type.name
        self.artifacts = []
        self.query_artifacts()
        self.deadline = deadline
        #use delta.days to retrive days!
        self.delta = (self.today - datetime.datetime.combine(self.deadline, datetime.time(0, 0)))
        self.enrollment = enrollment
        self.status_details = current.status_details[self.submission.status] if self.submission and self.submission.status else None
    def query_artifacts(self):
        self.artifacts = ([r for r in self.document_type.artifact.select()])
        if self.submission:
            for a in self.artifacts:
                a.submitted_artifact = a.submitted_artifact(current.db.submitted_artifact.submission == self.submission.id).select()
    def deadline_situation(self):
        return delta_description(self.delta) + ' ' + (T('to deadline') if self.delta.days < 0 else T('late'))
    def is_submited(self):
        return self.submission != None
    def is_late(self):
        return self.delta.days >= 0
    def check_role(self, user_id=0):
        if user_id == 0: user_id = current.auth.user_id
        if self.submission:
            if self.submission.enrollment.advisor == user_id: return 'Advisor'
            if self.submission.enrollment.student == user_id: return 'Student'
            if self.submission.reviewer == user_id: return 'Reviewer'
    def student_next_action(self):
        if self.submission:
            if self.submission.status in [current.status['new']]: return 'edit' if not self.is_late() else 'none'
            elif self.submission.status in [current.status['rejected']]: return 'edit'
            else: return 'view'
        elif self.open_submission and not self.is_late():
            return 'submit'
        else:
            return 'none'

    def submit(self):
        self.submission.update_record(status=current.status['submitted'], submission_date = datetime.datetime.now())
        current.db.submission_log.insert(submission=self.submission, role='Student',
                                         content_text='', status=current.status['submitted'])
        current.db.commit()
    def accept(self, ok):
        if self.submission and self.submission.status == current.status["submitted"]:
            opt = "accepted" if ok else "rejected"
            self.submission.update_record(status = current.status[opt])
            current.db.submission_log.insert(submission=self.submission, author=current.auth.user_id, role='Advisor',
                                     content_text='', status=current.status[opt])
            if self.submission.enrollment.reviewer: self.assign(self.submission.enrollment.reviewer, role='Auto')
            current.db.commit()
            return True
    def assign(self, reviewer, role='Admin'):
        if self.submission and self.submission.status == current.status["accepted"]:
            if self.submission.enrollment.advisor.id == reviewer.id: return False
            self.submission.update_record(reviewer = reviewer.id, status=current.status["assigned"])
            current.db.submission_log.insert(submission=self.submission, author=current.auth.user_id, role=role,
                                     content_text='', status=current.status["assigned"])
            current.db.commit()
            return True
    def evaluate(self, form_data):
        if self.submission and self.submission.status == current.status["assigned"]:
            if self.submission.reviewer.id != current.auth.user_id: return False
            self.submission.update_record(review_form = form_data, status=current.status["evaluated"])
            current.db.submission_log.insert(submission=self.submission, author=current.auth.user_id, role='Reviewer',
                                     content_text='', status=current.status["evaluated"])
            current.db.commit()
            return True
    def veredict(self, approve, form_data):
        next_status = current.status["approved"] if approve else current.status["reproved"]
        if self.submission and self.submission.status == current.status["evaluated"] and current.admin:
            self.submission.update_record(review_form = form_data, status=next_status)
            current.db.submission_log.insert(submission=self.submission, author=current.auth.user_id, role='Admin',
                                     content_text='', status=next_status)
            current.db.commit()
            return True
        else: return False

class Enrollment:
    def __init__(self, enrollment_id):
        self.enrollment_id = enrollment_id
        self.row = current.db.enrollment(self.enrollment_id)
        self.doc_types = current.db((current.db.document_type.program == self.row.program) & (current.db.document_type.is_active == True)).select()
        self.query_reports()
    def add_report(self, deadline, rep):
        sub = [s for s in self.submissions if s not in self.assigned_submissions and s.document_type == rep]
        if len(sub) > 0:
            self.assigned_submissions.append(sub[0])
            self.reports[len(self.reports)] = Report(rep.id, deadline, self, sub[0])
        else:
            self.reports[len(self.reports)] = Report(rep.id, deadline, self,
                                                     open_submission=rep not in self.open_submissions)
            self.open_submissions.append(rep)
    def new_submission(self,doc_type_id):
        sub = current.db.submission.insert(enrollment = self.row.id, document_type = doc_type_id, submission_date = datetime.datetime.now(), status=current.status['new'])
        current.db.submission_log.insert(submission=sub, author=current.auth.user_id, role='Student',
                                         content_text='', status=current.status['new'])
        self.refresh()
    def refresh(self):
        self.row = current.db.enrollment(self.enrollment_id)
        self.query_reports()
    def query_reports(self):
        self.reports = {}
        self.assigned_submissions = []
        self.open_submissions = []
        self.submissions = self.row.submission.select()
        max_date = self.row.max_date or (self.row.start_date + datetime.timedelta(years=2))
        for rep in self.doc_types:
            ref_date = self.row.start_date if (rep.relative_date == 'ingress') else datetime.date(datetime.date.today().year, 1, 1)
            if not rep.recurrent:
                dt = add_months(ref_date,rep.period, rep.tolerance)
                if self.row.start_date <= dt <= max_date: self.add_report(dt, rep)
            else:
                dt,i = self.row.start_date,1
                while dt < max_date:
                    dt,i = add_months(ref_date,i*rep.period,rep.tolerance),i+1
                    if self.row.start_date <= dt <= max_date: self.add_report(dt, rep)
#
# ACTION MENU
def build_action_menu(menu, rebuild=False):
    action_menu = []
    action_total = 0
    db = current.db
    def add_action_menu(status, count, action_total, action_menu):
        if count > 0:
            action_menu += [(SPAN(T(status['requires']).capitalize() + ' ') + SPAN(str(count), _class="badge"),
                            False, URL('user','list_reports', args=[status['name']]),[])]
        return count

    if current.admin:
        for status in ["accepted","evaluated"]:
            status_detail = current.status_details[current.status[status]].data
            action_total += add_action_menu(status_detail, current.db(current.db.submission.status == current.status[status]).count(), action_total, action_menu)
        pending = current.db(((db.enrollment.is_active == False) & (db.enrollment.end_date == None)) | (db.enrollment.advisor == None)).count()
        action_total += pending
        if pending > 0: action_menu += [(SPAN(T('Pending Enrollment').capitalize() + ' ') + SPAN(str(pending), _class="badge"),
                            False, URL('manage','pending_enrollment'),[])]

    if current.advisor:
        for status in ["submitted"]:
            status_detail = current.status_details[current.status[status]].data
            action_total += add_action_menu(status_detail, current.db((current.db.enrollment.id == current.db.submission.enrollment) &
                                              (current.db.submission.status == current.status[status]) &
                                              (current.db.enrollment.advisor == current.auth.user_id)).count(),
                                               action_total, action_menu)
        for status in ["assigned"]:
            status_detail = current.status_details[current.status[status]].data
            action_total += add_action_menu(status_detail, current.db((current.db.submission.status == current.status[status]) &
                                              (current.db.submission.reviewer == current.auth.user_id)).count(),
                                               action_total, action_menu)
    render = (SPAN(SPAN(STRONG(T('Action Required')) + ' ', _class="highlighted") + SPAN(str(action_total), _class="badge badge-warning"),_id="action-menu"), False, None, [] + action_menu);

    if action_total > 0 and not rebuild:
        menu.insert(0,render)
    elif action_total > 0 and rebuild:
        menu[0] = render
    elif isinstance(menu[0][0],SPAN) and menu[0][0].attributes['_id'] == 'action-menu': del menu[0]
