from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class CarritoCantidadTests(TestCase):
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
