from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User, Permission
from .models import Rol, UsuarioRol

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .forms import CrearUsuarioForm
from .models import UsuarioRol

from django.contrib.auth.hashers import make_password
from .forms import CrearUsuarioForm, EditarUsuarioForm
from taller.models import Conductor  # Agregar esta línea con los otros imports


def es_administrador_roles(user):
    return user.is_superuser or user.has_perm('roles.puede_ver_roles')

@login_required
@user_passes_test(es_administrador_roles)
def panel_roles(request):
    roles = Rol.objects.all()
    usuarios_sin_rol = User.objects.filter(rol_usuario__isnull=True)
    usuarios_con_rol = UsuarioRol.objects.select_related('usuario', 'rol').all()
    
    context = {
        'roles': roles,
        'usuarios_sin_rol': usuarios_sin_rol,
        'usuarios_con_rol': usuarios_con_rol,
    }
    return render(request, 'roles/panel.html', context)


@login_required
@user_passes_test(es_administrador_roles)
def asignar_rol(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        rol_id = request.POST.get('rol_id')
        
        usuario = get_object_or_404(User, pk=usuario_id)
        rol = get_object_or_404(Rol, pk=rol_id)
        
        UsuarioRol.objects.update_or_create(
            usuario=usuario,
            defaults={'rol': rol}
        )
        
        # ✅ NUEVO: Sincronizar con conductor
        try:
            conductor = Conductor.objects.get(usuario=usuario)
            if rol.nombre != 'Chofer':
                conductor.activo = False
                conductor.save()
                messages.info(request, f'El usuario ya no aparece como conductor porque su rol es {rol.nombre}')
            else:
                conductor.activo = True
                conductor.save()
        except Conductor.DoesNotExist:
            pass
        
        # Sincronizar permisos del rol al usuario
        usuario.user_permissions.clear()
        usuario.user_permissions.set(rol.permisos.all())
        
        messages.success(request, f'Rol "{rol.nombre}" asignado a {usuario.username}')
    
    return redirect('roles:panel')


@login_required
@user_passes_test(es_administrador_roles)
def crear_rol(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        permisos_ids = request.POST.getlist('permisos')
        
        rol = Rol.objects.create(nombre=nombre, descripcion=descripcion)
        rol.permisos.set(permisos_ids)
        
        messages.success(request, f'Rol "{nombre}" creado correctamente.')
        return redirect('roles:panel')
    
    permisos = Permission.objects.all().order_by('content_type__app_label', 'codename')
    return render(request, 'roles/crear_rol.html', {'permisos': permisos})





@login_required
@user_passes_test(es_administrador_roles)
def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            user = User.objects.create(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=make_password(form.cleaned_data['password']),
                is_active=True
            )
            rol = form.cleaned_data['rol']
            UsuarioRol.objects.create(usuario=user, rol=rol)
            
            # ✅ Sincronizar permisos
            user.user_permissions.set(rol.permisos.all())
            
            messages.success(request, f'Usuario "{user.username}" creado correctamente.')
            return redirect('roles:panel')
    else:
        form = CrearUsuarioForm()
    
    return render(request, 'roles/crear_usuario.html', {'form': form})





@login_required
@user_passes_test(es_administrador_roles)
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    usuario_rol = UsuarioRol.objects.filter(usuario=usuario).first()
    
    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save(commit=False)
            nueva_password = form.cleaned_data.get('password')
            if nueva_password:
                user.password = make_password(nueva_password)
            user.save()
            
            # Actualizar rol
            rol_id = request.POST.get('rol_id')
            if rol_id:
                rol = get_object_or_404(Rol, pk=rol_id)
                if usuario_rol:
                    usuario_rol.rol = rol
                    usuario_rol.save()
                else:
                    UsuarioRol.objects.create(usuario=usuario, rol=rol)
                
                # ✅ NUEVO: Sincronizar con conductor
                try:
                    conductor = Conductor.objects.get(usuario=usuario)
                    if rol.nombre != 'Chofer':
                        conductor.activo = False
                        conductor.save()
                        messages.info(request, f'El usuario ya no aparece como conductor')
                    else:
                        conductor.activo = True
                        conductor.save()
                except Conductor.DoesNotExist:
                    pass
            
            messages.success(request, f'Usuario "{usuario.username}" actualizado correctamente.')
            return redirect('roles:panel')
        else:
            messages.error(request, 'Error al actualizar el usuario.')
    else:
        form = EditarUsuarioForm(instance=usuario)
        roles = Rol.objects.all()
        rol_actual = usuario_rol.rol if usuario_rol else None
    
    return render(request, 'roles/editar_usuario.html', {
        'form': form,
        'usuario': usuario,
        'roles': roles,
        'rol_actual': rol_actual,
    })


@login_required
@user_passes_test(es_administrador_roles)
def eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    
    if request.method == 'POST':
        # No permitir eliminar el propio usuario
        if request.user.id == usuario.id:
            messages.error(request, 'No puedes eliminar tu propio usuario.')
            return redirect('roles:panel')
        
        usuario.delete()
        messages.success(request, f'Usuario "{usuario.username}" eliminado correctamente.')
        return redirect('roles:panel')
    
    return render(request, 'roles/eliminar_usuario.html', {'usuario': usuario})