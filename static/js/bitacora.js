function cargarDesdeCoordinacion(coordinacionId) {
  if (!coordinacionId) return;

  fetch(`/bitacora/api/coordinacion/${coordinacionId}/`)
    .then((response) => response.json())
    .then((data) => {
      setInputValue("id_origen", data.origen);
      setInputValue("id_intermedio", data.intermedio);
      setInputValue("id_destino", data.destino);

      setSelectValue("id_tracto", data.tracto);
      setSelectValue("id_rampla", data.rampla);
      setSelectValue("id_conductor", data.conductor);

      setInputValue("id_fecha", data.fecha_carga);
      setInputValue("id_fecha_descarga", data.fecha_descarga);
    })
    .catch((err) => console.error("Error cargando coordinación:", err));
}

function setInputValue(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = value ?? "";
}

function setSelectValue(id, value) {
  const $el = $("#" + id);
  if (!$el.length) return;

  // si Select2 ya está inicializado, dispara change para que se refleje
  $el.val(value ?? null).trigger("change");
}

function initClienteAutocomplete(modalOrPageRoot) {
  const root = modalOrPageRoot || document;
  const $cliente = $(root).find("#id_cliente");
  if (!$cliente.length) return;
  if ($cliente.data("select2")) return;

  $cliente.select2({
    width: "100%",
    theme: "bootstrap4",
    placeholder: "Buscar cliente por razón social o RUT...",
    allowClear: true,
    ajax: {
      url: "/bitacora/api/clientes/",
      dataType: "json",
      delay: 250,
      data: function (params) {
        return { q: params.term || "" };
      },
      processResults: function (data) {
        return { results: data.results || [] };
      },
      cache: true,
    },
  });

  $cliente.on("select2:select", function (e) {
    const c = e.params.data || {};
    // si necesitas autollenar campos extra, hazlo aquí
  });
}

function initFormListeners() {
  // Coordinación
  $("#id_coordinacion").on("change", function () {
    const coordId = $(this).val();
    if (coordId) cargarDesdeCoordinacion(coordId);
  });

  // ✅ Coordinador: NO usar template tags aquí.
  // Toma el valor real que ya viene desde Django (initial del form).
  const $coord = $("#id_coordinador");
  if ($coord.length) {
    // sincroniza el resumen al cargar
    $("#resumen-coordinador").text($coord.val() || "---");

    // sincroniza el resumen al escribir
    $coord.on("input", function () {
      $("#resumen-coordinador").text($(this).val() || "---");
    });
  }
}

$(document).ready(function () {
  initClienteAutocomplete();
  initFormListeners();
});



function initClienteAutocomplete(modalOrPageRoot) {
    var root = modalOrPageRoot || document;
  
    // Cambia #id_cliente por el id real del campo cliente en tu form
    var $cliente = $(root).find("#id_cliente");
    if (!$cliente.length) return;
  
    // Evita doble init
    if ($cliente.data("select2")) return;
  
    $cliente.select2({
      width: "100%",
      placeholder: "Buscar cliente por razón social o RUT...",
      allowClear: true,
      ajax: {
        url: "/bitacora/api/clientes/",
        dataType: "json",
        delay: 250,
        data: function (params) {
          return { q: params.term || "" };
        },
        processResults: function (data) {
          return { results: data.results || [] };
        }
      }
    });
  
    // ✅ Cuando eligen un cliente, puedes auto-llenar otros campos si existen
    $cliente.on("select2:select", function (e) {
      var c = e.params.data || {};
  
      // si tienes inputs para mostrar datos del cliente en bitácora:
      setVal(root, "#id_cliente_rut", c.rut);
      setVal(root, "#id_cliente_direccion", c.direccion);
      setVal(root, "#id_cliente_localidad", c.localidad);
      setVal(root, "#id_cliente_telefono", c.telefono);
      setVal(root, "#id_cliente_email", c.email);
    });
  }
  
  function setVal(root, selector, value) {
    var el = (root || document).querySelector(selector);
    if (el && value != null) el.value = value;
  }
  
// bitacora.js - funciones adicionales
function initFormListeners() {
    // Cargar datos de coordinación
    $('#id_coordinacion').change(function() {
        var coordId = $(this).val();
        if (coordId) {
            cargarDesdeCoordinacion(coordId);
        }
    });

    // Auto-llenar coordinador con usuario actual
    if (!$('#id_coordinador').val()) {
        $('#id_coordinador').val('{{ request.user.get_full_name }}');
        $('#resumen-coordinador').text('{{ request.user.get_full_name }}');
    }
}

// Función para formatear números
function formatCurrency(value) {
    return '$' + parseFloat(value || 0).toLocaleString('es-CL');
}

// Llamar cuando el DOM esté listo
$(document).ready(function() {
    initClienteAutocomplete();
    initFormListeners();
});

