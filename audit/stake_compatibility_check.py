"""Read-only comparison with the current public SDK payout-lattice assertion.

Official source inspected on 2026-10-18:
https://github.com/engineio/math-sdk/blob/main/utils/rgs_verification.py
verify_lookup_format: positive payouts >=10; all payouts % 10 == 0.
This is not an execution of the remote platform or a publication test.
"""
import json
from pathlib import Path
import sys
import numpy as np

sys.dont_write_bytecode = True
target = Path(r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
sys.path.insert(0, str(target))
from polska_gurom import config as c

with np.load(target/"verification"/"joint_counts.npz",allow_pickle=False) as archive:
    base = archive["base"]
line, sc = np.nonzero(base)
payouts = line + np.array([c.SCATTER_PAYTABLE_UNITS.get(min(int(k),5),0) for k in sc])
invalid = (payouts % 10) != 0
# Untriggered rounds have no extra bonus and give direct reachable counterexamples.
untriggered_invalid = invalid & (sc < 3)
examples = sorted(set(map(int,payouts[untriggered_invalid])))[:12]
report = {
    "sdk_source": "https://github.com/engineio/math-sdk/blob/main/utils/rgs_verification.py",
    "reference_date": "2026-10-18",
    "method": "Local exhaustive support compared with public SDK verify_lookup_format assertion; no remote RGS test.",
    "payout_scale": c.PAYOUT_SCALE,
    "sdk_integer_payout_step": 10,
    "local_untriggered_payout_examples_failing_step_in_multiplier_units": examples,
    "local_untriggered_payout_examples_failing_step_in_total_bet_multiples": [v/c.PAYOUT_SCALE for v in examples],
    "unconditional_probability_of_untriggered_round_failing_step": int(base[line[untriggered_invalid],sc[untriggered_invalid]].sum())/(36**5),
    "publication_files_found": {
        "index_json": any(target.rglob("index.json")),
        "books_jsonl_zst": any(target.rglob("*.jsonl.zst")),
        "lookup_csv": any(target.rglob("lookUpTable*.csv")),
    },
    "status": "Local model passes its own tests; current payout lattice is incompatible with this SDK check and publication integration is absent.",
}
Path(__file__).with_name("stake_compatibility_check.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
