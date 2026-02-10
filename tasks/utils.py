def get_task_permission(user):
    from users.models import userRole 
    if user.is_superuser:
        return 2 

    roles_usuario = userRole.objects.filter(user=user).select_related('role')
    if not roles_usuario.exists():
        return 0

    permisos = []
    for ur in roles_usuario:
        permisos.append(ur.role.tareas_empleados)
        permisos.append(ur.role.tareas_supervisor)

    permisos_validos = [p for p in permisos if p > 0]
    return min(permisos_validos) if permisos_validos else 0