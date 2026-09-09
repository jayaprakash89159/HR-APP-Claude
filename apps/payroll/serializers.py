from django.db.models import Q
from rest_framework import serializers

from apps.employees.models import Employee

from .models import EmployeeSalary, SalaryComponent, SalaryStructure, SalaryStructureComponent


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = [
            'id', 'name', 'code', 'component_type', 'calculation_type', 'fixed_amount', 'percentage',
            'formula', 'is_taxable', 'is_statutory', 'is_pf_applicable',
            'is_esi_applicable', 'display_order', 'is_active',
        ]

    def validate(self, attrs):
        calculation_type = attrs.get('calculation_type', getattr(self.instance, 'calculation_type', 'fixed'))
        percentage = attrs.get('percentage', getattr(self.instance, 'percentage', 0))
        formula = attrs.get('formula', getattr(self.instance, 'formula', ''))
        if calculation_type in ('percentage', 'percentage_ctc') and percentage <= 0:
            raise serializers.ValidationError({'percentage': 'A percentage component must be greater than zero.'})
        if calculation_type == 'formula' and not formula.strip():
            raise serializers.ValidationError({'formula': 'Formula components require a formula.'})
        if calculation_type != 'formula' and formula.strip():
            raise serializers.ValidationError({'formula': 'Only formula components may define a formula.'})
        return attrs


class SalaryStructureComponentSerializer(serializers.ModelSerializer):
    component = SalaryComponentSerializer(read_only=True)
    component_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = SalaryStructureComponent
        fields = ['id', 'component', 'component_id', 'display_order', 'is_active']


class SalaryStructureSerializer(serializers.ModelSerializer):
    components = SalaryStructureComponentSerializer(many=True, read_only=True)
    component_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)

    class Meta:
        model = SalaryStructure
        fields = ['id', 'name', 'code', 'description', 'is_active', 'created_at', 'components', 'component_ids']
        read_only_fields = ['id', 'created_at']

    def validate_component_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError('A salary component cannot be assigned twice.')
        found = set(SalaryComponent.objects.filter(id__in=value, is_active=True).values_list('id', flat=True))
        missing = set(value) - found
        if missing:
            raise serializers.ValidationError('Every component must exist and be active.')
        return value

    def create(self, validated_data):
        component_ids = validated_data.pop('component_ids', [])
        structure = super().create(validated_data)
        self._save_components(structure, component_ids)
        return structure

    def update(self, instance, validated_data):
        component_ids = validated_data.pop('component_ids', None)
        structure = super().update(instance, validated_data)
        if component_ids is not None:
            structure.components.all().delete()
            self._save_components(structure, component_ids)
        return structure

    @staticmethod
    def _save_components(structure, component_ids):
        SalaryStructureComponent.objects.bulk_create([
            SalaryStructureComponent(salary_structure=structure, component_id=component_id, display_order=index)
            for index, component_id in enumerate(component_ids)
        ])


class EmployeeSalarySerializer(serializers.ModelSerializer):
    employee_id = serializers.UUIDField(write_only=True)
    employee = serializers.SerializerMethodField(read_only=True)
    revised_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EmployeeSalary
        fields = [
            'id', 'employee', 'employee_id', 'salary_structure', 'ctc', 'monthly_ctc',
            'basic', 'hra', 'special_allowance', 'medical_allowance',
            'conveyance_allowance', 'other_allowances', 'gross_salary',
            'effective_from', 'effective_to', 'salary_type', 'revision_reason',
            'is_active', 'revised_by', 'created_at',
        ]
        read_only_fields = ['id', 'revised_by', 'created_at']

    def get_employee(self, obj):
        return {
            'id': str(obj.employee_id),
            'employee_code': obj.employee.employee_code,
            'name': obj.employee.get_full_name(),
        }

    def validate(self, attrs):
        employee_id = attrs.get('employee_id', getattr(self.instance, 'employee_id', None))
        from_date = attrs.get('effective_from', getattr(self.instance, 'effective_from', None))
        to_date = attrs.get('effective_to', getattr(self.instance, 'effective_to', None))
        if to_date and from_date and to_date < from_date:
            raise serializers.ValidationError({'effective_to': 'Effective-to date must be on or after effective-from date.'})
        if attrs.get('ctc', getattr(self.instance, 'ctc', 0)) < 0 or attrs.get('monthly_ctc', getattr(self.instance, 'monthly_ctc', 0)) < 0:
            raise serializers.ValidationError('CTC values cannot be negative.')
        if employee_id:
            overlap = EmployeeSalary.objects.filter(employee_id=employee_id, is_active=True)
            if self.instance:
                overlap = overlap.exclude(pk=self.instance.pk)
            if not to_date:
                overlap = overlap.filter(Q(effective_to__isnull=True) | Q(effective_to__gte=from_date))
            else:
                overlap = overlap.filter(effective_from__lte=to_date).filter(
                    Q(effective_to__isnull=True) | Q(effective_to__gte=from_date)
                )
            if overlap.exists():
                raise serializers.ValidationError('This employee already has an overlapping active salary record.')
        return attrs

    def create(self, validated_data):
        employee_id = validated_data.pop('employee_id')
        try:
            employee = Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            raise serializers.ValidationError({'employee_id': 'Employee not found.'})
        validated_data['employee'] = employee
        validated_data['revised_by'] = self.context['request'].user
        return super().create(validated_data)