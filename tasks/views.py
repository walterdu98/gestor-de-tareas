from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from .models import Task, Notificacion 
from .utils import get_task_permission
from django.urls import reverse

@login_required
def task_list(request):
    from users.models import User 
    
    permiso = get_task_permission(request.user)
    es_jefe = request.user.user_roles.filter(role__role_name__iexact='jefe').exists()
    es_admin = request.user.is_superuser

    Task.objects.filter(estado='PENDIENTE', fecha_limite__lt=timezone.now()).update(
        estado='NO_COMPLETADA'
    )

    tareas_base = Task.objects.select_related('creada_por', 'asignado_a')
    if es_admin or es_jefe:
        tareas = tareas_base.all()
    else:
        tareas = tareas_base.filter(Q(creada_por=request.user) | Q(asignado_a=request.user)).distinct()

    q_nombre = request.GET.get('nombre')
    q_estado = request.GET.get('estado')
    q_asignador = request.GET.get('asignador')
    
    if q_nombre:
        if q_nombre.isdigit():
            tareas = tareas.filter(Q(id=q_nombre) | Q(titulo__icontains=q_nombre))
        else:
            tareas = tareas.filter(titulo__icontains=q_nombre)
            
    if q_estado: 
        tareas = tareas.filter(estado=q_estado)

    if q_asignador:
        if q_asignador.isdigit():
            tareas = tareas.filter(Q(creada_por__user_id=q_asignador) | Q(asignado_a__user_id=q_asignador))
        else:
            tareas = tareas.filter(Q(creada_por__username__icontains=q_asignador) | Q(asignado_a__username__icontains=q_asignador))
    
    if request.GET.get('vencidas') == '1':
        tareas = tareas.filter(fecha_limite__lt=timezone.now()).exclude(estado='FINALIZADA')
        
    if request.GET.get('no_completadas') == '1':
        tareas = tareas.filter(estado='NO_COMPLETADA')

    tareas_ordenadas = tareas.order_by('-creada_en')
    paginator = Paginator(tareas_ordenadas, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tasks/tasks_list.html', {
        'tareas': page_obj,  
        'permiso': permiso,
        'estados_disponibles': Task.ESTADOS,
        'total_tareas': tareas.count()
    })

@login_required
def task_create(request):
    from users.models import User, SupervisorEmpleado 
    
    permiso = get_task_permission(request.user)
    user_roles = request.user.user_roles.select_related('role')
    es_admin = request.user.is_superuser
    es_jefe = user_roles.filter(role__role_name__iexact='jefe').exists()
    es_supervisor = user_roles.filter(role__tareas_supervisor__gt=0).exists()

    if not (es_admin or es_jefe or es_supervisor):
        messages.error(request, "No tienes permisos para crear tareas.")
        return redirect('tasks:tasks_list')

    if es_admin or es_jefe:
        usuarios = User.objects.exclude(user_id=request.user.user_id).exclude(is_superuser=True).order_by('username')
    else:
        mis_empleados_ids = SupervisorEmpleado.objects.filter(supervisor=request.user).values_list('empleado_id', flat=True)
        usuarios = User.objects.filter(user_id__in=mis_empleados_ids).order_by('username')

    if request.method == 'POST':
        asignado_id = request.POST.get('asignado_a')
        try:
            if not asignado_id: raise ValueError("Selecciona un responsable.")
            asignado_a = User.objects.get(user_id=asignado_id)
            
            if es_supervisor and not (es_admin or es_jefe):
                if not SupervisorEmpleado.objects.filter(supervisor=request.user, empleado=asignado_a).exists():
                    raise ValueError("No puedes asignar tareas a este usuario.")

            nueva_tarea = Task.objects.create(
                titulo=request.POST.get('titulo'),
                descripcion=request.POST.get('descripcion'),
                asignado_a=asignado_a,
                creada_por=request.user,
                fecha_limite=request.POST.get('fecha_limite') or None,
                estado='PENDIENTE'
            )

            url_filtrada = reverse('tasks:tasks_list') + f"?nombre={nueva_tarea.id}"

            Notificacion.objects.create(
                receptor=asignado_a,
                tarea=nueva_tarea,
                mensaje=f"📋 {request.user.username} te asignó: {nueva_tarea.titulo}",
                link=url_filtrada 
            )

            messages.success(request, f"✅ Tarea '{nueva_tarea.titulo}' creada.")
            return redirect('tasks:tasks_list')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'tasks/task_create.html', {'usuarios': usuarios, 'permiso': permiso})

@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    permiso = get_task_permission(request.user)
    
    if permiso == 3:
        messages.error(request, "Acceso denegado.")
        return redirect('tasks:tasks_list')

    es_proceso_de_reapertura = task.estado in ['FINALIZADA', 'NO_COMPLETADA']

    if es_proceso_de_reapertura:
        task.reabierta = True
        task.estado = 'PENDIENTE'
        task.fecha_finalizacion = None
        task.save() 

    if request.method == 'POST':
        try:
            task.titulo = request.POST.get('titulo')

            desc_form = request.POST.get('descripcion') or request.POST.get('description')
            
            if desc_form:
                task.descripcion = desc_form
            
            nueva_fecha = request.POST.get('fecha_limite')
            if nueva_fecha: 
                task.fecha_limite = nueva_fecha
            
            task.save()
            messages.success(request, f"✏️ Tarea #{task.id} actualizada.")
            return redirect('tasks:tasks_list')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
    return render(request, 'tasks/task_edit.html', {
        'tarea': task,
        'es_reapertura': es_proceso_de_reapertura 
    })

@login_required
def task_finish(request, task_id):
    task = get_object_or_404(Task, id=task_id, asignado_a=request.user)
    if request.method == 'POST':
        if task.estado == 'NO_COMPLETADA':
            messages.error(request, "Esta tarea ya expiró.")
        else:
            permiso = get_task_permission(request.user)
            nuevo_estado = 'FINALIZADA' if permiso <= 2 else 'PENDIENTE_REVISION'
            task.estado = nuevo_estado
            task.fecha_finalizacion = timezone.now()
            task.save()

            if nuevo_estado == 'PENDIENTE_REVISION':
                url_filtrada = reverse('tasks:tasks_list') + f"?nombre={task.id}"
                Notificacion.objects.create(
                    receptor=task.creada_por,
                    tarea=task,
                    mensaje=f"📢 {request.user.username} ha terminado: {task.titulo}.",
                    link=url_filtrada
                )

            messages.info(request, "Tarea enviada para revisión o finalizada.")
    return redirect('tasks:tasks_list')

@login_required
def task_change_status(request, task_id):
    from users.models import SupervisorEmpleado 
    
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        nuevo_estado = request.POST.get('estado')
        permiso = get_task_permission(request.user)
        es_su_supervisor = SupervisorEmpleado.objects.filter(supervisor=request.user, empleado=task.asignado_a).exists()

        url_filtrada = reverse('tasks:tasks_list') + f"?nombre={task.id}"

        if task.asignado_a == request.user and nuevo_estado == 'PENDIENTE_REVISION':
            task.estado = nuevo_estado
            task.save()

            Notificacion.objects.create(
                receptor=task.creada_por,
                tarea=task,
                mensaje=f"📢 {request.user.username} envió a revisión la tarea #{task.id}.",
                link=url_filtrada
            )

            messages.success(request, "Tarea enviada a revisión.")
        elif permiso <= 2 or es_su_supervisor or task.creada_por == request.user:
            estado_anterior = task.estado
            task.estado = nuevo_estado
            
            if nuevo_estado in ['FINALIZADA', 'NO_COMPLETADA']:
                task.fecha_finalizacion = timezone.now()
                task.reabierta = False 
            else:
                task.fecha_finalizacion = None
                
            task.save()

            if nuevo_estado == 'PENDIENTE' and estado_anterior == 'PENDIENTE_REVISION':
                Notificacion.objects.create(
                    receptor=task.asignado_a,
                    tarea=task,
                    mensaje=f"🔄 Tarea reabierta: {task.titulo}.",
                    link=url_filtrada
                )

            messages.success(request, "Estado actualizado.")
    return redirect('tasks:tasks_list')

@login_required
def task_delete(request, task_id):
    if request.method == 'POST':
        tarea = get_object_or_404(Task, id=task_id)
        permiso = get_task_permission(request.user)

        if request.user.is_superuser or permiso in [5, 6, 7]:
            tarea.delete()
            messages.success(request, f"✅ Tarea #{task_id} eliminada.")
        else:
            messages.error(request, "❌ No tienes permisos para eliminar tareas.")
            
    return redirect('tasks:tasks_list')

@login_required
def marcar_notificacion_leida(request, notif_id):
    """Marca la notificación como leída y mantiene los parámetros del link"""
    notificacion = get_object_or_404(Notificacion, id=notif_id, receptor=request.user)
    notificacion.leido = True
    notificacion.save()
    
    if notificacion.link:
        return redirect(notificacion.link)
    
    return redirect('tasks:tasks_list')