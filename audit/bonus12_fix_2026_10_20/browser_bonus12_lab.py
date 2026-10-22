"""Isolated browser rendering QA. Not the player's normal random game server."""
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'test-interface'))
import server

manifest,cdf,payouts=server.selection.load_distribution()
book_id=manifest['bonus_coverage']['12']['book_ids'][0]
ticket=0 if book_id==0 else cdf[book_id-1]

class WitnessTicket(random.Random):
    def randrange(self, stop, *args):
        if args or stop != manifest['total_weight']:raise ValueError('Unexpected RNG draw')
        return ticket

class Lab(server.InterfaceServer):
    def session_for(self, token, *, require_existing=False):
        session,new_token=super().session_for(token,require_existing=require_existing)
        if new_token is not None:session.rng=WitnessTicket()
        return session,new_token

print('ISOLATED12FS QA: fixed ticket selects actual exported book; not random-frequency evidence',flush=True)
print(f'book{book_id}, version{manifest["math_version"]}, payout{payouts[book_id]}units',flush=True)
Lab(('127.0.0.1',8778)).serve_forever()
