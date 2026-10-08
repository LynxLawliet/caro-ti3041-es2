from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.urls import reverse
from django.utils.text import slugify

from .models import Categoria, ContenidoSitio, Pedido, Producto, RegistroAdministrativo

CATEGORIA_VISUAL = {
    "herramientas-manuales": "🔨",
    "herramientas-electricas": "⚡",
    "accesorios-para-herramientas": "⚙",
    "abrasivos": "◈",
    "fijaciones": "⊕",
    "medicion": "📏",
    "refuerzo-de-taludes": "⛰",
    "geosinteticos": "▦",
    "acero-para-hormigon": "▤",
    "mezclas-asfalticas": "▰",
    "equipos-para-obra-civil": "⚒",
    "iluminacion": "✦",
    "adhesivos-y-sellantes": "◉",
    "plomeria": "◌",
    "seguridad-industrial": "⛑",
}

CONTENIDO_POR_DEFECTO = {
    'marca': 'Ferretería Caro-Kahn',
    'home_etiqueta': 'Todo para obra, hogar y mantenimiento',
    'home_titulo': 'Materiales y herramientas que impulsan cada proyecto.',
    'home_descripcion': 'Desde herramientas manuales hasta materiales para construcción, en Ferretería Caro-Kahn encontrarás soluciones confiables para obra, remodelación y mantenimiento diario.',
    'home_cta': 'Explorar catálogo',
    'catalogo_etiqueta': 'Soluciones para tus proyectos',
    'catalogo_titulo': 'Nuestro catálogo técnico',
    'catalogo_descripcion': 'Encuentra herramientas, materiales y accesorios para cada trabajo.',
    'home_beneficios_etiqueta': '¿Por qué elegirnos?',
    'home_beneficios_titulo': 'Más que herramientas, soluciones para cada trabajo.',
    'beneficio_1_titulo': 'Amplio stock',
    'beneficio_1_descripcion': 'Disponibilidad para obra, mantenimiento y uso doméstico.',
    'beneficio_2_titulo': 'Calidad profesional',
    'beneficio_2_descripcion': 'Productos pensados para un uso frecuente y exigente.',
    'beneficio_3_titulo': 'Compra rápida',
    'beneficio_3_descripcion': 'Proceso simple para comparar, agregar y confirmar compras.',
    'home_cta_etiqueta': 'Tu proyecto empieza aquí',
    'home_cta_titulo': 'Encuentra lo que necesitas para construir con confianza.',
    'lista_hero_titulo': 'Materiales y soluciones profesionales para tus proyectos',
    'lista_hero_descripcion': 'Encuentra herramientas, materiales y accesorios con información clara de stock, precios y compra directa.',
    'lista_testimonios_titulo': 'Una compra pensada para profesionales',
    'testimonio_1_texto': 'Encontrar el producto, revisar el stock y agregarlo al carrito es rápido y claro.',
    'testimonio_1_autor': 'Cliente de obra',
    'testimonio_1_rol': 'Compras para construcción',
    'testimonio_2_texto': 'La información del catálogo ayuda a comparar opciones antes de tomar una decisión.',
    'testimonio_2_autor': 'Profesional independiente',
    'testimonio_2_rol': 'Herramientas y mantenimiento',
    'lista_cta_titulo': '¿Listo para empezar tu próximo proyecto?',
    'lista_cta_descripcion': 'Selecciona tus productos, revisa tu carrito y completa tu compra.',
    'footer_descripcion': 'Tu aliado estratégico en materiales y soluciones de construcción profesional.',
}

def index(request):
    productos = _productos_disponibles()
    destacados = productos[:4]
    conteo_categorias = {}
    for producto in productos:
        nombre = producto['categoria'].strip()
        conteo_categorias[nombre] = conteo_categorias.get(nombre, 0) + 1

    categorias = []
    for nombre, cantidad in sorted(
        conteo_categorias.items(),
        key=lambda categoria: categoria[0].casefold(),
    ):
        estilo = slugify(nombre)
        icono = CATEGORIA_VISUAL.get(estilo, "✳")
        categorias.append({
            "nombre": nombre,
            "cantidad": cantidad,
            "estilo": estilo if estilo in CATEGORIA_VISUAL else "general",
            "icono": icono,
        })

    contexto = {
        'productos_destacados': destacados,
        'categorias': categorias,
        'total_productos': len(productos),
    }
    return render(request, 'catalogo/home.html', contexto)

def cargar_contenido():
    contenido_sitio = {
        registro.clave: registro.valor
        for registro in ContenidoSitio.objects.all()
    }
    return {**CONTENIDO_POR_DEFECTO, **contenido_sitio}


def _producto_a_dict(producto):
    return {
        'id': producto.pk,
        'nombre': producto.nombre,
        'categoria': producto.categoria.nombre,
        'precio': int(producto.precio),
        'stock': producto.stock,
        'imagen_url': producto.imagen_url,
        'imagen_archivo': producto.imagen_archivo,
        'descripcion': producto.descripcion,
        'visible': producto.visible,
    }


def _productos_disponibles():
    return [
        _producto_a_dict(producto)
        for producto in Producto.objects.filter(visible=True)
        .select_related('categoria')
        .order_by('pk')
    ]

def lista(request):
    productos = _productos_disponibles()
    busqueda = request.GET.get('q', request.GET.get('nombre', '')).strip()
    categoria_seleccionada = request.GET.get('categoria', '').strip()

    if busqueda:
        texto_busqueda = busqueda.casefold()
        productos = [
            producto for producto in productos
            if texto_busqueda in producto['nombre'].casefold()
        ]

    if categoria_seleccionada:
        categoria_normalizada = categoria_seleccionada.casefold()
        productos = [
            producto for producto in productos
            if producto['categoria'].casefold() == categoria_normalizada
        ]

    # Cálculos para el resumen
    todos_los_productos = _productos_disponibles()
    total_registros = len(productos)
    productos_con_stock = sum(1 for p in productos if p['stock'] > 0)
    categorias = sorted({p['categoria'] for p in todos_los_productos})
    
    contexto = {
        'productos': productos,
        'total_registros': total_registros,
        'productos_con_stock': productos_con_stock,
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_seleccionada': categoria_seleccionada,
    }
    return render(request, 'catalogo/lista.html', contexto)

def admin_landing(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Debes iniciar sesión con una cuenta administradora.')
        return redirect(f"{reverse('login')}?next={reverse('admin_landing')}")

    productos = [
        _producto_a_dict(producto)
        for producto in Producto.objects.select_related('categoria').order_by('pk')
    ]
    contenido = cargar_contenido()
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'guardar_contenido':
            campos = CONTENIDO_POR_DEFECTO.keys()
            contenido.update({campo: request.POST.get(campo, contenido.get(campo, '')) for campo in campos})
            for campo in campos:
                ContenidoSitio.objects.update_or_create(
                    clave=campo,
                    defaults={
                        'valor': contenido[campo],
                        'actualizado_por': request.user,
                    },
                )
            RegistroAdministrativo.registrar(
                usuario=request.user,
                accion=RegistroAdministrativo.Accion.ACTUALIZACION,
                modelo="ContenidoSitio",
                resumen="Se actualizaron los textos visibles de la página.",
            )
            messages.success(request, 'Los textos visibles de la Landingpage fueron actualizados.')
        elif accion == 'guardar_producto':
            try:
                producto_id = int(request.POST.get('producto_id', ''))
                producto = Producto.objects.get(pk=producto_id)
                nombre = request.POST.get('nombre', '').strip()
                categoria_nombre = request.POST.get('categoria', '').strip()
                stock = int(request.POST.get('stock', '0'))
                precio = int(request.POST.get('precio', producto.precio))
                if not nombre or not categoria_nombre:
                    raise ValueError
                if stock < 0 or precio < 0:
                    raise ValueError
                with transaction.atomic():
                    categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                    producto.nombre = nombre
                    producto.categoria = categoria
                    producto.descripcion = request.POST.get('descripcion', '').strip()
                    producto.imagen_url = request.POST.get('imagen_url', '').strip()
                    producto.precio = precio
                    producto.stock = stock
                    producto.visible = request.POST.get('visible') == 'on'
                    producto.full_clean()
                    producto.save()
                RegistroAdministrativo.registrar(
                    usuario=request.user,
                    accion=RegistroAdministrativo.Accion.ACTUALIZACION,
                    modelo="Producto",
                    objeto_id=producto_id,
                    resumen=f'Se actualizó el producto "{producto.nombre}".',
                )
                messages.success(request, f'El producto "{producto.nombre}" fue actualizado.')
            except (Producto.DoesNotExist, TypeError, ValueError, ValidationError):
                messages.error(request, 'No se pudo actualizar el producto. Revisa los campos.')
        elif accion == 'crear_producto':
            try:
                nombre = request.POST.get('nombre', '').strip()
                categoria_nombre = request.POST.get('categoria', '').strip()
                precio = int(request.POST.get('precio', '0'))
                stock = int(request.POST.get('stock', '0'))
                if not nombre or not categoria_nombre or precio < 0 or stock < 0:
                    raise ValueError
                with transaction.atomic():
                    categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                    producto = Producto(
                        nombre=nombre,
                        categoria=categoria,
                        precio=precio,
                        stock=stock,
                        imagen_url=request.POST.get('imagen_url', '').strip(),
                        descripcion=request.POST.get('descripcion', '').strip(),
                        visible=request.POST.get('visible') == 'on',
                    )
                    producto.full_clean()
                    producto.save()
                RegistroAdministrativo.registrar(
                    usuario=request.user,
                    accion=RegistroAdministrativo.Accion.CREACION,
                    modelo="Producto",
                    objeto_id=producto.pk,
                    resumen=f'Se añadió el producto "{nombre}" al catálogo.',
                )
                messages.success(request, f'El producto "{nombre}" fue añadido al catálogo.')
            except (TypeError, ValueError, ValidationError):
                messages.error(request, 'No se pudo añadir el producto. Revisa nombre, precio y stock.')
        elif accion == 'eliminar_producto':
            try:
                producto_id = int(request.POST.get('producto_id', ''))
                producto = Producto.objects.get(pk=producto_id)
                nombre = producto.nombre
                producto.delete()
                carrito = request.session.get('carrito', {})
                carrito.pop(str(producto_id), None)
                request.session['carrito'] = carrito
                request.session.modified = True
                RegistroAdministrativo.registrar(
                    usuario=request.user,
                    accion=RegistroAdministrativo.Accion.ELIMINACION,
                    modelo="Producto",
                    objeto_id=producto_id,
                    resumen=f'Se eliminó el producto "{nombre}" del catálogo.',
                )
                messages.success(request, f'El producto "{nombre}" fue eliminado del catálogo.')
            except (Producto.DoesNotExist, TypeError, ValueError):
                messages.error(request, 'No se pudo eliminar el producto seleccionado.')

    productos = [
        _producto_a_dict(producto)
        for producto in Producto.objects.select_related('categoria').order_by('pk')
    ]
    contenido = cargar_contenido()
    return render(request, 'catalogo/admin_landing.html', {
        'productos': productos,
        'contenido': contenido,
    })

def detalle(request, producto_id):
    productos = _productos_disponibles()
    producto = next((p for p in productos if p['id'] == producto_id), None)
    if not producto:
        raise Http404("Producto no encontrado en la ferretería")

    return render(request, 'catalogo/detalle.html', {'producto': producto})


def _obtener_carrito(request):
    return request.session.get('carrito', {})


def _guardar_carrito(request, carrito):
    request.session['carrito'] = carrito
    request.session.modified = True


def agregar_al_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('detalle', producto_id=producto_id)

    producto = next(
        (producto for producto in _productos_disponibles() if producto['id'] == producto_id),
        None,
    )
    if not producto:
        raise Http404('Producto no encontrado en la ferretería')
    if producto['stock'] <= 0:
        messages.error(request, 'Este producto no tiene stock disponible.')
        return redirect('detalle', producto_id=producto_id)

    try:
        cantidad_solicitada = int(request.POST.get('cantidad', ''))
    except (TypeError, ValueError):
        cantidad_solicitada = 0

    if cantidad_solicitada < 1:
        messages.error(request, 'Ingresa una cantidad entera de al menos 1.')
        return redirect('detalle', producto_id=producto_id)

    carrito = _obtener_carrito(request)
    clave_producto = str(producto_id)
    item_existente = carrito.get(clave_producto, {})
    try:
        cantidad_existente = int(item_existente.get('cantidad', 0))
    except (TypeError, ValueError):
        messages.error(request, 'No se pudo validar la cantidad que ya está en el carrito.')
        return redirect('carrito')

    if cantidad_existente < 0:
        messages.error(request, 'No se pudo validar la cantidad que ya está en el carrito.')
        return redirect('carrito')

    cantidad_total = cantidad_existente + cantidad_solicitada
    if cantidad_total <= producto['stock']:
        carrito[clave_producto] = {
            'id': producto['id'],
            'nombre': producto['nombre'],
            'precio': producto['precio'],
            'cantidad': cantidad_total,
            'imagen_url': producto.get('imagen_url', ''),
        }
        _guardar_carrito(request, carrito)
        messages.success(request, f"Se añadieron {cantidad_solicitada} unidad(es) de {producto['nombre']} al carrito.")
        return redirect('carrito')
    else:
        disponibles = max(producto['stock'] - cantidad_existente, 0)
        messages.warning(request, f'Solo puedes añadir {disponibles} unidad(es) más de este producto.')
    return redirect('detalle', producto_id=producto_id)


def carrito(request):
    items = _items_con_subtotales(request)
    total = sum(item['subtotal'] for item in items)
    return render(request, 'catalogo/carrito.html', {'items_carrito': items, 'total_carrito': total})


def _items_con_subtotales(request):
    items = []
    for item in _obtener_carrito(request).values():
        item_con_subtotal = dict(item)
        item_con_subtotal['subtotal'] = item['precio'] * item['cantidad']
        items.append(item_con_subtotal)
    return items


def vaciar_carrito(request):
    if request.method == 'POST':
        request.session.pop('carrito', None)
        messages.success(request, 'El carrito temporal fue vaciado.')
    return redirect('carrito')


def actualizar_cantidad_carrito(request, producto_id):
    if request.method == 'POST':
        carrito = _obtener_carrito(request)
        clave_producto = str(producto_id)
        if clave_producto not in carrito:
            messages.error(request, 'El producto no está en el carrito.')
            return redirect('carrito')

        producto = next(
            (producto for producto in _productos_disponibles() if producto['id'] == producto_id),
            None,
        )
        try:
            cantidad = int(request.POST.get('cantidad', 0))
        except (TypeError, ValueError):
            cantidad = 0

        if cantidad <= 0:
            carrito.pop(clave_producto, None)
            _guardar_carrito(request, carrito)
            messages.info(request, 'Producto eliminado del carrito.')
        elif not producto:
            messages.error(request, 'Producto no encontrado en la ferretería.')
        elif cantidad > producto['stock']:
            messages.warning(request, f"Solo hay {producto['stock']} unidad(es) disponibles.")
        else:
            carrito[clave_producto]['cantidad'] = cantidad
            _guardar_carrito(request, carrito)
            messages.success(request, 'Cantidad actualizada.')
    return redirect('carrito')


def eliminar_del_carrito(request, producto_id):
    if request.method == 'POST':
        carrito = _obtener_carrito(request)
        if carrito.pop(str(producto_id), None) is not None:
            _guardar_carrito(request, carrito)
            messages.success(request, 'Producto eliminado del carrito.')
    return redirect('carrito')


def login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        contrasena = request.POST.get('contrasena', '')
        usuario_django = authenticate(request, username=usuario, password=contrasena)
        if usuario_django and usuario_django.is_staff:
            auth_login(request, usuario_django)
            request.session['usuario_ficticio'] = usuario_django.get_username()
            messages.success(request, f'Bienvenido/a, {usuario_django.get_username()}.')
            return redirect(request.POST.get('next') or 'admin_landing')

        usuario_registrado = request.session.get('usuario_registrado')
        if (
            usuario
            and usuario_registrado
            and usuario == usuario_registrado.get('usuario')
            and contrasena == usuario_registrado.get('contrasena')
        ):
            request.session['usuario_ficticio'] = usuario
            messages.success(request, f'Bienvenido/a, {usuario}.')
            return redirect(request.POST.get('next') or 'carrito')
        messages.error(request, 'El usuario o la contraseña no son válidos.')
    return render(request, 'catalogo/login.html', {'modo': 'login'})


def registro(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        contrasena = request.POST.get('contrasena', '')
        confirmacion = request.POST.get('confirmacion', '')
        if not usuario or not contrasena:
            messages.error(request, 'Completa el usuario y la contraseña.')
        elif contrasena != confirmacion:
            messages.error(request, 'Las contraseñas no coinciden.')
        else:
            request.session['usuario_registrado'] = {
                'usuario': usuario,
                'contrasena': contrasena,
            }
            request.session['usuario_ficticio'] = usuario
            messages.success(request, f'Cuenta simulada creada para {usuario}.')
            return redirect(request.POST.get('next') or 'lista')
    return render(request, 'catalogo/login.html', {'modo': 'registro'})


def logout(request):
    auth_logout(request)
    request.session.pop('usuario_ficticio', None)
    messages.success(request, 'La sesión simulada fue cerrada.')
    return redirect('lista')


def comprar(request, producto_id):
    if not request.session.get('usuario_ficticio'):
        messages.info(request, 'Inicia sesión para comprar este producto.')
        return redirect(f"{reverse('login')}?next={reverse('comprar', args=[producto_id])}")

    if request.method != 'POST':
        return redirect('detalle', producto_id=producto_id)

    producto = next(
        (producto for producto in _productos_disponibles() if producto['id'] == producto_id),
        None,
    )
    if not producto:
        raise Http404('Producto no encontrado en la ferretería')
    if producto['stock'] <= 0:
        messages.error(request, 'Este producto no tiene stock disponible.')
        return redirect('lista')

    try:
        cantidad = int(request.POST.get('cantidad', ''))
    except (TypeError, ValueError):
        cantidad = 0
    if cantidad < 1:
        messages.error(request, 'Ingresa una cantidad entera de al menos 1.')
        return redirect('detalle', producto_id=producto_id)
    if cantidad > producto['stock']:
        messages.warning(request, f"Solo hay {producto['stock']} unidad(es) disponibles.")
        return redirect('detalle', producto_id=producto_id)

    carrito = _obtener_carrito(request)
    carrito[str(producto_id)] = {
        'id': producto['id'],
        'nombre': producto['nombre'],
        'precio': producto['precio'],
        'cantidad': cantidad,
        'imagen_url': producto.get('imagen_url', ''),
    }
    _guardar_carrito(request, carrito)
    messages.success(request, f"{cantidad} unidad(es) de {producto['nombre']} lista(s) para finalizar la compra.")
    return redirect('checkout')


def pedido_confirmado(request):
    items = request.session.get('ultimo_pedido', [])
    total = sum(item['subtotal'] for item in items)
    return render(request, 'catalogo/pedido_confirmado.html', {
        'items_carrito': items,
        'total_carrito': total,
    })


def checkout(request):
    if not request.session.get('usuario_ficticio'):
        messages.info(request, 'Inicia sesión para finalizar la compra simulada.')
        return redirect(f"{reverse('login')}?next={reverse('checkout')}")

    items = _items_con_subtotales(request)
    if not items:
        messages.info(request, 'Tu carrito está vacío.')
        return redirect('carrito')

    total = sum(item['subtotal'] for item in items)
    if request.method == 'POST':
        usuario = request.user if request.user.is_authenticated else None
        with transaction.atomic():
            productos = {
                producto.pk: producto
                for producto in Producto.objects.filter(
                    pk__in=[item['id'] for item in items],
                    visible=True,
                ).select_for_update()
            }
            for item in items:
                producto = productos.get(item['id'])
                if producto is None or item['cantidad'] > producto.stock:
                    messages.error(
                        request,
                        f"El stock de {item['nombre']} cambió y ya no alcanza para completar el pedido.",
                    )
                    return redirect('carrito')

            for item in items:
                producto = productos[item['id']]
                producto.stock -= item['cantidad']
                producto.save(update_fields=('stock', 'actualizado_en'))

            Pedido.registrar_compra(
                items,
                nombre_cliente=request.session['usuario_ficticio'],
                usuario=usuario,
            )

        request.session['ultimo_pedido'] = items
        request.session.pop('carrito', None)
        messages.success(request, 'Pedido confirmado correctamente (simulación).')
        return redirect('pedido_confirmado')

    return render(request, 'catalogo/checkout.html', {'items_carrito': items, 'total_carrito': total})
