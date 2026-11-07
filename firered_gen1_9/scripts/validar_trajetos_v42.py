#!/usr/bin/env python3
"""Validate read-only topology and two continuous native v42 island round trips.

Outputs must be new. Only synthetic preparation; no supplied personal saves.
Requires Python + Pillow and mGBA 0.10.5 libretro (build in MOTOR_V40.md).
"""
import argparse,contextlib,json,os,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from scripts import motor_v42 as p,auditar_trajetos_v42 as audit

class Tee:
    def __init__(self,file):self.file=file;self.terminal=sys.stderr
    def write(self,s):self.file.write(s);self.terminal.write(s)
    def flush(self):self.file.flush();self.terminal.flush()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('rom','base','core','saida'):parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args();rom=a.rom.read_bytes();base=a.base.read_bytes()
    if p.digest(rom)!=p.OUTPUT_SHA256 or p.digest(base)!=p.BASE_SHA256:parser.error('Wrong ROM hashes')
    core_sha=p.digest(a.core.read_bytes());a.saida.mkdir(parents=True,exist_ok=False)
    (a.saida/'estrutura.json').write_text(json.dumps(audit.audit(rom),indent=2)+'\n')
    for key,path in {'TRAJETOS_V42_ROM':a.rom,'TRAJETOS_V42_BASE':a.base,'MGBA_CORE':a.core,'TRAJETOS_V42_OBSERVATIONS':a.saida/'observacoes.json','MOTOR_V41_SCREENS':a.saida/'telas'}.items():os.environ[key]=str(path.resolve())
    names=('test_trajetos_v42.PathAlgorithmTests','test_trajetos_v42.IslandTopologyTests','test_trajetos_v42_mgba.ContinuousIslandJourneys')
    suite=unittest.defaultTestLoader.loadTestsFromNames(names);expected=suite.countTestCases();start=time.monotonic()
    with (a.saida/'testes.log').open('x') as log:
        tee=Tee(log)
        with contextlib.redirect_stdout(tee):result=unittest.TextTestRunner(stream=tee,verbosity=2).run(suite)
    unchanged=a.rom.read_bytes()==rom and a.base.read_bytes()==base
    good=result.wasSuccessful() and not result.skipped and result.testsRun==expected==6 and unchanged
    summary=dict(passed=good,tests=result.testsRun,expected=expected,seconds=round(time.monotonic()-start,3),failures=[(str(t),msg) for t,msg in result.failures],errors=[(str(t),msg) for t,msg in result.errors],skips=[(str(t),msg) for t,msg in result.skipped],rom_sha256=p.OUTPUT_SHA256,base_sha256=p.BASE_SHA256,core_sha256=core_sha,roms_unchanged=unchanged,classes=names,synthetic_preparation=True,island_teleports=False)
    (a.saida/'resultados.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0 if good else 1
if __name__=='__main__':raise SystemExit(main())
