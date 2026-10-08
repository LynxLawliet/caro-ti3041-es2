import json
from pathlib import Path

from django.core.management.color import no_style
from django.db import migrations


def import_json_catalog(apps, schema_editor):
    categoria_model = apps.get_model("catalogo", "Categoria")
    producto_model = apps.get_model("catalogo", "Producto")
    contenido_model = apps.get_model("catalogo", "ContenidoSitio")

    data_dir = Path(__file__).resolve().parents[1] / "data"
    productos = json.loads((data_dir / "productos.json").read_text(encoding="utf-8"))
    contenido = json.loads((data_dir / "contenido.json").read_text(encoding="utf-8"))

    for item in productos:
        categoria, _ = categoria_model.objects.using(schema_editor.connection.alias).get_or_create(
            nombre=item["categoria"]
        )
        producto_model.objects.using(schema_editor.connection.alias).get_or_create(
            pk=item["id"],
            defaults={
                "nombre": item["nombre"],
                "categoria": categoria,
                "precio": item["precio"],
                "stock": item["stock"],
                "imagen_url": item.get("imagen_url", ""),
                "imagen_archivo": item.get("imagen_archivo", ""),
                "descripcion": item.get("descripcion", ""),
                "visible": item.get("visible", True),
            },
        )

    for clave, valor in contenido.items():
        contenido_model.objects.using(schema_editor.connection.alias).get_or_create(
            clave=clave,
            defaults={"valor": valor},
        )

    sequence_sql = schema_editor.connection.ops.sequence_reset_sql(
        no_style(),
        [categoria_model, producto_model, contenido_model],
    )
    for statement in sequence_sql:
        schema_editor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [
        ("catalogo", "0002_contenidositio_registroadministrativo"),
    ]

    operations = [
        migrations.RunPython(import_json_catalog, migrations.RunPython.noop),
    ]
