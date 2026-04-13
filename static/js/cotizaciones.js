(function() {
    "use strict";

    const IVA_RATE = 0.19;

    // --- FUNCIONES DE UTILIDAD ---
    function parseCLP(value) {
        if (!value) return 0;
        let s = String(value).replace(/\$/g, "").replace(/\./g, "").replace(/\s/g, "").trim();
        let n = parseFloat(s);
        return isNaN(n) ? 0 : n;
    }

    function formatCLP(amount) {
        return "$ " + Math.round(amount).toLocaleString("es-CL");
    }

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

    // ==========================================
    // REMOVER FILA NUEVA (ÍTEMS)
    // ==========================================
    window.removerFilaNueva = function(btn) {
        const fila = btn.closest('tr');
        if (fila) {
            fila.remove();
            const totalForms = document.getElementById('id_items-TOTAL_FORMS');
            if (totalForms) {
                const currentCount = document.querySelectorAll('#items-tbody tr.item-row:not([style*="display: none"])').length;
                totalForms.value = currentCount;
            }
            if (window.calcularTodo) window.calcularTodo();
        }
    };

    // ==========================================
    // ELIMINAR FILA EXISTENTE (ÍTEMS con ID en BD)
    // ==========================================
    window.eliminarFilaExistente = function(btn) {
        if (confirm("¿Eliminar este ítem definitivamente?")) {
            const row = btn.closest('.item-row');
            const deleteCheckbox = row.querySelector('input[name$="-DELETE"]');
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                row.style.display = 'none';
                row.classList.remove('item-row');
                if (window.calcularTodo) window.calcularTodo();
            }
        }
    };

    // ==========================================
    // REMOVER CUOTA NUEVA
    // ==========================================
    window.removerCuotaNueva = function(btn) {
        const fila = btn.closest('.cuota-row');
        if (fila) {
            fila.remove();
            const totalForms = document.getElementById('id_cuotas-TOTAL_FORMS');
            if (totalForms) {
                const currentCount = document.querySelectorAll('#cuotas-tbody tr.cuota-row:not([style*="display: none"])').length;
                totalForms.value = currentCount;
            }
            window.actualizarIndicesCuotas();
        }
    };

    // ==========================================
    // ELIMINAR CUOTA EXISTENTE (con ID en BD)
    // ==========================================
    window.eliminarCuotaExistente = function(btn) {
        if (confirm("¿Eliminar esta cuota definitivamente?")) {
            const row = btn.closest('.cuota-row');
            const deleteCheckbox = row.querySelector('input[name$="-DELETE"]');
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                row.style.display = 'none';
                window.actualizarIndicesCuotas();
            }
        }
    };

    // ==========================================
    // ACTUALIZAR ÍNDICES DE CUOTAS
    // ==========================================
    window.actualizarIndicesCuotas = function() {
        const cuotasTbody = document.getElementById('cuotas-tbody');
        if (!cuotasTbody) return;
        
        const rows = cuotasTbody.querySelectorAll('.cuota-row');
        rows.forEach((row, idx) => {
            // Actualizar índice visual
            const indexCell = row.querySelector('.cuota-index');
            if (indexCell) indexCell.innerText = idx + 1;
            
            // Actualizar names de inputs
            row.querySelectorAll('input, select').forEach(input => {
                const name = input.getAttribute('name');
                if (name) {
                    input.setAttribute('name', name.replace(/cuotas-\d+-/, `cuotas-${idx}-`));
                }
                const id = input.getAttribute('id');
                if (id) {
                    input.setAttribute('id', id.replace(/cuotas-\d+-/, `cuotas-${idx}-`));
                }
            });
        });
        
        const totalForms = document.getElementById('id_cuotas-TOTAL_FORMS');
        if (totalForms) {
            totalForms.value = rows.length;
        }
    };

    // ==========================================
    // AGREGAR NUEVA CUOTA
    // ==========================================
    window.agregarNuevaCuota = function() {
        const tbody = document.getElementById('cuotas-tbody');
        const template = document.getElementById('cuota-row-template');
        const totalForms = document.getElementById('id_cuotas-TOTAL_FORMS');
        
        if (!tbody || !template) {
            console.warn('No se encontraron los elementos necesarios para agregar cuota');
            return;
        }
        
        let count = totalForms ? parseInt(totalForms.value) : 0;
        if (isNaN(count)) count = 0;
        
        // Reemplazar __prefix__ con el índice actual
        let html = template.innerHTML.replace(/__prefix__/g, count);
        
        // Crear nueva fila
        const newRow = document.createElement('tr');
        newRow.className = 'cuota-row';
        newRow.innerHTML = html;
        
        // Agregar al final del tbody
        tbody.appendChild(newRow);
        
        // Incrementar TOTAL_FORMS
        if (totalForms) {
            totalForms.value = count + 1;
        }
        
        // Actualizar índices
        window.actualizarIndicesCuotas();
        
        // Si el total está calculado, sugerir distribución automática
        const totalSpan = document.getElementById('t-total');
        if (totalSpan) {
            const totalText = totalSpan.textContent.replace(/[^0-9]/g, '');
            const totalValue = parseInt(totalText) || 0;
            const cuotaCount = tbody.querySelectorAll('.cuota-row:not([style*="display: none"])').length;
            if (cuotaCount > 0 && totalValue > 0) {
                const montoPorCuota = Math.round(totalValue / cuotaCount);
                tbody.querySelectorAll('.cuota-row:not([style*="display: none"])').forEach((row, idx) => {
                    const montoInput = row.querySelector('.cuota-monto');
                    if (montoInput && !montoInput.value) {
                        if (idx === cuotaCount - 1) {
                            // Última cuota: resto
                            const sumaAnteriores = montoPorCuota * (cuotaCount - 1);
                            montoInput.value = totalValue - sumaAnteriores;
                        } else {
                            montoInput.value = montoPorCuota;
                        }
                    }
                });
            }
        }
    };

    // ==========================================
    // LÓGICA DE CÁLCULO MEJORADA
    // ==========================================
    window.calcularTodo = function() {
        const form = document.querySelector('form[data-cot-form]');
        if (!form) return;

        let baseAfecta = 0;
        let baseExenta = 0;

        const rows = form.querySelectorAll('#items-tbody tr.item-row');
        
        rows.forEach(row => {
            const deleteCheck = row.querySelector('input[name$="-DELETE"]');
            if (deleteCheck && deleteCheck.checked) return;
            
            const cantInput = row.querySelector('.item-cantidad');
            const unitInput = row.querySelector('.item-valor');
            const exentoSelect = row.querySelector('.exento-select');
            
            if (!cantInput || !unitInput) return;
            
            const cant = parseFloat(cantInput.value) || 0;
            const unit = parseFloat(unitInput.value) || 0;
            const exento = exentoSelect ? exentoSelect.value === 'True' : false;
            
            const totalFila = cant * unit;
            
            if (exento) { 
                baseExenta += totalFila; 
            } else { 
                baseAfecta += totalFila; 
            }

            const spanTotal = row.querySelector('.item-total');
            if (spanTotal) spanTotal.textContent = formatCLP(totalFila);
        });

        const netoTotal = baseAfecta + baseExenta;
        const iva = Math.round(baseAfecta * IVA_RATE);
        
        let descuentoMonto = 0;
        const descuentoMontoInput = form.querySelector('.descuento-monto');
        const descuentoPorcentajeInput = form.querySelector('.descuento-porcentaje');
        
        if (descuentoMontoInput && descuentoMontoInput.value) {
            descuentoMonto = parseFloat(descuentoMontoInput.value) || 0;
        } else if (descuentoPorcentajeInput && descuentoPorcentajeInput.value) {
            const descuentoPorcentaje = parseFloat(descuentoPorcentajeInput.value) || 0;
            descuentoMonto = Math.round(netoTotal * (descuentoPorcentaje / 100));
        }
        
        let recargoMonto = 0;
        const recargoInput = form.querySelector('.recargo-porcentaje');
        if (recargoInput && recargoInput.value) {
            const recargoPorcentaje = parseFloat(recargoInput.value) || 0;
            recargoMonto = Math.round(netoTotal * (recargoPorcentaje / 100));
        }
        
        const totalFinal = netoTotal + iva - descuentoMonto + recargoMonto;

        const updateText = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = formatCLP(val);
        };

        updateText('t-neto', netoTotal);
        updateText('t-iva', iva);
        updateText('t-total', totalFinal);
        
        const afectoEl = document.getElementById('t-afecto');
        if (afectoEl) afectoEl.textContent = formatCLP(baseAfecta);
        
        const exentoEl = document.getElementById('t-exento');
        if (exentoEl) exentoEl.textContent = formatCLP(baseExenta);
    };

    // ==========================================
    // AGREGAR NUEVA FILA (ÍTEMS)
    // ==========================================
    function agregarNuevaFila() {
        const tbody = document.getElementById('items-tbody');
        const template = document.getElementById('item-row-template');
        const totalForms = document.getElementById('id_items-TOTAL_FORMS');
        
        if (!tbody || !template || !totalForms) {
            console.warn('No se encontraron los elementos necesarios para agregar fila');
            return;
        }
        
        let count = parseInt(totalForms.value);
        if (isNaN(count)) count = 0;
        
        let html = template.innerHTML.replace(/__prefix__/g, count);
        
        const newRow = document.createElement('tr');
        newRow.className = 'item-row';
        newRow.innerHTML = html;
        
        tbody.appendChild(newRow);
        totalForms.value = count + 1;
        
        if (window.calcularTodo) window.calcularTodo();
    }

    // ==========================================
    // DISTRIBUIR CUOTAS AUTOMÁTICAMENTE
    // ==========================================
    window.distribuirCuotas = function() {
        const totalSpan = document.getElementById('t-total');
        if (!totalSpan) return;
        
        const totalText = totalSpan.textContent.replace(/[^0-9]/g, '');
        const totalValue = parseInt(totalText) || 0;
        
        const cuotasTbody = document.getElementById('cuotas-tbody');
        const cuotaRows = cuotasTbody.querySelectorAll('.cuota-row:not([style*="display: none"])');
        const cuotaCount = cuotaRows.length;
        
        if (cuotaCount === 0 || totalValue === 0) return;
        
        const montoPorCuota = Math.floor(totalValue / cuotaCount);
        const resto = totalValue - (montoPorCuota * cuotaCount);
        
        cuotaRows.forEach((row, idx) => {
            const montoInput = row.querySelector('.cuota-monto');
            if (montoInput) {
                if (idx === cuotaCount - 1) {
                    montoInput.value = montoPorCuota + resto;
                } else {
                    montoInput.value = montoPorCuota;
                }
            }
        });
    };

    // ==========================================
    // ENVÍO DEL FORMULARIO MEJORADO
    // ==========================================
    document.addEventListener('submit', async function(e) {
        const form = e.target.closest('form[data-cot-form]');
        if (!form || form.getAttribute('data-submitting') === '1') return;

        e.preventDefault();
        
        const rows = form.querySelectorAll('#items-tbody tr.item-row');
        let hasValidItems = false;
        
        for (let row of rows) {
            const deleteCheck = row.querySelector('input[name$="-DELETE"]');
            if (deleteCheck && deleteCheck.checked) continue;
            
            const tituloInput = row.querySelector('.item-titulo');
            const titulo = tituloInput ? tituloInput.value?.trim() : '';
            const cantidad = parseFloat(row.querySelector('.item-cantidad')?.value) || 0;
            const valor = parseFloat(row.querySelector('.item-valor')?.value) || 0;
            
            if (titulo || cantidad > 0 || valor > 0) {
                hasValidItems = true;
                break;
            }
        }
        
        if (!hasValidItems) {
            alert('Debe agregar al menos un ítem con descripción.');
            return;
        }
        
        const btn = form.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        
        form.setAttribute('data-submitting', '1');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

        const fd = new FormData(form);

        try {
            const res = await fetch(form.action, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie('csrftoken') 
                },
                body: fd
            });

            const data = await res.json();

            if (res.ok && data.ok) {
                const modal = document.getElementById('cotModal');
                if (modal) {
                    if (typeof $ !== 'undefined' && $.fn.modal) {
                        $(modal).modal('hide');
                    } else if (modal.modal) {
                        modal.modal('hide');
                    } else {
                        modal.style.display = 'none';
                        document.body.classList.remove('modal-open');
                        const backdrop = document.querySelector('.modal-backdrop');
                        if (backdrop) backdrop.remove();
                    }
                }
                
                if (typeof cargarTablaCotizaciones === 'function') {
                    cargarTablaCotizaciones();
                } else if (typeof window.cargarTabla === 'function') {
                    window.cargarTabla();
                } else {
                    window.location.reload();
                }
            } else {
                let errorMsg = "Error al guardar la cotización:\n\n";
                
                if (data.errors) {
                    if (typeof data.errors === 'object') {
                        if (data.errors.form) {
                            errorMsg += "• Errores en cabecera:\n";
                            for (let field in data.errors.form) {
                                const fieldErrors = data.errors.form[field];
                                if (Array.isArray(fieldErrors)) {
                                    errorMsg += `  - ${field}: ${fieldErrors.join(', ')}\n`;
                                } else {
                                    errorMsg += `  - ${field}: ${fieldErrors}\n`;
                                }
                            }
                        }
                        if (data.errors.formset_items && data.errors.formset_items.length > 0) {
                            errorMsg += "\n• Errores en ítems:\n";
                            data.errors.formset_items.forEach((err, idx) => {
                                if (err && err.titulo) {
                                    errorMsg += `  - Ítem ${idx + 1}: ${Array.isArray(err.titulo) ? err.titulo.join(', ') : err.titulo}\n`;
                                }
                            });
                        }
                        if (data.errors.formset_cuotas && data.errors.formset_cuotas.length > 0) {
                            errorMsg += "\n• Errores en cuotas:\n";
                            data.errors.formset_cuotas.forEach((err, idx) => {
                                if (err) {
                                    const fields = Object.keys(err).join(', ');
                                    errorMsg += `  - Cuota ${idx + 1}: ${fields}\n`;
                                }
                            });
                        }
                    } else {
                        errorMsg += data.errors;
                    }
                } else if (data.error) {
                    errorMsg += data.error;
                } else if (data.message) {
                    errorMsg += data.message;
                } else {
                    errorMsg += "Error desconocido. Revise la consola para más detalles.";
                }
                
                alert(errorMsg);
                console.error("Error detallado:", data);
                
                form.removeAttribute('data-submitting');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }

        } catch (err) {
            console.error("Excepción en envío:", err);
            alert("Hubo un problema de conexión. Por favor, intente nuevamente.");
            form.removeAttribute('data-submitting');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });

    // ==========================================
    // EVENTOS DE INTERFAZ
    // ==========================================
    document.addEventListener('input', function(e) {
        if (e.target.matches('.item-cantidad, .item-valor, .descuento-monto, .descuento-porcentaje, .recargo-porcentaje, .exento-select')) {
            window.calcularTodo();
        }
        if (e.target.matches('.cuota-fecha, .cuota-monto')) {
            // No hacer nada extra
        }
    });

    document.addEventListener('change', function(e) {
        if (e.target.matches('.exento-select, input[name$="-DELETE"]')) {
            window.calcularTodo();
        }
        if (e.target.matches('.condicion-venta')) {
            if (e.target.value === 'CONT') {
                // Si es contado, limpiar cuotas
                const cuotasTbody = document.getElementById('cuotas-tbody');
                if (cuotasTbody) {
                    cuotasTbody.innerHTML = '';
                    const totalForms = document.getElementById('id_cuotas-TOTAL_FORMS');
                    if (totalForms) totalForms.value = 0;
                }
            }
        }
    });

    // Evento para agregar nueva fila de ítems
    document.addEventListener('click', function(e) {
        const addBtn = e.target.closest('#btn-add-item');
        if (addBtn) {
            e.preventDefault();
            e.stopPropagation();
            agregarNuevaFila();
        }
        
        const addCuotaBtn = e.target.closest('#btn-add-cuota');
        if (addCuotaBtn) {
            e.preventDefault();
            e.stopPropagation();
            window.agregarNuevaCuota();
        }
        
        const distribuirBtn = e.target.closest('#btn-distribuir-cuotas');
        if (distribuirBtn) {
            e.preventDefault();
            window.distribuirCuotas();
        }
    });

    // ==========================================
    // INICIALIZACIÓN
    // ==========================================
    function inicializarTodo() {
        if (window.calcularTodo) window.calcularTodo();
        if (window.actualizarIndicesCuotas) window.actualizarIndicesCuotas();
        
        // Si hay un botón de distribuir cuotas, agregar evento
        setTimeout(() => {
            const distribuirBtn = document.getElementById('btn-distribuir-cuotas');
            if (distribuirBtn && !distribuirBtn._hasListener) {
                distribuirBtn.addEventListener('click', window.distribuirCuotas);
                distribuirBtn._hasListener = true;
            }
        }, 200);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(inicializarTodo, 100);
        });
    } else {
        setTimeout(inicializarTodo, 100);
    }

})();