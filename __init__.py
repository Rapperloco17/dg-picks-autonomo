import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from cuotas import obtener_cuota_bet365
from cuotas_cache import get_cuota_cached
