Explica las instrucciones del archivo adjunto // Explica a detalle y dame los comandos necesarios para la "Etapa 0" //
Recomienda un "Prompt" para cumplir con las siguientes características: ...... Según el archivo.
 
Consulta 1:

"Actúa como un desarrollador backend generando datos de prueba. Necesito que crees un arreglo JSON válido con exactamente 40 objetos que representen el catálogo de una ferretería.
Cada objeto debe contener obligatoriamente los siguientes campos:  id: un número entero secuencial del 1 al 40.nombre: el nombre del producto (sé variado y realista).categoria: la clasificación del artículo (ej. Herramientas manuales, Fijaciones).precio: un número entero positivo en pesos chilenos.stock: un número entero entre 0 y 50. Es fundamental que al menos 5 productos tengan el stock en "0" para poder probar la lógica condicional visual de la interfaz.
Devuelve únicamente el arreglo JSON, sin explicaciones adicionales ni bloques de texto."

Respuesta de la IA: Entregó un arreglo JSON válido con 40 objetos estructurados con los campos solicitados y variaciones de stock, incluyendo valores en cero.

Qué se usó o modificó: Se utilizó el código generado tal cual para crear el archivo productos.json, aunque se revisaron manualmente los montos de los precios para asegurar que fueran realistas para el mercado chileno.

Consulta 2:

"Actúa como un desarrollador front end experto en Django. Necesito diseñar la interfaz para un catálogo web de una ferretería utilizando Django Template Language (DTL).

Requisitos técnicos y de diseño:
1. Genera dos archivos:
   - 'base.html': Plantilla base que incluya un encabezado con el nombre de la ferretería, barra de navegación simple, bloque {% block content %} y un pie de página. Usa Bootstrap 5 vía CDN para los estilos.
   - 'lista.html': Plantilla que herede de 'base.html'. Debe mostrar una cuadrícula responsiva (cards) que itere una lista de objetos 'productos' usando un bucle {% for producto in productos %}.
2. Cada tarjeta de producto debe mostrar:
   - Nombre del producto
   - Categoría
   - Precio formateado
   - Stock disponible
   - Un botón o enlace que apunte a la vista de detalle: {% url 'detalle' producto.id %}
3. Entrega el código HTML limpio, semántico y listo para copiar en la carpeta de templates."

Respuesta de la IA: Generó el código base con las etiquetas de herencia ({% extends %}, {% block content %}) y un bucle {% for %} básico, utilizando clases del framework Bootstrap 5.

Qué se usó o modificó: Se extrajo únicamente la lógica de sintaxis de Django (bucle condicionales y URLs). Se descartó por completo el código de Bootstrap propuesto, ya que se optó por construir un diseño propio con CSS puro.

Consulta 3:

"Actúa como un desarrollador Front End Senior. Necesito estructurar y añadir nuevas funcionalidades visuales a la Landing Page (plantillas base.html y lista.html) de un proyecto académico en Django. El sitio es un catálogo online para una ferretería enfocada en materiales técnicos e infraestructura.

Necesito que me generes el código HTML semántico y el CSS puro (sin frameworks como Bootstrap) considerando los siguientes requerimientos:

Nuevas Funciones en la Interfaz:

Diseña una 'Barra de Búsqueda' simulada en el encabezado (header).

Crea una barra lateral (aside) o sección superior de 'Filtros Rápidos' utilizando botones o etiquetas (ej. Herramientas Manuales, Diseño Estructural de Pavimentos, Insumos para Refuerzo de Taludes, Mezclas Asfálticas).

Añade un pie de página (footer) con enlaces de contacto y un diseño corporativo.

Estructura HTML y CSS:

Utiliza CSS Grid para organizar el listado de productos de forma fluida.

Utiliza Flexbox para el encabezado y la alineación de los filtros.

La paleta de colores debe ser profesional e industrial: tonos grises asfalto, blanco para lectura clara y un color de acento de alta visibilidad (como naranja o amarillo de seguridad).

Todo el CSS debe estar debidamente comentado y ordenado por secciones (Variables, Globales, Layout, Componentes).

Integración con Django:

El código debe respetar la sintaxis de herencia de templates ({% block content %}, {% extends %}).

Por favor, entrégame el código de base.html y lista.html por separado, y explica brevemente cómo esta estructura mejora la mantenibilidad del proyecto."

Respuesta de la IA: Proporcionó una estructura semántica y un bloque de estilos CSS puro organizado por variables, enfocándose en una paleta de colores industrial y un diseño responsivo utilizando CSS Grid.

Qué se usó o modificó: Se integró el código CSS en la etiqueta <style> de base.html. Se modificaron las variables de color hexadecimales (--acento, --asfalto) para ajustarlas a la identidad del catálogo y se adaptaron los nombres de las clases para que coincidieran con el HTML previo.

Consulta 4:

"Actúa como un desarrollador experto en Django y frontend. Estoy construyendo la Etapa 3 de un catálogo web de ferretería. La restricción técnica principal es que no puedo usar modelos ni conexión a base de datos; todos los productos se procesan desde un archivo productos.json leído en views.py.

Necesito que me entregues el código de las vistas (views.py) y los templates (HTML/JS) para simular las siguientes cuatro funcionalidades sin romper la restricción de la base de datos:

Imágenes: Modifica la estructura de mi JSON actual para incluir un campo imagen_url con enlaces a imágenes de placeholder gratuitas enfocadas en materiales de construcción, herramientas o infraestructura vial. Actualiza el template para renderizarlas.

Filtro Dinámico: Crea un script en JavaScript puro para lista.html que permita filtrar en tiempo real las tarjetas de productos por categoria y por rango de precio, ocultando los elementos del DOM dinámicamente sin recargar la página ni hacer consultas al backend.

Simulación de Compra: Diseña un botón de 'Añadir al carro' en la vista de detalle. Al hacer clic, utiliza la API de localStorage de JavaScript para guardar temporalmente los productos seleccionados y muestra un modal confirmando la reserva del pedido, simulando el proceso de forma estática.

Panel de Administración (Mockup): Crea una ruta, una vista y un template llamado admin_landing.html. Debe lucir como un panel de control con un formulario HTML que simule la edición del título de la página principal. Al enviar el formulario mediante POST, la vista debe simplemente retornar un mensaje de éxito usando el framework messages de Django, sin guardar nada en disco."

Respuesta de la IA: La herramienta generó un bloque de código extenso que incluía la actualización del archivo JSON con enlaces a imágenes de prueba, un script en JavaScript para filtrar tarjetas en el frontend, y toda la lógica (vistas, rutas y HTML) para simular un carrito de compras y un panel de control estático.  

Qué se usó o modificó: Se integró únicamente el campo de imágenes en el JSON y el script de JavaScript puro para el filtro dinámico, ya que representan una mejora visual válida para la Etapa 3 que opera exclusivamente en el lado del cliente. Se descartó y eliminó por completo todo el código relacionado con el carrito de compras, el inicio de sesión y el panel de administración, ya que estos elementos excedían los límites de las instrucciones de la evaluación y añadían rutas innecesarias que podían generar errores de ejecución.

Consulta 5:

Actúa como un desarrollador Front End Senior experto en Django Template Language y diseño web moderno.

Necesito rediseñar y reestructurar mi catálogo web de ferretería en Django (nombre: 'Ferretería Caro-Kahn') para transformarlo de un listado simple en una Landing Page moderna, persuasiva y estéticamente atractiva, completamente en español.

Requisitos de Estructura y Contenido (Landing Page):

Diseña una estructura persuasiva que incluya las siguientes secciones principales:

Sección Héroe (Hero Section): Un encabezado de pantalla completa con un título impactante (ej: "Materiales y Soluciones Profesionales para tus Proyectos de Construcción"), una descripción convincente y un botón de Llamado a la Acción (CTA) grande y visible (ej: "Explora Nuestro Catálogo Técnico").

Sección de Beneficios (Why Us): Tres o cuatro tarjetas minimalistas que expliquen las ventajas competitivas de la ferretería (ej: "Asesoría Técnica Experta", "Stock Garantizado", "Envío Directo a Obra", "Calidad Certificada").

Sección del Catálogo (Adaptada): Integra la cuadrícula de productos existente, pero con un diseño de tarjetas (cards) mucho más limpio y atractivo. Mantén el bucle {% for producto in productos %}, pero cada tarjeta debe tener una imagen grande (simulada con placehold.co), nombre, categoría, precio formateado y un botón de detalle elegante.

Sección de Testimonios (Mockup): Una sección estática simulando opiniones de clientes satisfechos (ingenieros, constructores) para generar confianza.

Sección de Llamado a la Acción Final: Un panel de cierre invitando a cotizar, contactar o descargar un catálogo técnico.

Estética Moderna y Detalles Visuales:

Utiliza CSS puro (sin frameworks como Bootstrap) para un diseño minimalista y ligero.

Aplica una cuadrícula responsiva (CSS Grid) para el catálogo y Flexbox para el layout general.

Elige una paleta de colores profesional e industrial, inspirada en las capturas previas: grises asfalto (`#252a2e`), blanco para claridad (`#ffffff`) y un color de acento de alta visibilidad como naranja o amarillo seguridad (`#f5a900`).

Utiliza una tipografía moderna sans-serif legible (como Segoe UI o similar).

Añade micro-interacciones sutiles, como efectos de `hover` suaves en las tarjetas y botones, y un diseño "aireado" con buen uso de espacios en blanco.

Integración con Django:

El código debe respetar la sintaxis de herencia de templates ({% block content %}, {% extends 'catalogo/base.html' %}).

Por favor, entrégame el código de `base.html` y `lista.html` (o `landing.html`, si prefieres renombrarlo) por separado, con todo el CSS incrustado en `<style>` en `base.html` y `<style scoped>` o similar en `lista.html` (o el CSS separado y explicado cómo integrarlo).

Explica brevemente cómo esta estructura mejora la mantenibilidad del proyecto.

Respuesta de la IA:
Entregó el código completo para base.html y lista.html, estructurando una Landing Page completa que incluía la Sección Héroe, tarjetas de beneficios, el catálogo con CSS Grid, testimonios y un llamado a la acción final, aplicando correctamente la paleta de colores asfalto/amarillo y la sintaxis de Django.

Qué se usó o modificó:
Se extrajo y utilizó el CSS puro para la cuadrícula responsiva (Grid) de las tarjetas de productos y la estructuración del encabezado. Sin embargo, se eliminaron por completo las secciones de "Héroe", "Beneficios", "Testimonios" y "Llamado a la Acción Final", ya que añadían contenido estático que excedía el alcance de las instrucciones de la evaluación. El código se redujo para mantener únicamente la visualización del catálogo y el resumen calculado, asegurando el cumplimiento estricto de la rúbrica.

Conclusión:

Durante el desarrollo de esta primera evaluación en los laboratorios de INACAP Sede Osorno, utilicé la Inteligencia Artificial principalmente como una herramienta para acelerar la escritura de código repetitivo y maquetar el diseño front-end. Le pedí generar los 40 registros en formato JSON porque inventar cada material de ferretería a mano habría consumido demasiado tiempo de la prueba. Esa respuesta me sirvió tal cual, permitiéndome enfocarme en la lógica de views.py. Por otro lado, al solicitar el diseño de la interfaz, la IA tendía a sobre-complicar el código sugiriendo el uso de Bootstrap o inventando funcionalidades fuera de alcance, como sistemas de carrito de compras o paneles de administración. Tuve que corregir exhaustivamente esas respuestas, eliminando todo el código sobrante para no romper la restricción de la evaluación, que exige trabajar sin base de datos. En este proceso aprendí que es vital aplicar un filtro crítico a las respuestas de la IA, asegurándome de extraer únicamente la herencia de plantillas, el bucle de iteración y el CSS puro que necesitaba para cumplir estrictamente con la mejora visual.