"""Failures around the local wallet commit must never leave an extra charge."""
from pathlib import Path
from collections import OrderedDict
from dataclasses import asdict
import json
import sys
import threading
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
from test_server import Client

class AtomicSettlementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=server.InterfaceServer(("127.0.0.1",0))
        cls.thread=threading.Thread(target=lambda:cls.server.serve_forever(poll_interval=.02),daemon=True)
        cls.thread.start()
        manifest,_,_=server.selection.load_distribution()
        cls.loss=server.selection.replay_spec(manifest["books"][1])
        assert cls.loss.payout_units==0

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3)

    def setUp(self):
        self.client=Client(self.server.server_port)
        self.before=self.client.state()
        self.session=next(s for s in self.server.sessions.values() if s.session_id==self.before["session_id"])
        self.selection=patch.object(server.selection,"select_round",return_value=(1,self.loss))
        self.selection.start();self.addCleanup(self.selection.stop)

    def assert_uncharged(self):
        self.assertEqual(self.client.state(),self.before)
        self.assertFalse(self.session.processed_ids)

    def retry_once(self,request_id):
        status,result,_=self.client.spin(bet=100,request_id=request_id)
        self.assertEqual(status,200)
        self.assertEqual(self.client.state()["balance_cents"],self.before["balance_cents"]-100)
        self.assertEqual(self.client.state()["rounds"],1)
        self.assertEqual(self.client.spin(bet=100,request_id=request_id)[1],result)

    def test_asdict_failure_leaves_wallet_and_idempotency_unchanged(self):
        with patch.object(server,"asdict",side_effect=MemoryError("injected before commit")):
            self.assertEqual(self.client.spin(bet=100,request_id="asdict-fail")[0],500)
        self.assert_uncharged();self.retry_once("asdict-fail")

    def test_json_encoding_failure_occurs_before_commit(self):
        encode=json.dumps
        def fail_result(payload,*args,**kwargs):
            if isinstance(payload,dict) and payload.get("request_id")=="encode-fail" and "round" in payload:
                raise MemoryError("injected JSON failure")
            return encode(payload,*args,**kwargs)
        with patch.object(server.json,"dumps",side_effect=fail_result):
            self.assertEqual(self.client.spin(bet=100,request_id="encode-fail")[0],500)
        self.assert_uncharged();self.retry_once("encode-fail")

    def test_processed_id_failure_rolls_back_both_cache_and_wallet(self):
        class FailOnce(set):
            failed=False
            def add(self,value):
                super().add(value)
                if not self.failed:self.failed=True;raise MemoryError("injected set failure")
        self.session.processed_ids=FailOnce()
        self.assertEqual(self.client.spin(bet=100,request_id="set-fail")[0],500)
        self.assert_uncharged();self.retry_once("set-fail")

    def test_cache_insert_failure_rolls_back_partial_entry(self):
        class FailOnce(OrderedDict):
            failed=False
            def __setitem__(self,key,value):
                super().__setitem__(key,value)
                if not self.failed:self.failed=True;raise MemoryError("injected cache failure")
        self.session.results=FailOnce()
        self.assertEqual(self.client.spin(bet=100,request_id="cache-fail")[0],500)
        self.assert_uncharged();self.retry_once("cache-fail")

    def test_output_failure_after_commit_keeps_exact_result_for_retry(self):
        write=server.InterfaceHandler._json_bytes
        failed=[]
        def fail_once(handler,data,status=200,cookie=None):
            if handler.path=="/api/spin" and status==200 and not failed:
                failed.append(True);raise OSError("injected output failure")
            return write(handler,data,status=status,cookie=cookie)
        with patch.object(server.InterfaceHandler,"_json_bytes",new=fail_once):
            self.assertEqual(self.client.spin(bet=100,request_id="output-fail")[0],500)
        self.assertEqual(self.client.state()["rounds"],1)
        self.retry_once("output-fail")

    def test_wallet_endpoint_is_current_after_historical_result_retry(self):
        _,first,_=self.client.spin(bet=100,request_id="first")
        self.client.spin(bet=500,request_id="second")
        self.assertEqual(self.client.spin(bet=100,request_id="first")[1],first)
        status,wallet,_=self.client.request("GET","/api/wallet")
        self.assertEqual(status,200);self.assertEqual(wallet["rounds"],2)
        self.assertEqual(wallet["balance_cents"],self.before["balance_cents"]-600)
        self.assertNotIn("recent_rounds",wallet)

if __name__=="__main__":
    unittest.main(verbosity=2)
