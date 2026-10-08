from django.contrib import admin

from .models import ContenidoSitio, RegistroAdministrativo


@admin.register(ContenidoSitio)
class ContenidoSitioAdmin(admin.ModelAdmin):
    list_display = ("clave", "actualizado_por", "actualizado_en")
    search_fields = ("clave", "valor")
    readonly_fields = ("actualizado_por", "creado_en", "actualizado_en")

    def save_model(self, request, obj, form, change):
        obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)
        RegistroAdministrativo.registrar(
            usuario=request.user,
            accion=(
                RegistroAdministrativo.Accion.ACTUALIZACION
                if change
                else RegistroAdministrativo.Accion.CREACION
            ),
            modelo="ContenidoSitio",
            objeto_id=obj.pk,
            resumen=f"Se {'actualizó' if change else 'creó'} el contenido «{obj.clave}».",
        )

    def delete_model(self, request, obj):
        clave = obj.clave
        objeto_id = obj.pk
        super().delete_model(request, obj)
        RegistroAdministrativo.registrar(
            usuario=request.user,
            accion=RegistroAdministrativo.Accion.ELIMINACION,
            modelo="ContenidoSitio",
            objeto_id=objeto_id,
            resumen=f"Se eliminó el contenido «{clave}».",
        )


@admin.register(RegistroAdministrativo)
class RegistroAdministrativoAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "usuario", "accion", "modelo", "objeto_id")
    list_filter = ("accion", "modelo", "creado_en")
    search_fields = ("usuario__username", "modelo", "objeto_id", "resumen")
    readonly_fields = (
        "usuario",
        "accion",
        "modelo",
        "objeto_id",
        "resumen",
        "creado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
