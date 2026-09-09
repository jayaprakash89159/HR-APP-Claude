from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('payroll', '0004_payroll_calculation_details')]

    operations = [
        migrations.AddField(
            model_name='salarycomponent',
            name='fixed_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]