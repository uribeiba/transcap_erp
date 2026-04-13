# remuneraciones/models/__init__.py
from .empleado import Empleado
from .contrato import Contrato
from .afp import AFP
from .salud import Salud
from .concepto import Concepto
from .liquidacion import Liquidacion
from .liquidacion_detalle import LiquidacionDetalle
from .tablas import TramoImpuesto
from .honorario import Honorario

__all__ = [
    'Empleado',
    'Contrato',
    'AFP',
    'Salud',
    'Concepto',
    'Liquidacion',
    'LiquidacionDetalle',
    'TramoImpuesto',
    'Honorario',
]