$(document).ready(function() {
    // Cargar tabla inicial
    cargarTablaServicios();
    
    // Buscar al escribir
    $('#input-buscar').on('keyup', function() {
        cargarTablaServicios();
    });
    
    // Filtrar por estado
    $('#select-estado').on('change', function() {
        cargarTablaServicios();
    });
    
    // Abrir modal para nuevo servicio
    $('#modal-servicio').on('show.bs.modal', function() {
        $.ajax({
            url: '/servicios/nuevo/',
            type: 'GET',
            success: function(data) {
                $('#modal-servicio-body').html(data);
            }
        });
    });
});

function cargarTablaServicios() {
    const q = $('#input-buscar').val();
    const estado = $('#select-estado').val();
    
    $.ajax({
        url: '/servicios/lista/',
        type: 'GET',
        data: {
            q: q,
            estado: estado
        },
        success: function(data) {
            $('#tabla-servicios-container').html(data);
        }
    });
}

function abrirDetalleServicio(id) {
    $.ajax({
        url: `/servicios/detalle/${id}/`,
        type: 'GET',
        success: function(data) {
            $('#modal-detalle-body').html(data);
            $('#modal-detalle').modal('show');
        }
    });
}

function abrirEditarServicio(id) {
    $.ajax({
        url: `/servicios/editar/${id}/`,
        type: 'GET',
        success: function(data) {
            $('#modal-servicio-body').html(data);
            $('#modal-servicio').modal('show');
        }
    });
}

function eliminarServicio(id) {
    if (confirm('¿Está seguro de eliminar este servicio?')) {
        $.ajax({
            url: `/servicios/eliminar/${id}/`,
            type: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function() {
                cargarTablaServicios();
                alert('Servicio eliminado correctamente');
            }
        });
    }
}

// Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}