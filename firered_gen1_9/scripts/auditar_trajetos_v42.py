#!/usr/bin/env python3
"""Read-only actual-ROM topology for continuous v42 island travel tests.

Collision grids are used in memory only, never exported as commercial assets.
Graph/path existence is structural evidence, not proof of native travel.
"""
import argparse,json,struct,sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts import motor_v42 as release,auditar_obtencao_v40 as native

@dataclass(frozen=True)
class Warp:
    index:int;x:int;y:int;elevation:int;destination_id:int;destination:tuple;behavior:int
    @property
    def xy(self):return self.x,self.y

@dataclass
class Map:
    key:tuple;name:str;width:int;height:int;header:int;cells:tuple;warps:tuple
    def walkable(self,xy):
        x,y=xy
        return 0<=x<self.width and 0<=y<self.height and not self.cells[y*self.width+x]&0xC00 and self.cells[y*self.width+x]>>12==3

def read_map(b,g,m,name):
    hd,ev,(w,h)=native.map_data(b,g,m);layout=native.pointer(b,hd)
    native.require(0<w<=256 and 0<h<=256,'Unexpected layout size')
    cells=struct.unpack_from('<'+'H'*(w*h),b,native.pointer(b,layout+12,2*w*h));warps=[]
    if b[ev+1]:
        at=native.pointer(b,ev+8,b[ev+1]*8)
        for i in range(b[ev+1]):
            x,y,elevation,wi,dm,dg=struct.unpack_from('<hhBBBB',b,at+i*8)
            native.require(0<=x<w and 0<=y<h,'Warp outside layout')
            tile=cells[y*w+x]&1023;tileset=native.pointer(b,layout+(16 if tile<640 else 20))
            attributes=native.pointer(b,tileset+20);index=tile if tile<640 else tile-640
            behavior=native.u32(b,attributes+index*4)&0x1FF
            warps.append(Warp(i,x,y,elevation,wi,(dg,dm),behavior))
    return Map((g,m),name,w,h,hd,cells,tuple(warps))

def world(b,strict=True):
    if strict:native.require(release.digest(b)==release.OUTPUT_SHA256,'Not exact v42')
    maps={}
    for m in native.fixed.load_map_catalog():
        if m.label.startswith(('NavelRock_','BirthIsland_')):maps[m.group,m.number]=read_map(b,m.group,m.number,m.label)
    native.require(len(maps)==24,'Unexpected island map count')
    for m in maps.values():
        for warp in m.warps:
            native.require(warp.destination in maps,'Warp leaves island graph')
            other=maps[warp.destination].warps[warp.destination_id]
            native.require(other.destination==m.key and other.destination_id==warp.index,'Nonreciprocal warp')
            native.require(warp.elevation==3 and m.walkable(warp.xy),'Unexpected warp elevation/collision')
    return maps

def map_route(maps,start,goal):
    queue=deque([start]);previous={start:None}
    while queue:
        key=queue.popleft()
        if key==goal:
            path=[]
            while previous[key] is not None:
                parent,warp=previous[key];path.append((parent,warp));key=parent
            return list(reversed(path))
        for warp in maps[key].warps:
            if warp.destination not in previous:previous[warp.destination]=(key,warp);queue.append(warp.destination)
    raise ValueError(f'No map route {start}->{goal}')

DIRECTIONS=(('UP',0,-1),('LEFT',-1,0),('RIGHT',1,0),('DOWN',0,1))
def cell_route(m,start,goal,blocked=()):
    blocked=set(blocked)|{w.xy for w in m.warps if w.xy!=goal}
    queue=deque([start]);previous={start:None}
    while queue:
        xy=queue.popleft()
        if xy==goal:
            path=[]
            while previous[xy] is not None:
                parent,button=previous[xy];path.append((button,xy));xy=parent
            return list(reversed(path))
        for button,dx,dy in DIRECTIONS:
            nxt=xy[0]+dx,xy[1]+dy
            if nxt not in previous and nxt not in blocked and m.walkable(nxt):previous[nxt]=(xy,button);queue.append(nxt)
    raise ValueError(f'No walk route in {m.name}: {start}->{goal}')

def audit(b):
    maps=world(b)
    return dict(version='v42',rom_sha256=release.OUTPUT_SHA256,read_only=True,native_travel_certified_by_this_parser=False,
        maps=[dict(group=m.key[0],number=m.key[1],name=m.name,width=m.width,height=m.height,header=hex(m.header),
            warps=[dict(index=w.index,x=w.x,y=w.y,elevation=w.elevation,behavior=hex(w.behavior),destination=list(w.destination),destination_id=w.destination_id) for w in m.warps]) for m in maps.values()],
        journeys=[dict(start=list(s),goal=list(g),transitions=len(map_route(maps,s,g))) for s,g in (((2,59),(2,37)),((2,37),(2,38)),((2,38),(2,59)),((2,58),(2,56)),((2,56),(2,58)))])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
    b=a.rom.read_bytes();report=audit(b);a.saida.parent.mkdir(parents=True,exist_ok=True)
    with a.saida.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    native.require(a.rom.read_bytes()==b,'ROM changed');print('24 actual-ROM island maps; reciprocal graph only, no gameplay claim.')
if __name__=='__main__':main()
