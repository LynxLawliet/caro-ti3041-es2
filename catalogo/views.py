from django.shortcuts import redirect, render
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.urls import reverse
import json
import os
from django.conf import settings

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
    productos = _productos_con_stock_temporal(request)
    destacados = productos[:4]
    categorias = sorted({producto['categoria'] for producto in productos})
    contexto = {
        'productos_destacados': destacados,
        'categorias': categorias,
        'total_productos': len(productos),
    }
    return render(request, 'catalogo/home.html', contexto)

# Función auxiliar para leer el JSON
def cargar_datos():
    ruta = os.path.join(settings.BASE_DIR, 'catalogo', 'data', 'productos.json')
    with open(ruta, 'r', encoding='utf-8') as f:
        productos = json.load(f)
    for producto in productos:
        producto.setdefault('descripcion', '')
        producto.setdefault('visible', True)
    return productos


def cargar_contenido():
    ruta = os.path.join(settings.BASE_DIR, 'catalogo', 'data', 'contenido.json')
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        contenido = {}
    return {**CONTENIDO_POR_DEFECTO, **contenido}


def guardar_json(nombre, datos):
    ruta = os.path.join(settings.BASE_DIR, 'catalogo', 'data', nombre)
    temporal = f'{ruta}.tmp'
    with open(temporal, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(temporal, ruta)


def _productos_con_stock_temporal(request):
    productos = cargar_datos()
    stock_temporal = request.session.get('stock_temporal', {})
    for producto in productos:
        clave_producto = str(producto['id'])
        if clave_producto in stock_temporal:
            producto['stock'] = stock_temporal[clave_producto]
    return [producto for producto in productos if producto.get('visible', True)]

def lista(request):
    productos = _productos_con_stock_temporal(request)
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
    todos_los_productos = _productos_con_stock_temporal(request)
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

    productos = cargar_datos()
    contenido = cargar_contenido()
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'guardar_contenido':
            campos = CONTENIDO_POR_DEFECTO.keys()
            contenido.update({campo: request.POST.get(campo, contenido.get(campo, '')) for campo in campos})
            guardar_json('contenido.json', contenido)
            messages.success(request, 'Los textos visibles de la Landingpage fueron actualizados.')
        elif accion == 'guardar_producto':
            try:
                producto_id = int(request.POST.get('producto_id', ''))
                producto = next(producto for producto in productos if producto['id'] == producto_id)
                stock = int(request.POST.get('stock', '0'))
                precio = int(request.POST.get('precio', producto.get('precio', 0)))
                if stock < 0 or precio < 0:
                    raise ValueError
                producto['nombre'] = request.POST.get('nombre', '').strip()
                producto['categoria'] = request.POST.get('categoria', '').strip()
                producto['descripcion'] = request.POST.get('descripcion', '').strip()
                producto['imagen_url'] = request.POST.get('imagen_url', '').strip()
                producto['precio'] = precio
                producto['stock'] = stock
                producto['visible'] = request.POST.get('visible') == 'on'
                if not producto['nombre'] or not producto['categoria']:
                    raise ValueError
                guardar_json('productos.json', productos)
                stock_temporal = request.session.get('stock_temporal', {})
                stock_temporal.pop(str(producto_id), None)
                request.session['stock_temporal'] = stock_temporal
                request.session.modified = True
                messages.success(request, f'El producto "{producto["nombre"]}" fue actualizado.')
            except (StopIteration, TypeError, ValueError):
                messages.error(request, 'No se pudo actualizar el producto. Revisa los campos.')
        elif accion == 'crear_producto':
            try:
                nombre = request.POST.get('nombre', '').strip()
                categoria = request.POST.get('categoria', '').strip()
                precio = int(request.POST.get('precio', '0'))
                stock = int(request.POST.get('stock', '0'))
                if not nombre or not categoria or precio < 0 or stock < 0:
                    raise ValueError
                nuevo_id = max((producto['id'] for producto in productos), default=0) + 1
                productos.append({
                    'id': nuevo_id,
                    'nombre': nombre,
                    'categoria': categoria,
                    'precio': precio,
                    'stock': stock,
                    'imagen_url': request.POST.get('imagen_url', '').strip(),
                    'imagen_archivo': '',
                    'descripcion': request.POST.get('descripcion', ''),
                    'visible': request.POST.get('visible') == 'on',
                })
                guardar_json('productos.json', productos)
                messages.success(request, f'El producto "{nombre}" fue añadido al catálogo.')
            except (TypeError, ValueError):
                messages.error(request, 'No se pudo añadir el producto. Revisa nombre, precio y stock.')
        elif accion == 'eliminar_producto':
            try:
                producto_id = int(request.POST.get('producto_id', ''))
                producto = next(producto for producto in productos if producto['id'] == producto_id)
                productos = [producto_actual for producto_actual in productos if producto_actual['id'] != producto_id]
                guardar_json('productos.json', productos)
                carrito = request.session.get('carrito', {})
                carrito.pop(str(producto_id), None)
                request.session['carrito'] = carrito
                stock_temporal = request.session.get('stock_temporal', {})
                stock_temporal.pop(str(producto_id), None)
                request.session['stock_temporal'] = stock_temporal
                request.session.modified = True
                messages.success(request, f'El producto "{producto["nombre"]}" fue eliminado del catálogo.')
            except (StopIteration, TypeError, ValueError):
                messages.error(request, 'No se pudo eliminar el producto seleccionado.')

    return render(request, 'catalogo/admin_landing.html', {
        'productos': productos,
        'contenido': contenido,
    })

def detalle(request, producto_id):
    productos = _productos_con_stock_temporal(request)
    # Buscar el producto por id
    producto = next((p for p in productos if p['id'] == producto_id), None)
    
    if not producto:
        raise Http404("Producto no encontrado en la ferretería") # Manejo de caso inexistente
        
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
        (producto for producto in _productos_con_stock_temporal(request) if producto['id'] == producto_id),
        None,
    )
    if not producto:
        raise Http404('Producto no encontrado en la ferretería')
    if producto['stock'] <= 0:
        messages.error(request, 'Este producto no tiene stock disponible.')
        return redirect('detalle', producto_id=producto_id)

    try:
        cantidad_solicitada = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad_solicitada = 0

    if cantidad_solicitada < 1:
        messages.error(request, 'La cantidad debe ser al menos 1.')
        return redirect('detalle', producto_id=producto_id)

    carrito = _obtener_carrito(request)
    clave_producto = str(producto_id)
    item = carrito.get(clave_producto, {
        'id': producto['id'],
        'nombre': producto['nombre'],
        'precio': producto['precio'],
        'cantidad': 0,
    })
    cantidad_total = item['cantidad'] + cantidad_solicitada
    if cantidad_total <= producto['stock']:
        item['cantidad'] = cantidad_total
        carrito[clave_producto] = item
        _guardar_carrito(request, carrito)
        messages.success(request, f"Se añadieron {cantidad_solicitada} unidad(es) de {producto['nombre']} al carrito.")
    else:
        disponibles = max(producto['stock'] - item['cantidad'], 0)
        messages.warning(request, f'Solo puedes añadir {disponibles} unidad(es) más de este producto.')
    return redirect('detalle', producto_id=producto_id)


def carrito(request):
    items = _items_con_subtotales(request)
    total = sum(item['precio'] * item['cantidad'] for item in items)
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
            (producto for producto in _productos_con_stock_temporal(request) if producto['id'] == producto_id),
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
        (producto for producto in _productos_con_stock_temporal(request) if producto['id'] == producto_id),
        None,
    )
    if not producto:
        raise Http404('Producto no encontrado en la ferretería')
    if producto['stock'] <= 0:
        messages.error(request, 'Este producto no tiene stock disponible.')
        return redirect('lista')

    try:
        cantidad = max(1, int(request.POST.get('cantidad', 1)))
    except (TypeError, ValueError):
        cantidad = 1
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

    total = sum(item['precio'] * item['cantidad'] for item in items)
    if request.method == 'POST':
        stock_temporal = request.session.get('stock_temporal', {})
        for item in items:
            clave_producto = str(item['id'])
            stock_actual = next(
                (producto['stock'] for producto in _productos_con_stock_temporal(request) if producto['id'] == item['id']),
                0,
            )
            if item['cantidad'] > stock_actual:
                messages.error(request, f"El stock de {item['nombre']} cambió y ya no alcanza para completar el pedido.")
                return redirect('carrito')
            stock_temporal[clave_producto] = stock_actual - item['cantidad']

        request.session['stock_temporal'] = stock_temporal
        request.session['ultimo_pedido'] = items
        request.session.pop('carrito', None)
        messages.success(request, 'Pedido confirmado correctamente (simulación).')
        return redirect('pedido_confirmado')

    return render(request, 'catalogo/checkout.html', {'items_carrito': items, 'total_carrito': total})

