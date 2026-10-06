from .views import cargar_contenido


def contenido_sitio(request):
    return {'contenido': cargar_contenido()}
