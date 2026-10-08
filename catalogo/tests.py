from decimal import Decimal
from unittest.mock import patch

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
        ContenidoSitio.objects.create(
            clave="marca",
            valor="Ferretería actualizada",
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

    def test_modelos_de_administracion_estan_disponibles_en_admin(self):
        self.assertIn(ContenidoSitio, admin.site._registry)
        self.assertIn(RegistroAdministrativo, admin.site._registry)

    @patch("catalogo.views.guardar_json")
    def test_panel_guarda_contenido_y_registra_auditoria(self, guardar_json_mock):
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
        guardar_json_mock.assert_called_once()

    def test_edicion_desde_admin_registra_auditoria(self):
        usuario = get_user_model().objects.create_superuser(
            username="root",
            email="root@example.com",
            password="clave",
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("admin:catalogo_contenidositio_add"),
            {"clave": "admin-titulo", "valor": "Título administrable", "_save": "Guardar"},
        )

        self.assertEqual(response.status_code, 302)
        contenido = ContenidoSitio.objects.get(clave="admin-titulo")
        self.assertEqual(contenido.actualizado_por, usuario)
        self.assertEqual(
            RegistroAdministrativo.objects.get(objeto_id=str(contenido.pk)).accion,
            RegistroAdministrativo.Accion.CREACION,
        )


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
        categoria = Categoria.objects.create(nombre='Herramientas manuales')
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

    def test_cuenta_no_autenticada_no_puede_entrar_al_panel(self):
        response = self.client.get(reverse('admin_landing'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('admin_landing')}",
        )
