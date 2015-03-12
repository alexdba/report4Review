from gluon import current
from components import SubStatus
#Inicializar os status de submissao
stat = {}
current.status = {}




current.status['new'] = 1
stat[1] = SubStatus(1,'new','not submitted','complete the submission','edit','Student')
current.status['rejected'] = 5
stat[5] = SubStatus(5,'rejected','rejected by advisor','review and submit again','thumbs-down','Student','warning')
current.status['submitted'] = 10
stat[10] = SubStatus(10,'submitted','submitted by student','accept or reject','ok','Advisor','info')
current.status['accepted'] = 15
stat[15] = SubStatus(15,'accepted','accepted by advisor','assign a reviewer','thumbs-up','Admin','info')
current.status['assigned'] = 20
stat[20] = SubStatus(20,'assigned','waiting evaluation','review the submission','hand-right','Reviewer')
current.status['evaluated'] = 25
stat[25] = SubStatus(25,'evaluated','waiting verification','verify the evaluation','check','Admin','info')
current.status['approved'] = 29
stat[29] = SubStatus(29,'approved','approved by positive evaluation','','ok','','success')
current.status['reproved'] = 30
stat[30] = SubStatus(30,'reproved','reproved by negative evaluation','','remove','','important')

current.status_details = stat

"""
This was used to store status flow in database 
if True:
    db.submission_status.truncate()
    for i in range(1,31):
        id = db.submission_status.insert(id=i,name='reserved')
        if i in stat:
            db(db.submission_status.id==i).update(**stat[i])
"""
