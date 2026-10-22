"""Research-only comparison of fixed paylines; original source is read-only."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
from polska_gurom import config as c
from polska_gurom.theory import expected_line_payout, theoretical_metrics
from itertools import product
from fractions import Fraction
from collections import Counter
from pathlib import Path
import json
import math

strip = c.REEL_STRIPS[0]
windows = [tuple(strip[(s+r)%36] for r in range(3)) for s in range(36)]
all_stops = tuple(product(range(36), repeat=3))
prefix_bits = {}
scatter_bits = [0] * 4
for i, stops in enumerate(all_stops):
    sc = sum(c.SCATTER in windows[s] for s in stops)
    scatter_bits[sc] |= 1 << i
for rows in product(range(3), repeat=3):
    bits = 0
    for i, stops in enumerate(all_stops):
        syms = {windows[stops[r]][rows[r]] for r in range(3)} - {c.WILD}
        if not syms or (len(syms)==1 and next(iter(syms)) in c.REGULAR_SYMBOLS):
            bits |= 1 << i
    prefix_bits[rows] = bits

def assess(lines):
    prefixes = set(line[:3] for line in lines)
    bits = 0
    for prefix in prefixes:
        bits |= prefix_bits[prefix]
    line_prob = Fraction(bits.bit_count(), 36**3)
    extra = Fraction(0)
    nohit = {}
    for sc in range(4):
        count = (scatter_bits[sc] & ~bits).bit_count()
        nohit[sc] = count
        if sc >= 1:
            extra += Fraction(count,36**3)*sum(Fraction(math.comb(2,k)*11**(2-k),144) for k in range(max(0,3-sc),3))
    return {'n_lines':len(lines), 'unique_prefixes':len(prefixes), 'line_hit_probability':float(line_prob), 'scatter_only_hit_probability':float(extra), 'hit_probability':float(line_prob+extra), 'hit_probability_fraction':str(line_prob+extra), 'prefix_multiplicity':{''.join(map(str,k)):v for k,v in sorted(Counter(line[:3] for line in lines).items())}, 'lines':[list(x) for x in lines], 'no_line_hit_scatter_distribution':nohit}

def turns(line):
    ds = [b-a for a,b in zip(line,line[1:]) if b!=a]
    return sum(a!=b for a,b in zip(ds,ds[1:]))

def adjacent(line):
    return all(abs(a-b)<=1 for a,b in zip(line,line[1:]))

def reflect(line):
    return tuple(2-x for x in line)

if __name__ == '__main__':
    all_lines = list(product(range(3),repeat=5))
    smooth = [x for x in all_lines if adjacent(x) and turns(x)<=1]
    original = tuple(c.PAYLINES)
    horizontals = ((1,1,1,1,1),(0,0,0,0,0),(2,2,2,2,2))
    print('pool',len(smooth), 'prefixes',len(set(x[:3] for x in smooth)))
    print('horiz',assess(horizontals)['hit_probability'])
    print('original',assess(original)['hit_probability'])
    print('all smooth prefixes',assess(smooth)['hit_probability'])
    # Visible research variants, not a recommendation to freeze mathematics.
    variants={'three_horizontal':assess(horizontals),'current_twenty':assess(original)}
    # Each prefix has two gently continued suffixes; horizontal lines included.
    prefix_set = [(0,0,0),(2,2,2),(1,1,1),(0,0,1),(2,2,1),(0,1,1),(2,1,1),(1,1,0),(1,1,2),(1,0,0)]
    chosen=[]
    for p in prefix_set:
        options=[x for x in smooth if x[:3]==p]
        options.sort(key=lambda x:(0 if len(set(x))==1 else 1, sum(abs(a-b) for a,b in zip(x,x[1:])), turns(x), x))
        chosen.extend(options[:2])
    variants['ten_prefixes_two_continuations']=assess(chosen)
    # Nine shared beginnings; 19 vertically symmetric lines plus one gradual ramp.
    representatives=[(0,0,0,0,0),(0,0,0,1,1),
                     (0,0,1,1,2),(0,0,1,2,2),
                     (0,1,1,1,0),(0,1,1,2,2),
                     (1,1,0,0,1),(1,1,0,1,2)]
    nine=[(1,1,1,1,1),(1,1,1,0,0),(1,1,1,2,2)]
    for line in representatives:
        nine.extend((line,reflect(line)))
    nine.append((0,0,0,1,2))
    assert len(nine)==20 and len(set(nine))==20
    assert all(adjacent(x) and turns(x)<=1 for x in nine)
    assert all(x in nine for x in horizontals)
    variants['nine_prefixes_smooth_twenty']=assess(nine)
    iconic=[line for line in nine if line[:3] not in ((0,0,1),(2,2,1))]
    iconic.extend(((0,1,2,1,0),(2,1,0,1,2),(0,1,2,2,1),(2,1,0,0,1)))
    assert len(iconic)==20 and len(set(iconic))==20
    assert all(adjacent(x) and turns(x)<=1 for x in iconic)
    assert all(x in iconic for x in horizontals)
    variants['nine_prefixes_with_v_twenty']=assess(iconic)
    # Expected winning-line count and EV are independent of row choice.
    q=Fraction(2105,36**3)
    current_theory=theoretical_metrics()
    for data in variants.values():
        data['one_line_hit_probability']=float(q)
        data['expected_number_winning_lines']=float(data['n_lines']*q)
        data['mean_winning_lines_when_line_hit']=data['expected_number_winning_lines']/data['line_hit_probability']
        data['base_line_ev_pre_cap']=data['n_lines']*expected_line_payout()
        data['base_total_ev_pre_cap']=data['base_line_ev_pre_cap']+current_theory['scatter_rtp']
        data['mean_payout_given_base_hit_pre_cap']=data['base_total_ev_pre_cap']/data['hit_probability']
        if data['n_lines']==20:
            data['full_round_ev_pre_cap']=current_theory['total_rtp']
    out=Path(__file__).with_name('comparison_results.json')
    out.write_text(json.dumps(variants,indent=2),encoding='utf-8')
    for name, data in variants.items():
        print(name, data['n_lines'],data['unique_prefixes'],data['hit_probability'])
        print(data['lines'])
