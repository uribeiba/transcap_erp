# facturacion/services/sii_client.py
import requests
from django.conf import settings

def enviar_dte_sii(factura):
    """
    Construye el XML del DTE según el tipo y lo envía al SII.
    Retorna (aceptado, mensaje, track_id)
    """
    # 1. Generar XML (usando PySII o template)
    # 2. Firmar electrónicamente (necesitas certificado digital)
    # 3. Enviar a https://maullin.sii.cl/DTEWS/ ... (ambiente producción o certificación)
    # Por ahora simulación:
    if factura.monto_total > 0:
        # Simular éxito
        return True, "DTE Aceptado por SII", "12345678"
    else:
        return False, "Monto total inválido", None