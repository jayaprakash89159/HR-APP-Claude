from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [('payroll', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='SalaryStructureComponent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='structures', to='payroll.salarycomponent')),
                ('salary_structure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='components', to='payroll.salarystructure')),
            ],
            options={
                'db_table': 'hr_salary_structure_components',
                'ordering': ['display_order', 'component__display_order', 'component__name'],
            },
        ),
        migrations.AddField(
            model_name='employeesalary',
            name='revision_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddConstraint(
            model_name='salarystructurecomponent',
            constraint=models.UniqueConstraint(fields=('salary_structure', 'component'), name='unique_salary_structure_component'),
        ),
    ]