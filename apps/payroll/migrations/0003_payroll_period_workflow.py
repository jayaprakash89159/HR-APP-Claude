from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('payroll', '0002_salary_administration')]

    operations = [
        migrations.AddField(model_name='payrollperiod', name='released_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='payrollperiod', name='paid_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='payrollperiod', name='locked_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='payrollperiod', name='rejection_reason', field=models.TextField(blank=True)),
        migrations.AddField(model_name='payrollperiod', name='released_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='released_payrolls', to='authentication.user')),
        migrations.AddField(model_name='payrollperiod', name='paid_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paid_payrolls', to='authentication.user')),
        migrations.AddField(model_name='payrollperiod', name='locked_by', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_payrolls', to='authentication.user')),
    ]