#!/usr/bin/env python3
"""Run the explicitly selected v42 suite; refuses skipped tests and existing output.

Requires a locally owned exact v41/v42 and mGBA 0.10.5 libretro (see MOTOR_V40.md).
Only synthetic saves, deleted by fixtures; retained results have no ROM/save bytes.
"""
import argparse,hashlib,json,os,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from scripts import motor_v42 as p

class Tee:
    def __init__(self,file):self.file=file
    def write(self,s):self.file.write(s);sys.stderr.write(s)
    def flush(self):self.file.flush();sys.stderr.flush()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('rom','base','core','saida'):parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args()
    if p.digest(a.rom.read_bytes())!=p.OUTPUT_SHA256 or p.digest(a.base.read_bytes())!=p.BASE_SHA256:parser.error('Wrong ROM hashes')
    core_hash=p.digest(a.core.read_bytes());a.saida.mkdir(parents=True,exist_ok=False)
    for key,path in {'MOTOR_V42_ROM':a.rom,'MOTOR_V42_BASE':a.base,'MGBA_CORE':a.core,'MOTOR_V42_OBSERVATIONS':a.saida/'observacoes.json','MOTOR_V41_SCREENS':a.saida/'telas'}.items():os.environ[key]=str(path.resolve())
    names=('test_motor_v42.TicketScriptTests','test_motor_v42.MotorV42BuildTests','test_motor_v42_mgba.MotorV42NativeTests')
    suite=unittest.defaultTestLoader.loadTestsFromNames(names);expected=suite.countTestCases();start=time.monotonic()
    with (a.saida/'testes.log').open('x') as log:result=unittest.TextTestRunner(stream=Tee(log),verbosity=2).run(suite)
    good=result.wasSuccessful() and not result.skipped and result.testsRun==expected
    summary=dict(passed=good,tests=result.testsRun,expected=expected,seconds=round(time.monotonic()-start,3),failures=[(str(t),msg) for t,msg in result.failures],errors=[(str(t),msg) for t,msg in result.errors],skips=[(str(t),msg) for t,msg in result.skipped],base_sha256=p.BASE_SHA256,rom_sha256=p.OUTPUT_SHA256,core_sha256=core_hash,classes=names,synthetic_only=True)
    (a.saida/'resultados.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0 if good else 1
if __name__=='__main__':raise SystemExit(main())
