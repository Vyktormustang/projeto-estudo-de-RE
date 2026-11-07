#!/usr/bin/env python3
"""Optional native screenshots; fresh synthetic game, exact v30, no warps.
Requires MOTOR_V30_ROM, MGBA_CORE and Pillow. Output directory must be new.
"""
import argparse,ctypes as C,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from PIL import Image
from mgba_treino_harness import VIDEO_CB
from test_motor_v30_guide_mgba import MotorV30GuideTests
from scripts import motor_v30 as p

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--saida',type=Path,required=True);args=a.parse_args()
    args.saida.mkdir(parents=True,exist_ok=False)
    T=MotorV30GuideTests;T.setUpClass();case=T();frames=[]
    @VIDEO_CB
    def video(data,w,h,pitch):
        if data:frames[:]=[(C.string_at(data,pitch*h),w,h,pitch)]
    case.f.video=video;case.f.core.core.retro_set_video_refresh(video)
    def shot(name):
        raw,w,h,pitch=frames[0];fmt=case.f.core.fmt_code;bpp=4 if fmt==1 else 2
        raw=b''.join(raw[y*pitch:y*pitch+w*bpp] for y in range(h))
        if fmt==1:img=Image.frombytes('RGB',(w,h),raw,'raw','BGRX')
        else:
            if fmt!=2:raise ValueError('Unsupported pixel format')
            rgb=bytearray()
            for i in range(0,len(raw),2):
                v=raw[i]|raw[i+1]<<8;rgb.extend((((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31))
            img=Image.frombytes('RGB',(w,h),bytes(rgb))
        img.save(args.saida/name);print(name,flush=True)
    try:
        case.open_top(1320);case.f.run(4);shot('GUIA_GRUPOS.png')
        case.select(6);case.f.run(4);shot('GUIA_ILHAS.png')
        for choice,name in ((0,'GUIA_KINDLE_ROAD.png'),(1,'GUIA_TREASURE_BEACH.png'),(3,'GUIA_BOND_BRIDGE.png')):
            case.select(choice);case.message_end(p.AREA_TEXTS[24+choice]);case.f.run(4);shot(name)
            case.f.pulse('B',40)
        case.f.pulse('B',40);case.select(7);case.f.run(4);shot('GUIA_HORARIOS_SAIR.png')
        case.select(0);case.f.run(150);shot('GUIA_REGRAS.png')
    finally:T.tearDownClass()
if __name__=='__main__':main()
