from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


CENT = Decimal('0.01')


def calculate_statutory(employee, basic, gross):
    """Apply only explicitly configured statutory rules.

    Rules belong in deployment settings because statutory rates and ceilings
    vary by jurisdiction and change over time. Missing rules produce zero,
    never an invented legal calculation.
    """
    configured = getattr(settings, 'PAYROLL_STATUTORY_RULES', {})
    profile = getattr(employee, 'statutory', None)
    result = {
        'pf_employee': Decimal('0'), 'pf_employer': Decimal('0'),
        'esi_employee': Decimal('0'), 'esi_employer': Decimal('0'),
        'professional_tax': Decimal('0'), 'tds': Decimal('0'),
        'lwf_employee': Decimal('0'), 'lwf_employer': Decimal('0'),
        'details': {'configured_rules': sorted(configured.keys())},
    }
    if profile is None:
        result['details']['warning'] = 'Employee statutory profile is missing.'
        return result

    result['pf_employee'], result['pf_employer'] = _contribution(
        configured.get('pf'), basic, getattr(profile, 'is_pf_applicable', False)
    )
    result['esi_employee'], result['esi_employer'] = _contribution(
        configured.get('esi'), gross, getattr(profile, 'is_esi_applicable', False)
    )
    result['professional_tax'] = _fixed_rule(
        configured.get('professional_tax'), getattr(profile, 'is_pt_applicable', False)
    )
    result['tds'] = _fixed_rule(configured.get('tds'), True)
    result['lwf_employee'] = _fixed_rule(
        configured.get('lwf_employee'), getattr(profile, 'is_pt_applicable', False)
    )
    result['lwf_employer'] = _fixed_rule(configured.get('lwf_employer'), True)
    return result


def _contribution(rule, base, applicable):
    if not rule or not rule.get('enabled') or not applicable:
        return Decimal('0'), Decimal('0')
    wage = min(base, Decimal(str(rule['wage_ceiling']))) if rule.get('wage_ceiling') else base
    employee_rate = Decimal(str(rule.get('employee_rate', 0))) / Decimal('100')
    employer_rate = Decimal(str(rule.get('employer_rate', 0))) / Decimal('100')
    return _money(wage * employee_rate), _money(wage * employer_rate)


def _fixed_rule(rule, applicable):
    if not rule or not rule.get('enabled') or not applicable:
        return Decimal('0')
    return _money(Decimal(str(rule.get('amount', 0))))


def _money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)
