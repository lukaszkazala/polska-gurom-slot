from pathlib import Path
import json,sys,threading,time,random,http.client,unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

OUT=Path(__file__).resolve().parent
APP=OUT/'isolated_app'
sys.path.insert(0,str(APP))
import server as app
from test_server import Client

OBSERVATIONS=[]
class AuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.http=app.InterfaceServer(('127.0.0.1',0))
  cls.worker=threading.Thread(target=lambda:cls.http.serve_forever(poll_interval=.01),daemon=True)
  cls.worker.start()
  cls.log_patch=patch.object(app.InterfaceHandler,'log_message',lambda *args:None)
  cls.log_patch.start()
  manifest,_,_=app.selection.load_distribution()
  cls.loss=next(app.selection.replay_spec(s) for s in manifest['books'] if app.selection.replay_spec(s).payout_units==0)
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.worker.join(3);cls.log_patch.stop()
 def setUp(self):
  self.client=Client(self.http.server_port)
  self.before=self.client.state()
  self.session=self.http.sessions[self.client.cookie.split('=',1)[1]]
 def child(self):
  c=Client(self.http.server_port,self.client.cookie);c.session_id=self.client.session_id;return c
 def test_01_distinct_concurrent_ids_and_bets_exact_ledger(self):
  bets=list(app.BET_OPTIONS_CENTS)*4
  def job(i):return self.child().spin(bet=bets[i],request_id=f'concurrent-{i}')
  with ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(job,range(len(bets))))
  self.assertTrue(all(row[0]==200 for row in rows))
  replies=[r[1] for r in rows];state=self.client.state()
  self.assertEqual(len({r['round_id'] for r in replies}),len(bets))
  self.assertEqual(state['rounds'],len(bets));self.assertEqual(state['total_bet_cents'],sum(bets))
  self.assertEqual(state['total_win_cents'],sum(r['win_cents'] for r in replies))
  self.assertEqual(state['balance_cents'],self.before['balance_cents']-sum(bets)+sum(r['win_cents'] for r in replies))
  ordered=sorted(replies,key=lambda r:r['stats']['rounds'])
  previous=self.before['balance_cents']
  for r in ordered:
   self.assertEqual(r['balance_before_cents'],previous)
   self.assertEqual(r['balance_cents'],previous-r['bet_cents']+r['win_cents'])
   previous=r['balance_cents']
  OBSERVATIONS.append({'case':'28 concurrent distinct IDs, 7 stakes','accepted':len(replies),'exact_wallet':state['balance_cents']})
 def test_02_concurrent_conflicting_stakes_one_id(self):
  def job(i):return self.child().spin(bet=100 if i%2 else 200,request_id='one-conflict')
  with ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(job,range(16)))
  success=[r[1] for r in rows if r[0]==200];fail=[r for r in rows if r[0]!=200]
  self.assertEqual(len(success),8);self.assertEqual(len(fail),8)
  self.assertTrue(all(r[0]==409 and r[1]['code']=='request_conflict' for r in fail))
  self.assertTrue(all(r==success[0] for r in success));self.assertEqual(self.client.state()['rounds'],1)
 def test_03_overdraft_prevented_with_parallel_losses(self):
  with self.session.lock:self.session.balance_cents=700
  def job(i):return self.child().spin(bet=100,request_id=f'limited-{i}')
  with patch.object(app.selection,'select_round',return_value=(0,self.loss)):
   with ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(job,range(16)))
  self.assertEqual(sum(r[0]==200 for r in rows),7)
  self.assertTrue(all(r[0]==200 or r[1]['code']=='insufficient_funds' for r in rows))
  state=self.client.state();self.assertEqual(state['balance_cents'],0);self.assertEqual(state['rounds'],7)
 def test_04_all_stakes_scale_identical_book_exactly(self):
  result=app.scenario_round('cascade')
  with patch.object(app.selection,'select_round',return_value=(0,result)):
   for bet in app.BET_OPTIONS_CENTS:
    status,data,_=self.client.spin(bet=bet,request_id=f'scale-{bet}')
    self.assertEqual(status,200);self.assertEqual(data['win_cents'],bet*result.payout_units//100)
    self.assertEqual(bet*result.payout_units%100,0)
  state=self.client.state();self.assertEqual(state['rounds'],7)
 def test_05_scenarios_all_modes_all_stakes_no_debit(self):
  for mode in app.SCENARIO_SEEDS:
   for bet in app.BET_OPTIONS_CENTS:
    status,data,_=self.client.spin(mode,bet,f'scenario-{mode}-{bet}')
    self.assertEqual(status,200);self.assertTrue(data['is_scenario'])
    self.assertEqual(data['balance_cents'],self.before['balance_cents']);self.assertEqual(data['stats']['rounds'],0)
  self.assertEqual(self.client.state()['total_bet_cents'],0)
 def test_06_injection_and_malformed_semantics_rejected_without_mutation(self):
  valid={'bet_cents':100,'mode':'random','request_id':'validation'}
  invalid=[{**valid,k:v} for k,v in [('grid',[['WILD']*5]*3),('seed',1),('scatter_count',5),('win_cents',999999),('balance_cents',999999),('payout_units',500000),('book_id',100020)]]
  invalid += [{**valid,'request_id':x} for x in [0,True,[],{},None,'a b','\n','ą','a'*129]]
  invalid += [{**valid,'mode':x} for x in [0,True,[],{},None,'RANDOM','bonus12']]
  invalid += [{**valid,'bet_cents':x} for x in [False,{},[],1e100,-1,0,10**100]]
  for body in invalid:
   self.assertEqual(self.client.request('POST','/api/spin',body,headers={'X-Game-Session':self.client.session_id})[0],400)
  self.assertEqual(self.client.state(),self.before)
  OBSERVATIONS.append({'case':'malformed semantic inputs and outcome injection','rejected':len(invalid)})
 def test_07_selector_failure_before_settlement_is_retry_safe(self):
  with patch.object(app.selection,'select_round',side_effect=RuntimeError('injected before commit')):
   status,data,_=self.client.spin(request_id='selector-fault')
  self.assertEqual(status,500);self.assertEqual(self.client.state(),self.before)
  self.assertEqual(self.client.spin(request_id='selector-fault')[0],200);self.assertEqual(self.client.state()['rounds'],1)
 def test_08_json_output_failure_after_cache_is_retry_safe(self):
  real=app.InterfaceHandler._json
  def fail_round(handler,payload,*args,**kwargs):
   if 'round_id' in payload:raise OSError('injected serialization/output fault')
   return real(handler,payload,*args,**kwargs)
  with patch.object(app.InterfaceHandler,'_json',fail_round):
   status,body,_=self.client.spin(request_id='output-fault')
  self.assertEqual(status,500);self.assertEqual(self.client.state()['rounds'],1)
  self.assertEqual(self.client.spin(request_id='output-fault')[0],200);self.assertEqual(self.client.state()['rounds'],1)
 def test_09_record_serialization_failure_exposes_non_atomic_settlement(self):
  # Production handler; deterministic fault at dataclass-to-response conversion.
  with patch.object(app.selection,'select_round',return_value=(0,self.loss)):
   with patch.object(app,'asdict',side_effect=MemoryError('audit injected conversion failure')):
    status,error,_=self.client.spin(bet=100,request_id='commit-gap')
   after_error=self.client.state()
   retry_status,retry,_=self.client.spin(bet=100,request_id='commit-gap')
  after_retry=self.client.state()
  self.assertEqual(status,500);self.assertEqual(after_error['rounds'],1)
  self.assertEqual(len(after_error['recent_rounds']),0);self.assertEqual(retry_status,200)
  self.assertEqual(after_retry['rounds'],2);self.assertEqual(after_retry['balance_cents'],self.before['balance_cents']-200)
  OBSERVATIONS.append({'case':'non_atomic_settlement_fault_injection','confirmed_bug':True,'injection':'asdict raises MemoryError once after wallet mutation','initial_balance':self.before['balance_cents'],'first_status':status,'after_error':after_error,'retry_status':retry_status,'after_retry_rounds':after_retry['rounds'],'after_retry_balance':after_retry['balance_cents'],'request_id':'commit-gap','same_request_charged_twice':True})
 def test_10_old_retry_contains_historical_wallet_snapshot(self):
  with patch.object(app.selection,'select_round',return_value=(0,self.loss)):
   _,first,_=self.client.spin(bet=100,request_id='old')
   self.child().spin(bet=500,request_id='new')
   _,retry,_=self.client.spin(bet=100,request_id='old')
  state=self.client.state()
  self.assertEqual(first,retry);self.assertEqual(retry['stats']['rounds'],1);self.assertEqual(state['rounds'],2)
  OBSERVATIONS.append({'case':'historical_wallet_on_retry','note':'Idempotent outcome correct; UI needs reconcile current wallet if another tab advanced it','retry_balance':retry['balance_cents'],'current_balance':state['balance_cents'],'retry_rounds':retry['stats']['rounds'],'current_rounds':state['rounds']})
 def test_11_reset_and_inflight_spin_are_serialized_and_old_epoch_rejected(self):
  entered=threading.Event();release=threading.Event();old=self.child();reset=self.child()
  def delay(rng):entered.set();self.assertTrue(release.wait(3));return (0,self.loss)
  with ThreadPoolExecutor(max_workers=2) as pool:
   with patch.object(app.selection,'select_round',delay):
    pending=pool.submit(old.spin,'random',100,'reset-race')
    self.assertTrue(entered.wait(2));reset_future=pool.submit(reset.request,'POST','/api/reset',{})
    time.sleep(.03);release.set();spin_reply=pending.result(4);reset_reply=reset_future.result(4)
  self.assertEqual(spin_reply[0],200);self.assertEqual(reset_reply[0],200)
  self.assertEqual(reset_reply[1]['rounds'],0);self.assertEqual(reset_reply[1]['balance_cents'],app.INITIAL_BALANCE_CENTS)
  status,error,_=old.spin('random',100,'reset-race');self.assertEqual(status,409);self.assertEqual(error['code'],'session_changed')
 def test_12_exact_final_funds_permit_one_loss_then_block(self):
  with self.session.lock:self.session.balance_cents=100
  with patch.object(app.selection,'select_round',return_value=(0,self.loss)):
   self.assertEqual(self.client.spin(bet=100,request_id='last-coin')[0],200)
   status,error,_=self.client.spin(bet=100,request_id='insolvent')
  self.assertEqual(status,409);self.assertEqual(error['code'],'insufficient_funds');self.assertEqual(self.client.state()['rounds'],1)
 def test_13_cached_result_replay_allowed_when_wallet_now_insolvent(self):
  with self.session.lock:self.session.balance_cents=100
  with patch.object(app.selection,'select_round',return_value=(0,self.loss)):
   first=self.client.spin(bet=100,request_id='last-coin')
   retry=self.client.spin(bet=100,request_id='last-coin')
  self.assertEqual(first,retry);self.assertEqual(self.client.state()['rounds'],1)
 def test_14_conflicting_mode_id_cannot_convert_scenario_to_paid(self):
  self.client.spin('win',100,'same-id')
  status,error,_=self.client.spin('random',100,'same-id')
  self.assertEqual(status,409);self.assertEqual(error['code'],'request_conflict');self.assertEqual(self.client.state()['rounds'],0)

class Recording(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.records=[]
 def addSuccess(self,test):super().addSuccess(test);self.records.append({'test':test._testMethodName,'status':'pass'})
 def addFailure(self,test,err):super().addFailure(test,err);self.records.append({'test':test._testMethodName,'status':'fail','error':self._exc_info_to_string(err,test)})
 def addError(self,test,err):super().addError(test,err);self.records.append({'test':test._testMethodName,'status':'error','error':self._exc_info_to_string(err,test)})
if __name__=='__main__':
 with (OUT/'extended_server.log').open('w',encoding='utf-8') as log:
  result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Recording).run(unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests))
 report={'engine':str(Path(app.game.__file__).resolve()),'math_version':app.config.MATH_VERSION,'tests_run':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'tests':result.records,'observations':OBSERVATIONS,'note':'PASS means observation/assertion reproduced; test09 intentionally proves a fault-injection transaction bug, not acceptable behavior.'}
 (OUT/'extended_server_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'observations':len(OBSERVATIONS)}))
 raise SystemExit(not result.wasSuccessful())
