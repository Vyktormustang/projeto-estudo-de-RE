#!/usr/bin/env python3
"""Run the expanded 99-method v33 audit (including the 6 previous audit regressions) in isolated processes, without sharing cores.
Requires MOTOR_V33_ROM, MOTOR_V33_BASE, MGBA_CORE, TREINO_TEST_ROM.
Use --jobs 1 for serial execution. See docs/MOTOR_V33.md. Only synthetic fixtures.
"""
import argparse
import concurrent.futures
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
GROUPS=(
 'test_motor_v33_audit_mgba',
 'test_motor_v33',
 'test_motor_v33_hud_mgba',
 'test_motor_v33_preferences_mgba',
 'test_motor_v33_regressions.MotorV33BagTests',
 'test_motor_v33_regressions.MotorV33ClockTests',
 'test_motor_v33_encounters_mgba',
 'test_motor_v33_guide_mgba',
 'test_motor_v33_regressions.MotorV33ExperienceTests',
 'test_motor_v33_regressions.MotorV33PriorClockTests',
 'test_motor_v33_regressions.MotorV33SoundproofTests',
 'test_motor_v33_gameplay_mgba',
 'test_treino_ev_mgba',
)

def flatten(suite):
    for test in suite:
        if isinstance(test,unittest.TestSuite):yield from flatten(test)
        else:yield test

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--jobs',type=int,choices=range(1,5),default=3)
    a.add_argument('--log',type=Path,required=True)
    args=a.parse_args()
    for key in ('MOTOR_V33_ROM','MOTOR_V33_BASE','MGBA_CORE','TREINO_TEST_ROM'):
        if not os.environ.get(key):a.error(f'missing {key}')
    for path in (ROOT,ROOT/'tests'):sys.path.insert(0,str(path))
    expected=[t.id() for t in flatten(unittest.defaultTestLoader.loadTestsFromNames(GROUPS))]
    if len(expected)!=99 or len(set(expected))!=99:raise RuntimeError('Selection changed; expected 99 unique tests')
    env=dict(os.environ);env['PYTHONPATH']=str(ROOT)+os.pathsep+str(ROOT/'tests')
    def run(group):
        try:
            result=subprocess.run([sys.executable,'-u','-m','unittest','-v',group],
                cwd=ROOT.parent,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=1800)
            return result.returncode,result.stdout
        except subprocess.TimeoutExpired as error:
            output=error.stdout or b''
            return 1,(output.decode(errors='replace') if isinstance(output,bytes) else output)+'\nTIMEOUT\n'
    start=time.monotonic();results={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures={pool.submit(run,group):group for group in GROUPS}
        for future in concurrent.futures.as_completed(futures):
            group=futures[future];results[group]=future.result()
            print(f'{group}: exit {results[group][0]}',flush=True)
    elapsed=time.monotonic()-start
    log=f'v33 expanded audit: {args.jobs} isolated worker processes; synthetic fixtures only.\n\n'
    log+='\n'.join(f'=== {g} ===\n{results[g][1]}' for g in GROUPS)
    passed=re.findall(r'^test_\w+ \(([^)]+)\) \.\.\. ok$',log,re.M)
    ok=all(code==0 for code,_ in results.values()) and len(passed)==99 and set(passed)==set(expected)
    log+=f'\n=== Combined validation (wall time) ===\nRan 99 tests in {elapsed:.3f}s\n\n'+('OK\n' if ok else 'FAILED: inspect group results\n')
    args.log.parent.mkdir(parents=True,exist_ok=True);args.log.write_text(log)
    print(f'{len(passed)}/99 passed in {elapsed:.3f}s; {args.log}',flush=True)
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
