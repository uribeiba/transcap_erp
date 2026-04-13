from decimal import Decimal

# -------------------------
# TOPE IMPONIBLE SALUD 2026
# -------------------------
def tope_imponible_salud():
    """
    Tope imponible para cálculo de cotización de salud (7% de UF/CLP)
    """
    return Decimal('1450000')  # ejemplo, ajustar según SII/AFP

# -------------------------
# TOPE IMPONIBLE AFP 2026
# -------------------------
def tope_imponible_afp():
    """
    Tope imponible para cálculo de cotización de AFP
    """
    return Decimal('1450000')  # ejemplo, ajustar según AFP

# -------------------------
# AFC (Seguro Cesantía)
# -------------------------
def tope_afc():
    """
    Tope imponible para cálculo de AFC
    """
    return Decimal('1450000')  # ejemplo, ajustar según ley

# -------------------------
# UTM 2026 (Unidad Tributaria Mensual)
# -------------------------
def UTM():
    """
    Valor oficial de la UTM en CLP
    """
    return Decimal('96000')  # ejemplo, actualizar según SII

# -------------------------
# UF 2026
# -------------------------
def UF():
    """
    Valor de la UF en CLP
    """
    return Decimal('36000')  # ejemplo, actualizar según SII

# -------------------------
# FACTORES AFP 2026 (ejemplo)
# -------------------------
def factor_afp():
    """
    Factor promedio de cotización AFP
    """
    return Decimal('0.107')  # 10.7% aproximado

# -------------------------
# SALUD 2026 (Fonasa / Isapre)
# -------------------------
def factor_salud():
    """
    Factor cotización salud
    """
    return Decimal('0.07')  # 7%

# -------------------------
# AFC 2026
# -------------------------
def factor_afc():
    """
    Factor seguro cesantía
    """
    return Decimal('0.006')  # 0.6%