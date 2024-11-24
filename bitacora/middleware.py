from django.http import HttpResponseForbidden
from django.conf import settings


# class XFrameOptionsMiddleware(MiddlewareMixin):
  # def process_response(self, request, response):
          # response['Content-Security-Policy'] = "frame-ancestors hhttps://codepen.io/pen/"
          # response['Cross-Origin-Opener-Policy'] = "unsafe-none"  # Correcto valor para permitir iframes
          # response['Referrer-Policy'] = "no-referrer-when-downgrade"  # Valor recomendado
          # return response

class IframeOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que deseas proteger
        protected_urls = ["/bitacora/", "/"]

        # Verifica si la URL coincide con alguna de las protegidas
        if any(request.path == url for url in protected_urls):
            # Verifica si la solicitud viene de los dominios permitidos
            allowed_domains = [
                'https://www.ttrading.co', 
                'https://ttrading.co',
                'https://signals.ttrading.co/formulario/',
                'https://editor.wix.com/studio/',
                'https://www.ttrading.co/miembro',
                ]

            if not any(domain for domain in allowed_domains):
                return HttpResponseForbidden("Access denied.")

        response = self.get_response(request)
        return response
