// static/js/cotizaciones.js - Sistema unificado de cotizaciones

(function() {
    'use strict';
    
    console.log("✅ Sistema de cotizaciones cargado");
    
    const IVA_RATE = 0.19;
    
    // ============================================
    // FUNCIONES DE UTILIDAD
    // ============================================
    
    function formatoMoneda(num) {
        if (isNaN(num) || num === null || num === undefined) num = 0;
        return '$ ' + num.toLocaleString('es-CL', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }
    
    function parsearNumero(texto) {
        if (!texto) return 0;
        const limpio = String(texto)
            .replace(/\./g, '')
            .replace(/[^0-9.-]/g, '')
            .replace(',', '.');
        return parseFloat(limpio) || 0;
    }
    
    function obtenerValorInput(input) {
        if (!input) return 0;
        const valor = input.value;
        if (input.type === 'checkbox') return input.checked ? 1 : 0;
        return parsearNumero(valor);
    }
    
    // ============================================
    // SISTEMA DE CÁLCULOS PARA COTIZACIONES
    // ============================================
    
    function CotizacionCalculadora(contenedor) {
        this.contenedor = contenedor || document;
        this.ivaRate = IVA_RATE;
        this.inicializado = false;
    }
    
    CotizacionCalculadora.prototype = {
        obtenerFilasItems: function() {
            return this.contenedor.querySelectorAll('#items-table tbody tr.item-row');
        },
        
        calcularFila: function(fila) {
            const cantidadInput = fila.querySelector('[name$="cantidad"]');
            const valorInput = fila.querySelector('[name$="valor_unitario"]');
            const exentoInput = fila.querySelector('[name$="exento"]');
            
            const cantidad = obtenerValorInput(cantidadInput);
            const valor = obtenerValorInput(valorInput);
            const exento = exentoInput ? exentoInput.checked : false;
            const total = cantidad * valor;
            
            // Actualizar total de la fila
            const totalSpan = fila.querySelector('.item-total');
            if (totalSpan) {
                totalSpan.textContent = formatoMoneda(total);
                totalSpan.dataset.raw = total;
            }
            
            return { cantidad, valor, exento, total };
        },
        
        calcularTotales: function() {
            let neto = 0;
            let afecto = 0;
            let exento = 0;
            
            const filas = this.obtenerFilasItems();
            filas.forEach(fila => {
                const datos = this.calcularFila(fila);
                neto += datos.total;
                
                if (datos.exento) {
                    exento += datos.total;
                } else {
                    afecto += datos.total;
                }
            });
            
            // Calcular IVA
            const iva = afecto * this.ivaRate;
            
            // Obtener descuento
            const descuentoInput = this.contenedor.querySelector('[name$="descuento"]');
            const descuento = obtenerValorInput(descuentoInput);
            
            // Calcular total final
            const total = neto + iva - descuento;
            
            // Actualizar interfaz
            this.actualizarTotalesUI({ neto, iva, descuento, total });
            
            return { neto, afecto, exento, iva, descuento, total };
        },
        
        actualizarTotalesUI: function(totales) {
            const netoEl = this.contenedor.querySelector('#t-neto');
            const ivaEl = this.contenedor.querySelector('#t-iva');
            const descEl = this.contenedor.querySelector('#t-desc');
            const totalEl = this.contenedor.querySelector('#t-total');
            
            if (netoEl) netoEl.textContent = formatoMoneda(totales.neto);
            if (ivaEl) ivaEl.textContent = formatoMoneda(totales.iva);
            if (descEl) descEl.textContent = formatoMoneda(totales.descuento);
            if (totalEl) totalEl.textContent = formatoMoneda(totales.total);
        },
        
        formatearInput: function(input) {
            if (!input || input.type === 'checkbox') return;
            
            input.addEventListener('blur', (e) => {
                const valor = parsearNumero(e.target.value);
                if (!isNaN(valor)) {
                    e.target.value = valor.toLocaleString('es-CL', {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                    });
                }
            });
        },
        
        inicializar: function() {
            if (this.inicializado) return;
            
            // Obtener todos los elementos relevantes
            const inputsCantidad = this.contenedor.querySelectorAll('[name$="cantidad"]');
            const inputsValor = this.contenedor.querySelectorAll('[name$="valor_unitario"]');
            const inputsExento = this.contenedor.querySelectorAll('[name$="exento"]');
            const inputDescuento = this.contenedor.querySelector('[name$="descuento"]');
            
            // Agregar event listeners
            const recalcular = () => this.calcularTotales();
            
            inputsCantidad.forEach(input => {
                input.addEventListener('input', recalcular);
                input.addEventListener('change', recalcular);
                this.formatearInput(input);
            });
            
            inputsValor.forEach(input => {
                input.addEventListener('input', recalcular);
                input.addEventListener('change', recalcular);
                this.formatearInput(input);
            });
            
            inputsExento.forEach(input => {
                input.addEventListener('change', recalcular);
            });
            
            if (inputDescuento) {
                inputDescuento.addEventListener('input', recalcular);
                inputDescuento.addEventListener('change', recalcular);
                this.formatearInput(inputDescuento);
            }
            
            // Calcular inicialmente
            this.calcularTotales();
            
            this.inicializado = true;
            console.log("✅ Sistema de cotizaciones inicializado en contenedor");
        }
    };
    
    // ============================================
    // INTERFAZ GLOBAL
    // ============================================
    
    window.CotizacionCalculadora = CotizacionCalculadora;
    
    window.inicializarCotizacionForm = function(contenedor) {
        console.log("🔧 Inicializando formulario de cotización");
        try {
            const calculadora = new CotizacionCalculadora(contenedor);
            calculadora.inicializar();
            return calculadora;
        } catch (error) {
            console.error("❌ Error inicializando cotización:", error);
            return null;
        }
    };
    
    // Inicializar automáticamente si hay un formulario en la página
    document.addEventListener('DOMContentLoaded', function() {
        const cotForm = document.querySelector('form[data-cot-form]');
        if (cotForm && !document.querySelector('.modal.show')) {
            window.inicializarCotizacionForm(document);
        }
    });
    
})();