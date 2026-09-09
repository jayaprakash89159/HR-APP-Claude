from rest_framework import serializers

from .models import PayrollPeriod


class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = [
            'id', 'name', 'month', 'year', 'from_date', 'to_date', 'status',
            'total_employees', 'total_gross', 'total_deductions', 'total_net',
            'processed_at', 'processed_by', 'approved_at', 'approved_by',
            'released_at', 'released_by', 'paid_at', 'paid_by', 'locked_at',
            'locked_by', 'rejection_reason', 'remarks', 'created_at',
        ]
        read_only_fields = [
            'id', 'status', 'total_employees', 'total_gross', 'total_deductions',
            'total_net', 'processed_at', 'processed_by', 'approved_at',
            'approved_by', 'released_at', 'released_by', 'paid_at', 'paid_by',
            'locked_at', 'locked_by', 'created_at',
        ]

    def validate(self, attrs):
        month = attrs.get('month', getattr(self.instance, 'month', None))
        year = attrs.get('year', getattr(self.instance, 'year', None))
        from_date = attrs.get('from_date', getattr(self.instance, 'from_date', None))
        to_date = attrs.get('to_date', getattr(self.instance, 'to_date', None))
        if month is None or month < 1 or month > 12:
            raise serializers.ValidationError({'month': 'Month must be between 1 and 12.'})
        if from_date and to_date and from_date > to_date:
            raise serializers.ValidationError({'to_date': 'Period end date must be on or after the start date.'})
        duplicate = PayrollPeriod.objects.filter(month=month, year=year)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
            if self.instance.status != 'draft' and any(field in attrs for field in ('month', 'year', 'from_date', 'to_date')):
                raise serializers.ValidationError('Only draft periods can change their dates.')
        if duplicate.exists():
            raise serializers.ValidationError('A payroll period already exists for this month and year.')
        return attrs