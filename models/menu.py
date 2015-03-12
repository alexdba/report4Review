from gluon import current
from components import build_action_menu
# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.logo = A(B('report',SPAN(4),'IQSC'),XML('&trade;&nbsp;'),
                  _class="brand",_href=URL('default','index'))
response.title = request.application.replace('_',' ').title()
response.subtitle = ''

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Alex Alberto <alexdba@iqsc.usp.br>'
response.meta.keywords = 'web2py, python, framework'
response.meta.generator = 'Python web2py at IQSC'

## your http://google.com/analytics id
response.google_analytics_id = None

## Aditional user alerts
if auth.user and (not auth.user.first_name or not auth.user.last_name):
    response.flash = T('Missing name information, please, complete your profile.')

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    (T('Main'), False, URL('user', 'overview'), [])
]

student_menu = [
    (T('Student'), False, URL(), [
        (T('Enrollments'), False, URL('user', 'student_enrollments'), []),
        (T('Reports'), False, URL('user', 'reports'), []),
    ])
]

admin_menu = [
    (SPAN(T('Manage'), _class='highlighted'), False, URL(), [
        (T('Users'), False, URL('manage', 'user'), []),
        (T('Groups'), False, URL('manage', 'group'), []),
        (T('Program')+'s', False, URL('manage', 'program'), []),
        (T('Document Types'), False, URL('manage', 'document_type'), []),
        (T('Submissions'), False, URL('manage', 'submission'), []),
        (T('Enrollments'), False, URL('manage', 'enrollment'), []),
        (T('Impersonate'), False, URL('default', 'user', args=['impersonate']), []),
        (T('Check References'), False, URL('manage', 'references'), []),
    ])
]
advisor_menu = [(T('Advisor'), False, URL(), [
    (T('Students'), False, URL('user','overview'),[]),
    (T('Reports'), False, URL('advisor','submission'),[])
])]

if current.admin:
    response.menu += admin_menu
if current.advisor:
    response.menu += advisor_menu
if not current.admin and not current.advisor and auth.user:
    response.menu += student_menu



build_action_menu(response.menu)

dev_menu = [
    (SPAN(T('Development'), _class='highlighted'), False, URL(), [
        (T('Manage'), False, URL('user', 'overview'), admin_menu),
        (T('Overview'), False, URL('user', 'overview'), []),
        (T('User Reports'), False, URL('user', 'reports'), []),
        (T('Submitted Reports'), False, URL('user', 'list_reports', args=['submitted']), []),
        (T('Assigned Reports'), False, URL('user', 'list_reports', args=['assigned']), []),
        (T('Evaluated Reports'), False, URL('user', 'list_reports', args=['evaluated']), []),
        (T('Import Users'), False, URL('user', 'import_users'), []),
    ])
]
if request.is_local:
    response.menu += dev_menu


DEVELOPMENT_MENU = True


if "auth" in locals(): auth.wikimenu()
