def settle_cap(raw_base_units, raw_bonus_units, cap_units):
    if min(raw_base_units, raw_bonus_units, cap_units) < 0:
        raise ValueError("Amounts must be nonnegative")
    raw_total = raw_base_units + raw_bonus_units
    paid_base = min(raw_base_units, cap_units)
    paid_total = min(raw_total, cap_units)
    return dict(paid_base_units=paid_base, paid_bonus_units=paid_total-paid_base,
                paid_total_units=paid_total, cap_reduction_units=raw_total-paid_total,
                cap_reached=raw_total >= cap_units)
