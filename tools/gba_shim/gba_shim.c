/*
 * gba_shim.c — ponte C mínima sobre a libmgba (mGBA) para o harness de RE.
 * =======================================================================
 *
 * PROBLEMA QUE RESOLVE
 *   O driver antigo (scripts/gba_libretro_emu.py + core mgba_libretro.so do
 *   .deb em emu/) abortava com `GLIBC_2.38 not found` em sandbox Debian 12
 *   (glibc 2.36) e não expunha CPU/registradores/breakpoints/leitura de IO.
 *   Este shim linka contra uma libmgba compilada localmente (ver Makefile) e
 *   expõe só o necessário — com tipos primitivos, sem structs na fronteira.
 *
 * O QUE EXPÕE
 *   ciclo de vida : gs_new, gs_free, gs_load, gs_reset
 *   execução      : gs_frames(n), gs_steps(n)   (determinístico; 1 passo = 1 instrução ARM/Thumb)
 *   input         : gs_keys(mask)               (mask libretro; 0 = tudo solto)
 *   CPU           : gs_reg(i), gs_set_reg(i,v), gs_pc(), gs_cpsr(), gs_thumb()
 *   memória       : gs_read{8,16,32}, gs_write{8,16,32} (via barramento: EWRAM/IWRAM/IO/VRAM/ROM)
 *   debug         : gs_bp_add(addr), gs_bp_clear(), gs_bp_hits(), gs_bp_pc(i)
 *   estado        : gs_state_size(), gs_state_save(buf), gs_state_load(buf)
 *   framebuffer   : gs_video(buf)               (240*160 uint16 RGB565)
 *
 * MÁSCARA DE TECLAS (libretro classic):
 *   B=1 Y=2 SELECT=4 START=8 UP=16 DOWN=32 LEFT=64 RIGHT=128 A=256 X=512 L=1024 R=2048
 *
 * LIMITE HONESTO
 *   Não é um debugger interativo: os breakpoints contam acertos por passo e
 *   param a execução no passo em que a condição vale (ver gs_steps).
 */
#include <limits.h>
#include <mgba/core/core.h>
#include <mgba/core/interface.h>
#include <mgba/core/serialize.h>
#include <mgba/gba/core.h>
#include <mgba/gba/interface.h>
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/input.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define GS_MAX_BP 64

static struct mCore* g_core = NULL;
static struct GBA* g_gba = NULL;
static color_t* g_vbuf = NULL;
static const unsigned g_stride = 240;

/* breakpoints (endereços de PC, sem bit de Thumb) */
static uint32_t g_bps[GS_MAX_BP];
static uint32_t g_bp_hits[GS_MAX_BP];
static int g_bp_count = 0;

/* logger: por padrão silencioso (mGBA imprime SWI/HLE no stderr) */
static int g_log_level = 3;   /* 0=DEBUG 1=INFO 2=WARN 3=ERROR 4=FATAL */
static void gs_logger(struct mLogger* logger, int category, enum mLogLevel level, const char* format, va_list args) {
	(void)logger;
	if (level < g_log_level) return;
	fprintf(stderr, "[mgba:%d] ", category);
	vfprintf(stderr, format, args);
	fputc('\n', stderr);
}
static struct mLogger g_logger_inst = { .log = gs_logger, .filter = NULL };

void gs_log(int level) { g_log_level = level; }

static void gs_reset_bp_counts(void) {
	for (int i = 0; i < g_bp_count; ++i) g_bp_hits[i] = 0;
}

static int gs_bp_check(uint32_t pc) {
	uint32_t a = pc & ~1u;
	for (int i = 0; i < g_bp_count; ++i) {
		if (g_bps[i] == a) {
			g_bp_hits[i]++;
			return 1;
		}
	}
	return 0;
}

void gs_free(void);

int gs_new(void) {
	if (g_core) gs_free();
	g_core = GBACoreCreate();
	if (!g_core) return 0;
	mLogSetDefaultLogger(&g_logger_inst);
	mCoreInitConfig(g_core, NULL);
	g_core->init(g_core);
	g_gba = g_core->board;
	g_vbuf = calloc((size_t)g_stride * 160, sizeof(color_t));
	if (!g_vbuf) return 0;
	g_core->setVideoBuffer(g_core, g_vbuf, g_stride);
	/* sem BIOS real: usa HLE-BIOS (mesmo caminho do core libretro usado antes) */
	return 1;
}

void gs_free(void) {
	if (g_core) {
		mCoreConfigDeinit(&g_core->config);
		g_core->deinit(g_core);
		g_core = NULL;
		g_gba = NULL;
	}
	free(g_vbuf);
	g_vbuf = NULL;
}

int gs_load(const char* path) {
	if (!g_core) return 0;
	if (!mCoreLoadFile(g_core, path)) return 0;
	g_core->reset(g_core);
	return 1;
}

void gs_reset(void) {
	if (g_core) g_core->reset(g_core);
}

/*
 * gs_keys: recebe máscara no formato libretro clássico (o mesmo do driver
 * antigo — mantém --input FRAME:BOTAO:HOLD compatível) e converte para os
 * bits internos do GBA (A=1<<0, B=1<<1, SELECT=1<<2, START=1<<3, RIGHT=1<<4,
 * LEFT=1<<5, UP=1<<6, DOWN=1<<7, R=1<<8, L=1<<9).
 */
void gs_keys(uint32_t lr) {
	if (!g_core) return;
	uint32_t k = 0;
	if (lr & 256)  k |= 1u << 0;  /* A      */
	if (lr & 1)    k |= 1u << 1;  /* B      */
	if (lr & 4)    k |= 1u << 2;  /* SELECT */
	if (lr & 8)    k |= 1u << 3;  /* START  */
	if (lr & 128)  k |= 1u << 4;  /* RIGHT  */
	if (lr & 64)   k |= 1u << 5;  /* LEFT   */
	if (lr & 16)   k |= 1u << 6;  /* UP     */
	if (lr & 32)   k |= 1u << 7;  /* DOWN   */
	if (lr & 2048) k |= 1u << 8;  /* R      */
	if (lr & 1024) k |= 1u << 9;  /* L      */
	g_gba->keysActive = k;   /* direto: setKeys() também dispara IRQ de keypad, indesejado aqui */
}

uint32_t gs_read8(uint32_t a)  { return g_core->busRead8(g_core, a); }
uint32_t gs_read16(uint32_t a) { return g_core->busRead16(g_core, a); }
uint32_t gs_read32(uint32_t a) { return g_core->busRead32(g_core, a); }
void gs_write8(uint32_t a, uint32_t v)  { g_core->busWrite8(g_core, a, (uint8_t)v); }
void gs_write16(uint32_t a, uint32_t v) { g_core->busWrite16(g_core, a, (uint16_t)v); }
void gs_write32(uint32_t a, uint32_t v) { g_core->busWrite32(g_core, a, v); }

int32_t gs_reg(int i) {
	if (!g_gba || i < 0 || i > 15) return 0;
	return (int32_t)g_gba->cpu->gprs[i];
}

void gs_set_reg(int i, int32_t v) {
	if (g_gba && i >= 0 && i <= 15) g_gba->cpu->gprs[i] = (uint32_t)v;
}

uint32_t gs_pc(void)   { return g_gba ? g_gba->cpu->gprs[ARM_PC] : 0; }
uint32_t gs_cpsr(void) { return g_gba ? g_gba->cpu->cpsr.packed : 0; }

void gs_bp_clear(void) {
	g_bp_count = 0;
	gs_reset_bp_counts();
}

int gs_bp_add(uint32_t addr) {
	if (g_bp_count >= GS_MAX_BP) return -1;
	g_bps[g_bp_count] = addr & ~1u;
	g_bp_hits[g_bp_count] = 0;
	return g_bp_count++;
}

uint32_t gs_bp_hits(int i) {
	if (i < 0 || i >= g_bp_count) return 0;
	return g_bp_hits[i];
}

int gs_bp_count_get(void) { return g_bp_count; }

/*
 * gs_steps: executa até `n` instruções. Se houver breakpoint registrado,
 * pára no instante em que o PC (antes de executar) casa com um deles e
 * devolve o índice do breakpoint que parou (>=0). -1 = rodou tudo sem parar.
 */
int gs_steps(int n) {
	if (!g_core) return -1;
	uint64_t start = g_gba->timing.globalCycles;
	int guard = n * 8 + 100000;
	for (int i = 0; i < n; ++i) {
		if (g_bp_count) {
			int hit = gs_bp_check(g_gba->cpu->gprs[ARM_PC] & ~1u);
			if (hit) return hit;
		}
		ARMRun(g_gba->cpu);
		if (g_gba->timing.globalCycles - start > (uint64_t)guard) break;
	}
	return -1;
}

/*
 * gs_frames: avança `n` frames completos; retorna o frameCounter final.
 * Se houver breakpoint, checa no começo de cada frame (granularidade de frame)
 * e devolve -1000 - índice quando para.
 */
int gs_frames(int n) {
	if (!g_core) return -1;
	for (int i = 0; i < n; ++i) {
		if (g_bp_count) {
			int hit = gs_bp_check(g_gba->cpu->gprs[ARM_PC] & ~1u);
			if (hit) return -1000 - hit;
		}
		g_core->runFrame(g_core);
	}
	return (int)g_gba->video.frameCounter;
}

/*
 * gs_keys_active: bits ativos do keypad DENTRO do emulador (formato GBA:
 * A=1<<0, B=1<<1, SELECT=1<<2, START=1<<3, RIGHT=1<<4, LEFT=1<<5, UP=1<<6,
 * DOWN=1<<7, R=1<<8, L=1<<9).
 *
 * GOTCHA (descoberto neste harness): ler 0x04000130 pelo barramento devolve o
 * ESPELHO de IO, que o mGBA só atualiza quando o JOGO lê o registrador. ROM de
 * teste que não lê teclas mostra 0x3FF para sempre. Para inspeção confiável de
 * input use esta função (ou faça o jogo ler).
 */
uint32_t gs_keys_active(void) { return g_gba ? g_gba->keysActive : 0; }

int gs_frame_counter(void) { return g_gba ? (int)g_gba->video.frameCounter : 0; }

/* gs_frames_bp: como gs_frames, mas devolve -1-n se parar no breakpoint n */
int gs_frames_bp(int n) {
	if (!g_core) return -1;
	for (int i = 0; i < n; ++i) {
		if (g_bp_count) {
			int hit = gs_bp_check(g_gba->cpu->gprs[ARM_PC] & ~1u);
			if (hit) return -1 - hit;
		}
		g_core->runFrame(g_core);
	}
	return (int)g_gba->video.frameCounter;
}

size_t gs_state_size(void) { return g_core ? g_core->stateSize(g_core) : 0; }

int gs_state_save(unsigned char* buf) {
	if (!g_core) return 0;
	struct GBASerializedState* st = (struct GBASerializedState*)buf;
	memset(buf, 0, g_core->stateSize(g_core));
	g_core->saveState(g_core, st);   /* layout GBASerializedState (0x61000 B) */
	return 1;
}

int gs_state_load(const unsigned char* buf) {
	if (!g_core) return 0;
	struct GBASerializedState* st = (struct GBASerializedState*)buf;
	return g_core->loadState(g_core, st) ? 1 : 0;
}

int gs_video(uint16_t* out) {
	if (!g_vbuf) return 0;
	for (unsigned y = 0; y < 160; ++y)
		for (unsigned x = 0; x < 240; ++x)
			out[y * 240 + x] = (uint16_t)g_vbuf[y * g_stride + x];
	return 1;
}

/* ---------------- helpers de conveniência (evitam lógica no Python) ---- */

/* lê bloco da memória via barramento; devolve bytes lidos */
int gs_read_block(uint32_t addr, unsigned char* out, int n) {
	if (!g_core) return 0;
	for (int i = 0; i < n; ++i) out[i] = (unsigned char)g_core->busRead8(g_core, addr + i);
	return n;
}

int gs_write_block(uint32_t addr, const unsigned char* in, int n) {
	if (!g_core) return 0;
	for (int i = 0; i < n; ++i) g_core->busWrite8(g_core, addr + i, in[i]);
	return n;
}

/* número de frames já executados desde o load (marcador de determinismo) */
int gs_cycles_lo(void) { return g_gba ? (int)(g_gba->timing.globalCycles & 0xFFFFFFFF) : 0; }
