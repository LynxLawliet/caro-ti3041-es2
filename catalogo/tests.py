from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import admin

from .models import (
    Categoria,
    ContenidoSitio,
    DetallePedido,
    Pedido,
    Producto,
    RegistroAdministrativo,
)
from .views import cargar_contenido


class LandingPageTests(TestCase):
    def test_landingpage_usa_hojas_de_estilo_modulares(self):
        response = self.client.get(reverse("inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "catalogo/css/base.css")
        self.assertContains(response, "catalogo/css/home.css")
        self.assertContains(response, "Soluciones por categoría")
        self.assertNotContains(response, "<style")

    def test_cada_categoria_tiene_estilo_propio_y_conteo_real(self):
        response = self.client.get(reverse("inicio"))
        categorias = response.context["categorias"]

        self.assertEqual(len(categorias), 15)
        self.assertEqual(
            len({categoria["estilo"] for categoria in categorias}),
            len(categorias),
        )
        self.assertEqual(
            sum(categoria["cantidad"] for categoria in categorias),
            response.context["total_productos"],
        )
        self.assertContains(response, "categoria-card--seguridad-industrial")

    def test_ctas_de_portada_enlazan_a_catalogo_y_carrito(self):
        response = self.client.get(reverse("inicio"))

        self.assertContains(response, 'class="boton-detalle" href="/catalogo/"')
        self.assertContains(response, 'class="boton-secundario-home" href="/catalogo/carrito/"')
        self.assertContains(response, 'class="panel-enlace" href="/catalogo/"')
        self.assertContains(response, 'class="enlace-seccion" href="/catalogo/"')
        self.assertEqual(
            self.client.get(reverse("lista")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("carrito")).status_code,
            200,
        )

    def test_ficha_producto_carga_estilos_y_conserva_acciones(self):
        response = self.client.get(reverse("detalle", args=[2]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "catalogo/css/detalle.css")
        self.assertContains(
            response,
            f'action="{reverse("agregar_al_carrito", args=[2])}"',
        )
        self.assertContains(response, 'name="cantidad"')
        self.assertContains(response, "Volver al catálogo")
        self.assertNotContains(response, "<style")

    def test_catalogo_separa_enlace_de_detalle_y_formulario_de_carrito(self):
        response = self.client.get(reverse("lista"))

        self.assertContains(
            response,
            f'href="{reverse("detalle", args=[1])}">Ver detalle</a>',
        )
        self.assertContains(
            response,
            f'action="{reverse("agregar_al_carrito", args=[1])}"',
        )
        self.assertContains(response, ">Agregar al carrito</button>")


class AdministracionPaginaModelTests(TestCase):
    def test_panel_admin_muestra_menu_modular_y_secciones_navegables(self):
        usuario = get_user_model().objects.create_user(
            username="admin-panel",
            is_staff=True,
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("admin_landing"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "catalogo/css/admin.css")
        self.assertContains(response, 'aria-label="Secciones de administración"')
        self.assertContains(response, 'href="#productos-admin"')
        self.assertContains(response, 'href="#nuevo-producto-admin"')
        self.assertContains(response, 'href="#contenido-admin"')
        self.assertNotContains(response, "<style")

    def test_contenido_persistido_sobrescribe_valor_predeterminado(self):
        ContenidoSitio.objects.update_or_create(
            clave="marca",
            defaults={"valor": "Ferretería actualizada"},
        )

        self.assertEqual(
            cargar_contenido()["marca"],
            "Ferretería actualizada",
        )

    def test_registrar_accion_admin_asocia_usuario(self):
        usuario = get_user_model().objects.create_user(username="administrador")

        registro = RegistroAdministrativo.registrar(
            usuario=usuario,
            accion=RegistroAdministrativo.Accion.ACTUALIZACION,
            modelo="ContenidoSitio",
            objeto_id=12,
            resumen="Se editó la marca del sitio.",
        )

        self.assertEqual(registro.usuario, usuario)
        self.assertEqual(registro.objeto_id, "12")

    def test_indice_admin_muestra_solo_productos_del_catalogo(self):
        usuario = get_user_model().objects.create_superuser(
            username="superadmin-indice",
            email="superadmin@example.com",
            password="clave-segura",
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertIn(Producto, admin.site._registry)
        self.assertContains(
            response,
            reverse("admin:catalogo_producto_changelist"),
        )
        for modelo in (
            Categoria,
            ContenidoSitio,
            DetallePedido,
            Pedido,
            RegistroAdministrativo,
        ):
            with self.subTest(modelo=modelo.__name__):
                self.assertNotIn(modelo, admin.site._registry)

    def test_registros_json_se_importan_y_en_admin_solo_aparecen_productos(self):
        usuario = get_user_model().objects.create_superuser(
            username="superadmin-catalogo",
            email="catalogo@example.com",
            password="clave-segura",
        )
        self.client.force_login(usuario)

        productos = self.client.get(reverse("admin:catalogo_producto_changelist"))
        indice = self.client.get(reverse("admin:index"))

        self.assertEqual(Producto.objects.count(), 41)
        self.assertEqual(Categoria.objects.count(), 15)
        self.assertEqual(ContenidoSitio.objects.count(), 30)
        self.assertContains(productos, "Martillo de carpintero 16 oz")
        self.assertContains(indice, reverse("admin:catalogo_producto_changelist"))
        self.assertNotContains(indice, "categorías")
        self.assertNotContains(indice, "pedidos")
        self.assertNotContains(indice, "contenidos del sitio")

    def test_editar_producto_en_admin_actualiza_catalogo_publico(self):
        usuario = get_user_model().objects.create_superuser(
            username="superadmin-producto",
            email="producto@example.com",
            password="clave-segura",
        )
        self.client.force_login(usuario)
        producto = Producto.objects.get(pk=1)

        response = self.client.post(
            reverse("admin:catalogo_producto_change", args=[producto.pk]),
            {
                "nombre": "Martillo actualizado desde Admin",
                "categoria": str(producto.categoria_id),
                "precio": "8990",
                "stock": "21",
                "imagen_url": producto.imagen_url,
                "imagen_archivo": producto.imagen_archivo,
                "descripcion": "Actualizado en Django Admin",
                "visible": "on",
                "_save": "Guardar",
            },
        )

        self.assertEqual(response.status_code, 302)
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, "Martillo actualizado desde Admin")
        pagina_catalogo = self.client.get(reverse("lista"))
        self.assertContains(pagina_catalogo, "Martillo actualizado desde Admin")

    def test_lista_admin_permite_editar_precio_stock_y_visibilidad(self):
        usuario = get_user_model().objects.create_superuser(
            username="superadmin-edicion-rapida",
            email="edicion-rapida@example.com",
            password="clave-segura",
        )
        self.client.force_login(usuario)
        producto = Producto.objects.get(pk=1)
        url = reverse("admin:catalogo_producto_changelist")
        pagina = self.client.get(url)

        self.assertContains(pagina, 'id="id_form-0-precio"')
        self.assertContains(pagina, 'id="id_form-0-stock"')
        self.assertContains(pagina, 'id="id_form-0-visible"')

        respuesta = self.client.post(url, {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": str(producto.pk),
            "form-0-precio": "9990",
            "form-0-stock": "19",
            "form-0-visible": "on",
            "_save": "Guardar",
        })

        self.assertEqual(respuesta.status_code, 302)
        producto.refresh_from_db()
        self.assertEqual(producto.precio, Decimal("9990"))
        self.assertEqual(producto.stock, 19)
        self.assertTrue(producto.visible)

    def test_usuario_staff_puede_hacer_crud_de_productos_en_admin(self):
        usuario = get_user_model().objects.create_user(
            username="staff-crud-productos",
            is_staff=True,
        )
        self.client.force_login(usuario)
        categoria = Categoria.objects.first()
        producto_url = reverse("admin:catalogo_producto_changelist")

        indice = self.client.get(reverse("admin:index"))
        self.assertContains(indice, producto_url)
        listado = self.client.get(producto_url)
        self.assertEqual(listado.status_code, 200)
        self.assertContains(listado, "Martillo de carpintero 16 oz")

        alta = self.client.post(
            reverse("admin:catalogo_producto_add"),
            {
                "nombre": "Producto creado desde Admin",
                "categoria": str(categoria.pk),
                "precio": "12500",
                "stock": "8",
                "imagen_url": "",
                "imagen_archivo": "",
                "descripcion": "Prueba de alta desde Django Admin",
                "visible": "on",
                "_save": "Guardar",
            },
        )
        self.assertEqual(alta.status_code, 302)
        producto = Producto.objects.get(nombre="Producto creado desde Admin")

        edicion = self.client.post(
            reverse("admin:catalogo_producto_change", args=[producto.pk]),
            {
                "nombre": "Producto editado desde Admin",
                "categoria": str(categoria.pk),
                "precio": "15000",
                "stock": "6",
                "imagen_url": "",
                "imagen_archivo": "",
                "descripcion": "Prueba de edición desde Django Admin",
                "visible": "on",
                "_save": "Guardar",
            },
        )
        self.assertEqual(edicion.status_code, 302)
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, "Producto editado desde Admin")

        url_eliminar = reverse("admin:catalogo_producto_delete", args=[producto.pk])
        confirmacion = self.client.get(url_eliminar)
        self.assertEqual(confirmacion.status_code, 200)
        eliminacion = self.client.post(url_eliminar, {"post": "yes"})
        self.assertEqual(eliminacion.status_code, 302)
        self.assertFalse(Producto.objects.filter(pk=producto.pk).exists())

    def test_panel_guarda_contenido_y_registra_auditoria(self):
        usuario = get_user_model().objects.create_user(
            username="editor",
            password="clave",
            is_staff=True,
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("admin_landing"),
            {
                "accion": "guardar_contenido",
                "marca": "Nueva marca",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ContenidoSitio.objects.get(clave="marca").valor,
            "Nueva marca",
        )
        self.assertEqual(
            RegistroAdministrativo.objects.filter(usuario=usuario).count(),
            1,
        )

    def test_admin_catalogo_oculta_modelos_que_no_son_productos(self):
        usuario = get_user_model().objects.create_superuser(
            username="root",
            email="root@example.com",
            password="clave",
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("admin:catalogo_producto_changelist"),
        )
        self.assertNotContains(response, "Contenido del sitio")
        self.assertNotContains(response, "Registro administrativo")


class CatalogoModelTests(TestCase):
    def test_registrar_compra_guarda_total_detalles_y_historial(self):
        usuario = get_user_model().objects.create_user(username='cliente')
        pedido = Pedido.registrar_compra(
            [{
                'id': 123,
                'nombre': 'Producto histórico',
                'precio': 1250,
                'cantidad': 2,
            }],
            nombre_cliente='cliente',
            usuario=usuario,
        )

        self.assertEqual(pedido.estado, Pedido.Estado.CONFIRMADO)
        self.assertEqual(pedido.total, Decimal('2500'))
        self.assertEqual(pedido.detalles.count(), 1)
        self.assertEqual(pedido.detalles.first().subtotal, Decimal('2500'))
        self.assertEqual(
            list(Pedido.obtener_historial(usuario=usuario)),
            [pedido],
        )

    def test_registrar_compra_vacia_falla_sin_guardar_pedido(self):
        with self.assertRaisesMessage(ValueError, 'sin productos'):
            Pedido.registrar_compra([])

        self.assertEqual(Pedido.objects.count(), 0)

    def test_registrar_compra_rechaza_cantidades_y_precios_fraccionarios(self):
        for cantidad, precio in ((1.5, 100), (1, 100.5)):
            with self.subTest(cantidad=cantidad, precio=precio):
                with self.assertRaisesMessage(ValueError, "no son válidos"):
                    Pedido.registrar_compra([{
                        "id": 123,
                        "nombre": "Producto de prueba",
                        "precio": precio,
                        "cantidad": cantidad,
                    }])

        self.assertEqual(Pedido.objects.count(), 0)

    def test_detalle_conserva_datos_del_producto_si_se_elimina(self):
        categoria = Categoria.objects.create(nombre='Categoría de prueba')
        producto = Producto.objects.create(
            nombre='Martillo de prueba',
            categoria=categoria,
            precio=Decimal('8990'),
            stock=4,
        )
        pedido = Pedido.objects.create(nombre_cliente='Cliente de prueba')
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            nombre_producto=producto.nombre,
            cantidad=2,
            precio_unitario=producto.precio,
        )

        self.assertEqual(detalle.subtotal, Decimal('17980'))

        producto.delete()
        detalle.refresh_from_db()

        self.assertIsNone(detalle.producto)
        self.assertEqual(detalle.nombre_producto, 'Martillo de prueba')


class CheckoutHistorialTests(TestCase):
    def test_checkout_registra_pedido_permanente_al_confirmar(self):
        self.client.post(reverse('registro'), {
            'usuario': 'cliente-sesion',
            'contrasena': 'clave',
            'confirmacion': 'clave',
        })
        self.client.post(
            reverse('agregar_al_carrito', args=[1]),
            {'cantidad': 2},
        )

        response = self.client.post(reverse('checkout'))

        self.assertRedirects(response, reverse('pedido_confirmado'))
        pedido = Pedido.objects.get(nombre_cliente='cliente-sesion')
        self.assertEqual(pedido.total, Decimal('17980'))
        self.assertEqual(
            pedido.detalles.get().nombre_producto,
            'Martillo de carpintero 16 oz',
        )
        self.assertNotIn('carrito', self.client.session)

    def test_totales_coinciden_en_carrito_checkout_pedido_y_confirmacion(self):
        self.client.post(reverse('registro'), {
            'usuario': 'cliente-calculos',
            'contrasena': 'clave',
            'confirmacion': 'clave',
        })
        self.client.post(
            reverse('agregar_al_carrito', args=[1]),
            {'cantidad': 2},
        )
        self.client.post(
            reverse('agregar_al_carrito', args=[2]),
            {'cantidad': 3},
        )

        total_esperado = 8990 * 2 + 3990 * 3
        carrito = self.client.get(reverse('carrito'))
        checkout = self.client.get(reverse('checkout'))
        self.assertEqual(carrito.context['total_carrito'], total_esperado)
        self.assertEqual(checkout.context['total_carrito'], total_esperado)
        self.assertEqual(
            sum(item['subtotal'] for item in checkout.context['items_carrito']),
            total_esperado,
        )

        response = self.client.post(reverse('checkout'))

        self.assertRedirects(response, reverse('pedido_confirmado'))
        pedido = Pedido.objects.get(nombre_cliente='cliente-calculos')
        self.assertEqual(pedido.total, Decimal(total_esperado))
        self.assertEqual(
            sum(detalle.subtotal for detalle in pedido.detalles.all()),
            Decimal(total_esperado),
        )
        confirmacion = self.client.get(reverse('pedido_confirmado'))
        self.assertEqual(confirmacion.context['total_carrito'], total_esperado)

    def test_compra_directa_rechaza_cantidad_cero(self):
        self.client.post(reverse('registro'), {
            'usuario': 'cliente-cantidad',
            'contrasena': 'clave',
            'confirmacion': 'clave',
        })

        response = self.client.post(
            reverse('comprar', args=[1]),
            {'cantidad': '0'},
        )

        self.assertRedirects(response, reverse('detalle', args=[1]))
        self.assertNotIn('1', self.client.session.get('carrito', {}))
        self.assertEqual(Pedido.objects.count(), 0)

    def test_compra_directa_notifica_que_el_producto_esta_listo_para_checkout(self):
        self.client.post(reverse('registro'), {
            'usuario': 'cliente-compra-directa',
            'contrasena': 'clave',
            'confirmacion': 'clave',
        })

        response = self.client.post(
            reverse('comprar', args=[1]),
            {'cantidad': '2'},
            follow=True,
        )

        self.assertContains(
            response,
            '2 unidad(es) de Martillo de carpintero 16 oz lista(s) para finalizar la compra.',
        )
        self.assertEqual(self.client.session['carrito']['1']['cantidad'], 2)


class CarritoCantidadTests(TestCase):
    def test_agregar_al_carrito_va_al_carrito_y_suma_solo_el_producto_elegido(self):
        respuesta_martillo = self.client.post(
            reverse('agregar_al_carrito', args=[1]),
            {'cantidad': '2'},
        )
        self.assertRedirects(respuesta_martillo, reverse('carrito'))
        self.assertEqual(self.client.session['carrito']['1']['cantidad'], 2)

        respuesta_destornillador = self.client.post(
            reverse('agregar_al_carrito', args=[2]),
            {'cantidad': '3'},
        )
        self.assertRedirects(respuesta_destornillador, reverse('carrito'))
        self.assertEqual(self.client.session['carrito']['1']['cantidad'], 2)
        self.assertEqual(self.client.session['carrito']['2']['cantidad'], 3)

        self.client.post(
            reverse('agregar_al_carrito', args=[1]),
            {'cantidad': '4'},
        )
        carrito = self.client.session['carrito']
        self.assertEqual(carrito['1']['cantidad'], 6)
        self.assertEqual(carrito['2']['cantidad'], 3)

    def test_agregar_al_carrito_rechaza_cantidad_no_entera(self):
        respuesta = self.client.post(
            reverse('agregar_al_carrito', args=[1]),
            {'cantidad': '1.5'},
        )

        self.assertRedirects(respuesta, reverse('detalle', args=[1]))
        self.assertNotIn('1', self.client.session.get('carrito', {}))

    def test_carrito_muestra_botones_de_cantidad(self):
        session = self.client.session
        session['carrito'] = {
            '1': {
                'id': 1,
                'nombre': 'Producto de prueba',
                'precio': 100,
                'cantidad': 2,
            }
        }
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.client.get(reverse('carrito'))

        self.assertContains(response, 'btn-menos')
        self.assertContains(response, 'btn-mas')

    def test_actualizar_cantidad_a_cero_elimina_producto(self):
        session = self.client.session
        session['carrito'] = {
            '1': {
                'id': 1,
                'nombre': 'Producto de prueba',
                'precio': 100,
                'cantidad': 1,
            }
        }
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        response = self.client.post(reverse('actualizar_cantidad_carrito', args=[1]), {'cantidad': 0})

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('1', self.client.session.get('carrito', {}))


class AdministracionAuthTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user(
            username='admin',
            password='clave-segura',
            is_staff=True,
        )

    def test_cuenta_admin_puede_iniciar_sesion_y_ver_enlace(self):
        response = self.client.post(reverse('login'), {
            'usuario': 'admin',
            'contrasena': 'clave-segura',
        })

        self.assertRedirects(response, reverse('admin_landing'))
        pagina = self.client.get(reverse('lista'))
        self.assertContains(pagina, reverse('admin_landing'))

    def test_usuario_sin_privilegios_no_ve_el_boton_de_administracion(self):
        usuario = get_user_model().objects.create_user(
            username='cliente-sin-permisos',
            password='clave-segura',
            is_staff=False,
        )
        self.client.force_login(usuario)

        pagina = self.client.get(reverse('lista'))

        self.assertNotContains(pagina, reverse('admin_landing'))
        self.assertNotContains(pagina, '>Administración</a>')

    def test_cuenta_no_autenticada_no_puede_entrar_al_panel(self):
        response = self.client.get(reverse('admin_landing'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('admin_landing')}",
        )
