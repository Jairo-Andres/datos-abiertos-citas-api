import json
import logging
import time
from collections import deque
from statistics import quantiles

from starlette.middleware.base import BaseHTTPMiddleware

from app.config import LOG_LEVEL


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {"nivel": record.levelname, "mensaje": record.getMessage(), "logger": record.name}
        data.update(getattr(record, "extra_campos", {}))
        return json.dumps(data, ensure_ascii=False)


def configurar_logs() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("api")
    logger.handlers = [handler]
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    return logger


class Latencias:
    """Guarda las últimas N latencias en memoria. Se reinicia cuando Render duerme el servicio."""

    def __init__(self, maximo: int = 1000):
        self.muestras: deque[float] = deque(maxlen=maximo)
        self.peticiones = 0
        self.errores = 0

    def registrar(self, ms: float, status: int) -> None:
        self.muestras.append(ms)
        self.peticiones += 1
        if status >= 500:
            self.errores += 1

    def resumen(self) -> dict:
        datos = sorted(self.muestras)
        if len(datos) >= 2:
            cortes = quantiles(datos, n=100)
            p50, p95 = cortes[49], cortes[94]
        else:
            p50 = p95 = datos[0] if datos else 0.0
        return {
            "peticiones": self.peticiones,
            "errores_5xx": self.errores,
            "latencia_ms_p50": round(p50, 1),
            "latencia_ms_p95": round(p95, 1),
        }


latencias = Latencias()


class LatenciaMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger: logging.Logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request, call_next):
        inicio = time.perf_counter()
        status = 500
        try:
            respuesta = await call_next(request)
            status = respuesta.status_code
            return respuesta
        finally:
            ms = (time.perf_counter() - inicio) * 1000
            latencias.registrar(ms, status)
            self.logger.info(
                "peticion",
                extra={"extra_campos": {
                    "metodo": request.method,
                    "ruta": request.url.path,
                    "status": status,
                    "ms": round(ms, 1),
                }},
            )
