from pathlib import Path
import subprocess
import sys
import shutil

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'audit/stake_cascades_v04/dependencies'))
import zstandard
node=shutil.which('node')
with (OUT/'frontend_bank_validation.log').open('wb') as log:
    process=subprocess.Popen([str(node),str(OUT/'validate_bank_frontend.cjs')],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
    try:
        with (ROOT/'test-interface-any-start/stake_math/books_base.jsonl.zst').open('rb') as source:
            with zstandard.ZstdDecompressor().stream_reader(source) as reader:
                while chunk:=reader.read(1024*1024):process.stdin.write(chunk)
    finally:
        process.stdin.close()
    code=process.wait()
print((OUT/'frontend_bank_validation.log').read_text(encoding='utf-8'))
raise SystemExit(code)
