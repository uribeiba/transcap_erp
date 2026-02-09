// static/js/main.js

// =======================
// INICIALIZACIÓN DEL MENÚ LATERAL
// =======================
document.addEventListener('DOMContentLoaded', function () {
  var current = window.location.pathname.replace(/\/+$/, '') || '/';

  document.querySelectorAll('.nav-sidebar a.nav-link.active').forEach(function (a) {
    a.classList.remove('active');
  });
  document.querySelectorAll('.nav-sidebar .menu-open').forEach(function (li) {
    li.classList.remove('menu-open');
  });

  document.querySelectorAll('.nav-sidebar a.nav-link').forEach(function (a) {
    var href = a.getAttribute('href') || '';
    if (href === '#' || href.trim() === '') return;

    var linkPath;
    try { linkPath = new URL(href, window.location.origin).pathname; }
    catch (e) { linkPath = href; }

    linkPath = linkPath.replace(/\/+$/, '') || '/';

    if (linkPath === current) {
      a.classList.add('active');

      var tree = a.closest('.nav-item.has-treeview') || a.closest('.nav-item.menu-is-opening');
      if (tree) {
        tree.classList.add('menu-open');
        var parentLink = tree.querySelector(':scope > a.nav-link');
        if (parentLink) parentLink.classList.add('active');
      }
    }
  });
});

// =======================
// COTIZACIONES - SISTEMA UNIFICADO COMPATIBLE
// =======================

// Cargar el sistema unificado de cotizaciones si no está ya disponible
function cargarSistemaCotizaciones() {
    // Verificar si ya está cargado
    if (typeof window.CotizacionCalculadora !== 'undefined') {
        console.log("✅ Sistema de cotizaciones ya cargado (cotizaciones.js)");
        return;
    }
    
    // Si no está cargado, mostrar advertencia
    console.warn("⚠️ Sistema de cotizaciones no encontrado. Asegúrate de que cotizaciones.js está cargado.");
    
    // Crear una implementación de respaldo básica para evitar errores
    window.CotizacionCalculadora = function(contenedor) {
        console.warn("⚠️ Usando implementación de respaldo para cotizaciones");
        this.contenedor = contenedor || document;
    };
    
    window.CotizacionCalculadora.prototype = {
        inicializar: function() {
            console.warn("⚠️ Implementación de respaldo - cálculos básicos");
            // Llamar a la función de respaldo que ya existe
            if (typeof window.calculosCotizacionRespaldo === 'function') {
                window.calculosCotizacionRespaldo(this.contenedor);
            }
        }
    };
    
    window.inicializarCotizacionForm = function(contenedor) {
        console.warn("⚠️ Usando inicialización de respaldo");
        try {
            const calculadora = new window.CotizacionCalculadora(contenedor);
            calculadora.inicializar();
            return calculadora;
        } catch (error) {
            console.error("❌ Error en inicialización de respaldo:", error);
            return null;
        }
    };
}

// Inicializar cuando sea necesario
document.addEventListener('DOMContentLoaded', function() {
    // Cargar sistema de cotizaciones si estamos en una página relevante
    if (window.location.pathname.includes('cotizaciones')) {
        cargarSistemaCotizaciones();
    }
});

// =======================
// FUNCIONES DE UTILIDAD GLOBAL (mantener para compatibilidad)
// =======================

// ✅ Función para formatear números como moneda chilena (compatible con _form.html)
if (typeof window.formatoMoneda === 'undefined') {
  window.formatoMoneda = function(num) {
    if (isNaN(num) || num === null || num === undefined) num = 0;
    return '$ ' + num.toLocaleString('es-CL', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  };
}

// ✅ Función para parsear números (quitar puntos de miles) - compatible
if (typeof window.parsearNumero === 'undefined') {
  window.parsearNumero = function(texto) {
    if (!texto) return 0;
    const limpio = String(texto)
      .replace(/\./g, '')  // Eliminar puntos (separadores de miles)
      .replace(',', '.');  // Convertir coma decimal a punto
    return parseFloat(limpio) || 0;
  };
}

// ✅ Función de respaldo para cálculos simplificados (mantener por si acaso)
window.calculosCotizacionRespaldo = function(contenedor) {
  console.log("🆘 Ejecutando cálculos de respaldo");
  
  try {
    let neto = 0;
    let afecto = 0;
    const ivaRate = 0.19;
    
    // Calcular por cada fila
    const rows = contenedor.querySelectorAll('#items-table tbody tr.item-row');
    rows.forEach(row => {
      const cantidadInput = row.querySelector('[name$="cantidad"]');
      const valorInput = row.querySelector('[name$="valor_unitario"]');
      const exentoCheck = row.querySelector('[name$="exento"]');
      const totalSpan = row.querySelector('.item-total');
      
      if (cantidadInput && valorInput) {
        const cantidad = parseFloat(cantidadInput.value) || 0;
        const valor = parseFloat(valorInput.value.replace(/\./g, '').replace(',', '.')) || 0;
        const total = cantidad * valor;
        
        // Actualizar total de la fila
        if (totalSpan) {
          totalSpan.textContent = '$ ' + total.toLocaleString('es-CL');
        }
        
        neto += total;
        
        // Verificar si es exento
        if (!exentoCheck || !exentoCheck.checked) {
          afecto += total;
        }
      }
    });
    
    // Calcular IVA y descuento
    const descuentoInput = contenedor.querySelector('[name$="descuento"]');
    const descuento = parseFloat(descuentoInput?.value) || 0;
    const iva = afecto * ivaRate;
    const total = neto + iva - descuento;
    
    // Actualizar la interfaz
    const netoEl = contenedor.querySelector('#t-neto');
    const ivaEl = contenedor.querySelector('#t-iva');
    const descEl = contenedor.querySelector('#t-desc');
    const totalEl = contenedor.querySelector('#t-total');
    
    if (netoEl) netoEl.textContent = '$ ' + neto.toLocaleString('es-CL');
    if (ivaEl) ivaEl.textContent = '$ ' + iva.toLocaleString('es-CL');
    if (descEl) descEl.textContent = '$ ' + descuento.toLocaleString('es-CL');
    if (totalEl) totalEl.textContent = '$ ' + total.toLocaleString('es-CL');
    
    console.log("✅ Cálculos de respaldo completados");
  } catch (error) {
    console.error("❌ Error en cálculos de respaldo:", error);
  }
};

// ✅ Función para verificar si estamos en un modal (mantener por si acaso)
window.estaEnModal = function() {
  const modal = document.querySelector('.modal.show');
  if (modal) {
    const form = document.querySelector('form[data-cot-form]');
    return form && modal.contains(form);
  }
  return false;
};

// ✅ Compatibilidad con código existente: si alguna parte del código espera initCotizacionForm, la redirigimos
if (typeof window.initCotizacionForm === 'undefined') {
  window.initCotizacionForm = function(root) {
    // Si el sistema unificado está disponible, usarlo
    if (typeof window.inicializarCotizacionForm !== 'undefined') {
      return window.inicializarCotizacionForm(root);
    } else {
      // Usar el sistema de respaldo
      return window.calculosCotizacionRespaldo(root);
    }
  };
}

console.log("✅ main.js cargado correctamente");