// static/js/cotizaciones.js - Sistema unificado de cotizaciones (FIX CLP + submit safe + Item N)
(function () {
  "use strict";

  console.log("✅ cotizaciones.js cargado");

  const IVA_RATE = 0.19;

  // ============================================================
  // Helpers CLP / números (más robustos para valores tipo 25000.00)
  // ============================================================

  function esInput(el) {
    return el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.tagName === "SELECT");
  }

  // Detecta formato miles CL (12.345.678) sin decimales
  function pareceMilesCL(s) {
    return /^[0-9]{1,3}(\.[0-9]{3})+$/.test(s);
  }

  // Convierte:
  // - "600.000" / "$ 600.000" -> 600000
  // - "25000.00" -> 25000
  // - "1.234,56" -> 1234.56
  function parseCLNumber(value) {
    if (value === null || value === undefined) return 0;
    let s = String(value).trim();
    if (!s) return 0;

    // quitar moneda/espacios
    s = s.replace(/\$/g, "").replace(/\s/g, "");

    // si trae coma, asumimos CL clásico: miles '.' + decimal ','
    if (s.includes(",")) {
      s = s.replace(/\./g, "");
      s = s.replace(/,/g, ".");
      s = s.replace(/[^0-9.-]/g, "");
      const n = parseFloat(s);
      return Number.isFinite(n) ? n : 0;
    }

    // si parece miles CL puro (12.345.678), removemos puntos
    if (pareceMilesCL(s)) {
      s = s.replace(/\./g, "");
      s = s.replace(/[^0-9.-]/g, "");
      const n = parseFloat(s);
      return Number.isFinite(n) ? n : 0;
    }

    // si no, dejamos el punto como decimal (ej: 25000.00)
    s = s.replace(/[^0-9.-]/g, "");
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : 0;
  }

  // Para enviar a Django DecimalField:
  // - "600.000" -> "600000"
  // - "1.234,56" -> "1234.56"
  // - "25000.00" -> "25000.00"
  function toDjangoDecimalString(value) {
    if (value === null || value === undefined) return "0";
    let s = String(value).trim();
    if (!s) return "0";

    s = s.replace(/\$/g, "").replace(/\s/g, "");

    if (s.includes(",")) {
      // CL: 1.234,56
      s = s.replace(/\./g, "");
      s = s.replace(/,/g, ".");
    } else if (pareceMilesCL(s)) {
      // CL: 12.345.678
      s = s.replace(/\./g, "");
    } // si no, puede ser decimal Django 25000.00 -> se deja

    s = s.replace(/[^0-9.-]/g, "");
    if (s === "-" || s === "" || s === ".") return "0";
    return s;
  }

  function formatoCLP(num) {
    const n = Number.isFinite(num) ? num : 0;
    return "$ " + Math.round(n).toLocaleString("es-CL", { maximumFractionDigits: 0 });
  }

  function esExentoDesdeControl(ctrl) {
    if (!ctrl) return false;

    if (ctrl.tagName === "SELECT") {
      const v = String(ctrl.value);
      return v === "True" || v === "true" || v === "1" || v === "SI" || v === "Sí" || v === "SÍ";
    }

    if (ctrl.type === "checkbox") return !!ctrl.checked;
    return String(ctrl.value) === "True";
  }

  // ============================================================
  // Calculadora
  // ============================================================

  function CotizacionCalculadora(contenedor) {
    this.contenedor = contenedor || document;
    this.ivaRate = IVA_RATE;
    this.inicializado = false;
  }

  CotizacionCalculadora.prototype.obtenerFilasItems = function () {
    return this.contenedor.querySelectorAll("#items-table tbody tr.item-row");
  };

  CotizacionCalculadora.prototype.calcularFila = function (fila) {
    const cantidadInput = fila.querySelector('[name$="cantidad"]');
    const valorInput = fila.querySelector('[name$="valor_unitario"]');
    const exentoCtrl = fila.querySelector('[name$="exento"]');

    const cantidad = parseCLNumber(cantidadInput ? cantidadInput.value : 0);
    const valor = parseCLNumber(valorInput ? valorInput.value : 0);
    const exento = esExentoDesdeControl(exentoCtrl);

    const total = cantidad * valor;

    const totalSpan = fila.querySelector(".item-total");
    if (totalSpan) {
      totalSpan.textContent = formatoCLP(total);
      totalSpan.dataset.raw = String(total);
    }

    return { cantidad, valor, exento, total };
  };

  CotizacionCalculadora.prototype.actualizarTotalesUI = function (totales) {
    const netoEl = this.contenedor.querySelector("#t-neto");
    const ivaEl = this.contenedor.querySelector("#t-iva");
    const descEl = this.contenedor.querySelector("#t-desc");
    const totalEl = this.contenedor.querySelector("#t-total");

    if (netoEl) netoEl.textContent = formatoCLP(totales.neto);
    if (ivaEl) ivaEl.textContent = formatoCLP(totales.iva);
    if (descEl) descEl.textContent = formatoCLP(totales.descuento);
    if (totalEl) totalEl.textContent = formatoCLP(totales.total);
  };

  CotizacionCalculadora.prototype.calcularTotales = function () {
    let neto = 0;
    let afecto = 0;
    let exento = 0;

    const filas = this.obtenerFilasItems();
    filas.forEach((fila) => {
      const datos = this.calcularFila(fila);
      neto += datos.total;
      if (datos.exento) exento += datos.total;
      else afecto += datos.total;
    });

    const iva = afecto * this.ivaRate;

    const descuentoInput = this.contenedor.querySelector('[name$="descuento"]');
    const descuento = parseCLNumber(descuentoInput ? descuentoInput.value : 0);

    const total = neto + iva - descuento;

    this.actualizarTotalesUI({ neto, iva, descuento, total });
    return { neto, afecto, exento, iva, descuento, total };
  };

  // ============================================================
  // UX inputs: formatear en blur, limpiar en focus
  // ============================================================

  function attachMoneyUX(input) {
    if (!input || input.dataset.moneyUx === "1") return;
    input.dataset.moneyUx = "1";

    input.addEventListener("focus", () => {
      const raw = toDjangoDecimalString(input.value);
      input.value = raw === "0" ? "" : raw;
    });

    input.addEventListener("blur", () => {
      const n = parseCLNumber(input.value);
      input.value = n ? Math.round(n).toLocaleString("es-CL", { maximumFractionDigits: 0 }) : "0";
    });
  }

  // ============================================================
  // Auto título: "Item 1", "Item 2"... si viene vacío (autorizado ✅)
  // ============================================================

  function autoTitulosItems(formRoot) {
    if (!formRoot) return;

    const filas = formRoot.querySelectorAll("#items-table tbody tr.item-row");
    let idx = 0;

    filas.forEach((fila) => {
      const del = fila.querySelector('[name$="DELETE"]');
      const marcadoEliminar = del && del.type === "checkbox" ? del.checked : false;
      if (marcadoEliminar) return;

      const titulo = fila.querySelector('[name$="titulo"]');
      const valor = fila.querySelector('[name$="valor_unitario"]');
      const cantidad = fila.querySelector('[name$="cantidad"]');

      const hayValor = parseCLNumber(valor ? valor.value : 0) > 0;
      const hayCantidad = parseCLNumber(cantidad ? cantidad.value : 0) > 0;

      if (!titulo) return;

      if (!String(titulo.value || "").trim() && (hayValor || hayCantidad)) {
        idx += 1;
        titulo.value = `Item ${idx}`;
      } else if (String(titulo.value || "").trim()) {
        // si ya tiene título, igual cuenta como item para que el orden quede natural
        idx += 1;
      }
    });
  }

  // ============================================================
  // Sanitizar ANTES de enviar (CLAVE para que guarde)
  // ============================================================

  function sanitizeFormNumbers(formRoot) {
    if (!formRoot) return;

    // 1) Auto títulos (antes de sanitizar, para no perder intención)
    autoTitulosItems(formRoot);

    // 2) campos típicos que se rompen con miles
    const selectors = ['[name$="descuento"]', '[name$="valor_unitario"]', '[name$="cantidad"]'];

    selectors.forEach((sel) => {
      formRoot.querySelectorAll(sel).forEach((el) => {
        if (!esInput(el)) return;
        if (el.type === "checkbox") return;
        el.value = toDjangoDecimalString(el.value);
      });
    });
  }

  // ============================================================
  // Init
  // ============================================================

  CotizacionCalculadora.prototype.inicializar = function () {
    if (this.inicializado) return;

    const recalcular = () => this.calcularTotales();

    this.contenedor.querySelectorAll('[name$="cantidad"]').forEach((i) => {
      i.addEventListener("input", recalcular);
      i.addEventListener("change", recalcular);
    });

    this.contenedor.querySelectorAll('[name$="valor_unitario"]').forEach((i) => {
      i.addEventListener("input", recalcular);
      i.addEventListener("change", recalcular);
      attachMoneyUX(i);
    });

    this.contenedor.querySelectorAll('[name$="exento"]').forEach((i) => {
      i.addEventListener("change", recalcular);
    });

    const desc = this.contenedor.querySelector('[name$="descuento"]');
    if (desc) {
      desc.addEventListener("input", recalcular);
      desc.addEventListener("change", recalcular);
      attachMoneyUX(desc);
    }

    // formatear CLP inicial
    this.contenedor.querySelectorAll('[name$="valor_unitario"], [name$="descuento"]').forEach((i) => {
      const n = parseCLNumber(i.value);
      i.value = n ? Math.round(n).toLocaleString("es-CL", { maximumFractionDigits: 0 }) : "0";
    });

    this.calcularTotales();
    this.inicializado = true;
    console.log("✅ CotizacionCalculadora inicializada");
  };

  // ============================================================
  // API global
  // ============================================================

  window.CotizacionCalculadora = CotizacionCalculadora;

  window.inicializarCotizacionForm = function (root) {
    try {
      const calc = new CotizacionCalculadora(root || document);
      calc.inicializar();

      // expone sanitizador para el panel (submit)
      window.__sanitizeCotizacionForm = function (formEl) {
        sanitizeFormNumbers(formEl);
      };

      return calc;
    } catch (e) {
      console.error("❌ Error inicializarCotizacionForm:", e);
      return null;
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    const cotForm = document.querySelector('form[data-cot-form]');
    if (cotForm && !document.querySelector(".modal.show")) {
      window.inicializarCotizacionForm(document);
    }
  });
})();