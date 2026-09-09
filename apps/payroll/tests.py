from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase, override_settings

from .services.calculator import _working_dates
from .services.formula import UnsafeFormulaError, evaluate_formula
from .services.statutory import calculate_statutory


class PayrollCalculationUtilityTests(SimpleTestCase):
    def test_working_dates_exclude_weekends_and_holidays(self):
        dates = _working_dates(date(2026, 9, 7), date(2026, 9, 13), {date(2026, 9, 9)})
        self.assertEqual(dates, [date(2026, 9, 7), date(2026, 9, 8), date(2026, 9, 10), date(2026, 9, 11)])

    @override_settings(PAYROLL_STATUTORY_RULES={})
    def test_statutory_values_are_zero_without_explicit_rules(self):
        class Statutory:
            is_pf_applicable = True
            is_esi_applicable = True
            is_pt_applicable = True

        class Employee:
            statutory = Statutory()

        result = calculate_statutory(Employee(), Decimal('50000'), Decimal('70000'))
        self.assertEqual(result['pf_employee'], Decimal('0'))
        self.assertEqual(result['esi_employee'], Decimal('0'))
        self.assertEqual(result['professional_tax'], Decimal('0'))

    @override_settings(PAYROLL_STATUTORY_RULES={
        'pf': {'enabled': True, 'employee_rate': '12', 'employer_rate': '12', 'wage_ceiling': '15000'},
    })
    def test_explicit_pf_rule_is_applied(self):
        class Statutory:
            is_pf_applicable = True
            is_esi_applicable = False
            is_pt_applicable = False

        class Employee:
            statutory = Statutory()

        result = calculate_statutory(Employee(), Decimal('50000'), Decimal('70000'))
        self.assertEqual(result['pf_employee'], Decimal('1800.00'))
        self.assertEqual(result['pf_employer'], Decimal('1800.00'))

    def test_formula_evaluator_supports_approved_arithmetic(self):
        self.assertEqual(evaluate_formula('basic * 0.1 + 25', {'basic': 1000}), Decimal('125.0'))

    def test_formula_evaluator_rejects_attribute_access(self):
        with self.assertRaises(UnsafeFormulaError):
            evaluate_formula("__import__('os').system('whoami')", {})
