def check_initialize():
    if not db().select(db.auth_group.ALL).first():
        db.auth_group.insert(role = 'Admin',
                            description = """Acesso irrestrito para gerenciamento (criar/editar/remover) de todos os dados e configurações do sistema.
                                            Responsabilidades:
                                             - Aceitar matrículas
                                             - Atribuir revisores
                                             - Atribuir usuários a grupos (orientadores e demais administradores)")"""
        )
        db.auth_group.insert(role = 'Advisor',
                            description = "Aceita/rejeita envios de seus alunos e revisa envios de outros alunos, conforme atribuição"
        )

    if not db().select(db.auth_user.ALL).first():
        db.auth_user.insert(
            password = db.auth_user.password.validate('admin')[0],
            email = 'admin@admin.com',
            first_name = 'System',
            last_name = 'Admin',
        )
        auth.add_membership(1,1)
        auth.add_permission(1, 'impersonate', db.auth_user)
    return 'init'

# do initialization check
cache.ram('db_initialized', lambda: check_initialize(), time_expire=None)
