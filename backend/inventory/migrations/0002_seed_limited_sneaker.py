from django.db import migrations


def seed_inventory(apps, schema_editor):
    Inventory = apps.get_model("inventory", "Inventory")
    Inventory.objects.get_or_create(
        sku="limited-edition-sneaker",
        defaults={"total_stock": 20, "available_stock": 20},
    )


def reverse_seed_inventory(apps, schema_editor):
    Inventory = apps.get_model("inventory", "Inventory")
    Inventory.objects.filter(sku="limited-edition-sneaker").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_inventory, reverse_seed_inventory),
    ]
