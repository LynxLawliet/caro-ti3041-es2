from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction


class ContenidoSitio(models.Model):
    clave = models.SlugField(max_length=100, unique=True)
    valor = models.TextField(blank=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="contenidos_sitio_actualizados",
        null=True,
        blank=True,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("clave",)
        verbose_name = "contenido del sitio"
        verbose_name_plural = "contenidos del sitio"

    def __str__(self):
        return self.clave


class RegistroAdministrativo(models.Model):
    class Accion(models.TextChoices):
        CREACION = "creacion", "Creación"
        ACTUALIZACION = "actualizacion", "Actualización"
        ELIMINACION = "eliminacion", "Eliminación"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="acciones_administrativas",
        null=True,
        blank=True,
    )
    accion = models.CharField(max_length=15, choices=Accion.choices)
    modelo = models.CharField(max_length=100)
    objeto_id = models.CharField(max_length=100, blank=True)
    resumen = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "registro administrativo"
        verbose_name_plural = "registros administrativos"

    def __str__(self):
        return f"{self.get_accion_display()} — {self.modelo} {self.objeto_id}".strip()

    @classmethod
    def registrar(cls, *, usuario, accion, modelo, objeto_id="", resumen):
        return cls.objects.create(
            usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
            accion=accion,
            modelo=modelo,
            objeto_id=str(objeto_id),
            resumen=resumen,
        )


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
    )
    precio = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField(default=0)
    imagen_url = models.URLField(blank=True)
    imagen_archivo = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADO = "confirmado", "Confirmado"
        CANCELADO = "cancelado", "Cancelado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="pedidos",
        null=True,
        blank=True,
    )
    nombre_cliente = models.CharField(max_length=150, blank=True)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido #{self.pk or 'nuevo'}"

    @classmethod
    @transaction.atomic
    def registrar_compra(cls, items, nombre_cliente="", usuario=None):
        if not items:
            raise ValueError("No se puede registrar una compra sin productos.")

        productos = {
            producto.pk: producto
            for producto in Producto.objects.filter(
                pk__in=[item.get("id") for item in items]
            )
        }
        detalles = []
        total = Decimal("0")

        for item in items:
            try:
                cantidad_decimal = Decimal(str(item["cantidad"]))
                precio = Decimal(str(item["precio"]))
            except (KeyError, TypeError, ValueError, InvalidOperation) as error:
                raise ValueError(
                    "Los datos de los productos de la compra no son válidos."
                ) from error

            nombre_producto = str(item["nombre"]).strip()
            if (
                not cantidad_decimal.is_finite()
                or cantidad_decimal != cantidad_decimal.to_integral_value()
                or not precio.is_finite()
                or precio < 0
                or precio != precio.to_integral_value()
                or not nombre_producto
            ):
                raise ValueError("Los datos de los productos de la compra no son válidos.")

            cantidad = int(cantidad_decimal)
            if cantidad < 1:
                raise ValueError("Los datos de los productos de la compra no son válidos.")

            total += precio * cantidad
            detalles.append(
                DetallePedido(
                    producto=productos.get(item.get("id")),
                    nombre_producto=nombre_producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                )
            )

        pedido = cls.objects.create(
            usuario=usuario,
            nombre_cliente=nombre_cliente,
            estado=cls.Estado.CONFIRMADO,
            total=total,
        )
        for detalle in detalles:
            detalle.pedido = pedido
        DetallePedido.objects.bulk_create(detalles)
        return pedido

    @classmethod
    def obtener_historial(cls, usuario=None, nombre_cliente=""):
        pedidos = cls.objects.prefetch_related("detalles")
        if usuario is not None:
            return pedidos.filter(usuario=usuario)
        if nombre_cliente:
            return pedidos.filter(nombre_cliente=nombre_cliente)
        return pedidos.none()


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        related_name="detalles_pedido",
        null=True,
        blank=True,
    )
    nombre_producto = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ("pk",)
        verbose_name = "detalle de pedido"
        verbose_name_plural = "detalles de pedido"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name="detalle_pedido_cantidad_positiva",
            ),
        ]

    def __str__(self):
        return f"{self.nombre_producto} x {self.cantidad}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
