typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define GET ((u32(*)(const void*,u32,void*))0x0810a96du)
#define COMP ((const u8*)0x08e06000u)
#define TMMS ((const u16*)0x08e18000u)
#define NAMES ((const u8*)0x08235930u)
extern u8 orig_can(void*,u16,u8);
extern void orig_label(u8*,u16);
u8 tm_can(void* mon, u16 item, u8 tutor) {
 if (item<375 || item>603) return orig_can(mon,item,tutor);
 u16 number = item - 375;
 u16 move = TMMS[item - 289];
 if (GET(mon,45,0)) return 3;
 u16 species=GET(mon,65,0);
 if(!move || species==0 || species>1025) return 1;
 if(!(COMP[species*29 + (number>>3)] & (1u<<(number&7))))return 1;
 for(int i=0;i<4;i++) if(GET(mon,13+i,0)==move)return 2;
 return 0;
}
void tm_label(u8*dst,u16 item) {
 if(item<375 || item>603) { orig_label(dst,item);return; }
 u32 n=item-374, h=0,t=0;
 while(n>=100){n-=100;h++;} while(n>=10){n-=10;t++;}
 dst[0]=0xc8;dst[1]=0xa1+h;dst[2]=0xa1+t;dst[3]=0xa1+n;dst[4]=0;
 u16 m=TMMS[item-289];const u8*name=NAMES+17*m;int i=0;
 while(i<17 && name[i]!=0xff){dst[5+i]=name[i];i++;}dst[5+i]=0xff;
}
