from src.engines.loan_engine.amortization import generate_schedule
from src.engines.loan_engine.prepayment import apply_prepayment_at_month, PrepaymentMode

found = False
for rate in [500, 600, 700, 800, 900, 1000, 1200, 1500, 2000, 2500, 3000, 3600]:
    for P in [1000000, 10000000, 50000000, 100000000]:
        for tenure in [2, 3, 6, 12, 36, 120, 360]:
            s = generate_schedule(P, rate, tenure, '2000-01-01')
            orig_emi = s[0].emi_paise
            for pm in [tenure, tenure - 1]:
                ob = P if pm == 1 else s[pm - 2].balance_paise
                for prepay in [10000, max(10000, ob // 100)]:
                    if prepay > ob:
                        continue
                    ns, res = apply_prepayment_at_month(s, pm, prepay, rate, mode=PrepaymentMode.REDUCE_EMI)
                    if res.new_emi_paise > orig_emi + 10:
                        print(f'EMI UP: rate={rate} P={P} tenure={tenure} pm={pm} prepay={prepay} orig_emi={orig_emi} new_emi={res.new_emi_paise} rem={res.original_remaining_months}')
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if found:
            break
    if found:
        break
print('done', found)
