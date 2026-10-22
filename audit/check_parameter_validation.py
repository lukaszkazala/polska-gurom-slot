"""Reproduce divergence for invalid probability without editing the engine."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
from polska_gurom.sim import simulate
from polska_gurom.theory import theoretical_metrics

result = {
    "valid_probability": 1.0,
    "invalid_probability": 1.5,
    "theory_rtp_at_1": theoretical_metrics(1.0)["total_rtp"],
    "theory_rtp_at_1_5": theoretical_metrics(1.5)["total_rtp"],
    "same_engine_output_at_1_and_1_5": (
        simulate(1000, expansion_probability=1.0)
        == simulate(1000, expansion_probability=1.5)
    ),
}
Path(__file__).with_name("parameter_validation_results.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
