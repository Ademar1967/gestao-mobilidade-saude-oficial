import logging
import traceback
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("diagnostico_erro")
handler = logging.FileHandler("diagnostico_erros.log")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)
logger.setLevel(logging.ERROR)


class DiagnosticoErroMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        logger.error(
            "Erro em %s: %s\n%s", request.path, exception, traceback.format_exc()
        )
