from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Ace', '0004_ace_quantity_alter_ace_designation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ace',
            name='asset_number',
            field=models.TextField(blank=True, null=True),
        ),
    ]
