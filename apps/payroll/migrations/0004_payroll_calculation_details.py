from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('payroll', '0003_payroll_period_workflow')]

    operations = [
        migrations.AddField(model_name='paysliprecord', name='calculation_details', field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name='paysliprecord', name='released_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='paysliprecord', name='released_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='released_payslips', to='authentication.user')),
    ]