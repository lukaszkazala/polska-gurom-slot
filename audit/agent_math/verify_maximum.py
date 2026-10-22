import sys,json,os
sys.dont_write_bytecode=True
sys.path.insert(0,r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
from polska_gurom.config import REEL_STRIPS
from polska_gurom.game import window_for_stop,evaluate_paid_spin,evaluate_free_spin,play_round

class FixedRNG:
    def __init__(self):
        self.stops=iter([33,26,20,14,6]+[21,15,20,3,30]*12)
    def randrange(self,n):return next(self.stops)
    def random(self):return 0
    def choice(self,seq):return 2

def grid(stops):
    cols=[window_for_stop(r,s) for r,s in zip(REEL_STRIPS,stops)]
    return [[col[row] for col in cols] for row in range(3)]

bg=grid([33,26,20,14,6]);fg=grid([21,15,20,3,30])
b=evaluate_paid_spin(bg);f=evaluate_free_spin(fg,FixedRNG());round_=play_round(FixedRNG())
out={'base_grid':bg,'base':b.__dict__,'free_grid':fg,'free':f.__dict__,
                  'round_total':round_[0].payout+round_[1],'round_bonus':round_[1],
                  'round_expansions':round_[2]}
print(json.dumps(out,indent=2))
with open(os.path.join(os.path.dirname(__file__),'maximum_witness_results.json'),'w') as file:
    json.dump(out,file,indent=2)
assert abs(round_[0].payout+round_[1]-3037.3)<1e-9
