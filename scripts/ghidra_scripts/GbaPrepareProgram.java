// Prepara um programa Ghidra de ROM de GBA (ARMv4T): mapa de memoria, cabecalho
// do cartucho, rotulos documentados e seeds de entrada ARM/Thumb.
//
// Roda como pre-script (antes da auto-analise) e como post-script (evidencias).
//@category GBA
//@description Mapeia a memoria do GBA, marca o cabecalho do cartucho e semeia as entradas ARM/Thumb.
//@menupath

import java.io.File;
import java.io.PrintWriter;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Language;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;

public class GbaPrepareProgram extends GhidraScript {

	// ---------------------------------------------------------------------
	// Constantes de hardware (GBATEK) e do projeto
	// ---------------------------------------------------------------------
	private static final long ROM_BASE = 0x08000000L;
	private static final long ROM_MAX_SIZE = 0x02000000L; // 32 MB
	private static final int HEADER_LENGTH = 0xC0;
	private static final long ROM_BLOCK_MIN_ACCEPT = 0x200; // 512 B: minimo para cabecalho + algo

	/** Regiao do mapa de memoria a materializar no programa. */
	private static final class Region {
		final String name;
		final long start;
		final long size;
		final boolean read;
		final boolean write;
		final boolean execute;
		final String note;

		Region(String name, long start, long size, boolean read, boolean write, boolean execute,
				String note) {
			this.name = name;
			this.start = start;
			this.size = size;
			this.read = read;
			this.write = write;
			this.execute = execute;
			this.note = note;
		}
	}

	private static final Region[] REGIONS = {
		// EWRAM 256 KB: memoria de trabalho do jogo (inclui o array da mochila)
		new Region("GBA_EWRAM_256K", 0x02000000L, 0x00040000L, true, true, false,
			"EWRAM (256 KB) - GBATEK"),
		// IWRAM 32 KB
		new Region("GBA_IWRAM_32K", 0x03000000L, 0x00008000L, true, true, false,
			"IWRAM (32 KB) - GBATEK"),
		// Registradores de I/O
		new Region("GBA_IO_REGISTERS", 0x04000000L, 0x00000400L, true, true, false,
			"Memoria de I/O mapeada - GBATEK"),
		// Paleta
		new Region("GBA_PALETTE_RAM", 0x05000000L, 0x00000400L, true, true, false,
			"Paleta (1 KB) - GBATEK"),
		// VRAM
		new Region("GBA_VRAM_96K", 0x06000000L, 0x00018000L, true, true, false,
			"VRAM (96 KB) - GBATEK"),
		// OAM
		new Region("GBA_OAM", 0x07000000L, 0x00000400L, true, true, false,
			"OAM (1 KB) - GBATEK"),
	};

	/** Mirrors de barramento da ROM (0x0A000000..0x0E000000). Opcionais. */
	private static final Region[] MIRROR_REGIONS = {
		new Region("GBA_ROM_MIRROR_0A", 0x0A000000L, ROM_MAX_SIZE, true, false, true,
			"Mirror de barramento da ROM (nao e memoria fisica separada) - GBATEK"),
		new Region("GBA_ROM_MIRROR_0C", 0x0C000000L, ROM_MAX_SIZE, true, false, true,
			"Mirror de barramento da ROM (nao e memoria fisica separada) - GBATEK"),
		new Region("GBA_ROM_MIRROR_0E", 0x0E000000L, ROM_MAX_SIZE, true, false, true,
			"Mirror de barramento da ROM (nao e memoria fisica separada) - GBATEK"),
	};

	/**
	 * Rotulos criados no programa.
	 * confidence: CONFIRMADO (GBATEK/medido no projeto) | HIPOTESE (nao validado).
	 */
	private static final Object[][] LABELS = {
		{ 0x08000000L, "gba_cart_header", "CONFIRMADO",
			"Cabecalho do cartucho GBA (0xC0 bytes) - GBATEK secao 9.2" },
		{ 0x080000A0L, "gba_game_title", "CONFIRMADO", "Titulo do jogo, 12 bytes ASCII - GBATEK" },
		{ 0x080000ACL, "gba_game_code", "CONFIRMADO", "Codigo do jogo, 4 bytes - GBATEK" },
		{ 0x080000B0L, "gba_maker_code", "CONFIRMADO", "Codigo do fabricante, 2 bytes - GBATEK" },
		{ 0x080000BCL, "gba_header_checksum_word", "CONFIRMADO",
			"Palavra com a versao (0xBC) e o complemento (0xBD) - GBATEK" },
		{ 0x080000C0L, "gba_word_at_0xC0", "OBSERVADO",
			"Palavra de 32 bits logo apos o cabecalho; reportada sem interpretacao" },
		{ 0x04000000L, "REG_DISPCNT", "CONFIRMADO", "Display control - GBATEK (0x04000000)" },
		{ 0x04000004L, "REG_DISPSTAT", "CONFIRMADO", "Display status - GBATEK" },
		{ 0x04000006L, "REG_VCOUNT", "CONFIRMADO", "Linha atual do scanline - GBATEK" },
		{ 0x04000130L, "REG_KEYINPUT", "CONFIRMADO",
			"Estado das teclas, ativo-baixo (0 = pressionado) - GBATEK" },
		{ 0x04000200L, "REG_IE", "CONFIRMADO", "Interrupt enable - GBATEK" },
		{ 0x04000202L, "REG_IF", "CONFIRMADO", "Interrupt request flags - GBATEK" },
		{ 0x04000208L, "REG_IME", "CONFIRMADO", "Interrupt master enable - GBATEK" },
		{ 0x020258B8L, "gBagSlots_slot0", "CONFIRMADO",
			"slot 0 da mochila {id:u16, qty:u16}, 4 B/slot - provado neste projeto (README)" },
		{ 0x03003118L, "gKeysMirror_HIPOTESE", "HIPOTESE",
			"espelho de teclas contexto-dependente - ver HANDOFF.md (bug aberto)" },
		{ 0x08000A38L, "SetGpuReg", "CONFIRMADO",
			"rotina por-frame usada no hook v3 (site do veneer) - CONFIRMADO no projeto" },
	};

	private static final int MAX_LISTED_FUNCTIONS = 60;

	// ---------------------------------------------------------------------
	// Entrada
	// ---------------------------------------------------------------------
	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		String mode = args.length > 0 ? args[0] : "pre";
		String evidenceDir = args.length > 1 ? args[1] : System.getProperty("java.io.tmpdir");
		boolean mirrors = hasFlag(args, "--mirrors");

		if ("self-test".equals(mode)) {
			runSelfTest();
			return;
		}
		if (!"pre".equals(mode) && !"post".equals(mode)) {
			throw new IllegalArgumentException(
				"modo invalido: " + mode + " (use pre, post ou self-test)");
		}

		File dir = new File(evidenceDir);
		if (!dir.exists() && !dir.mkdirs()) {
			throw new IllegalStateException("nao foi possivel criar " + dir.getAbsolutePath());
		}

		Map<String, Object> report = new LinkedHashMap<>();
		report.put("schema", "gba-prepare/v1");
		report.put("mode", mode);
		report.put("program_name", currentProgram.getName());
		report.put("language_id", currentProgram.getLanguageID().toString());
		report.put("compiler_spec_id", currentProgram.getCompilerSpec().getCompilerSpecID().toString());

		if ("pre".equals(mode)) {
			doPre(report, mirrors);
		}
		else {
			doPost(report);
		}

		File out = new File(dir, "gba_prepare_" + mode + ".json");
		try (PrintWriter pw = new PrintWriter(out, "UTF-8")) {
			pw.println(toJson(report, 0));
		}
		println("[gba] evidencia escrita: " + out.getAbsolutePath());
	}

	private boolean hasFlag(String[] args, String flag) {
		return Arrays.asList(args).contains(flag);
	}

	// ---------------------------------------------------------------------
	// PRE: mapa de memoria + cabecalho + seeds (roda antes da auto-analise)
	// ---------------------------------------------------------------------
	private void doPre(Map<String, Object> report, boolean withMirrors) throws Exception {
		Map<String, Object> warnings = new LinkedHashMap<>();
		List<Object> createdBlocks = new ArrayList<>();
		List<Object> existingBlocks = new ArrayList<>();
		List<String> labelResults = new ArrayList<>();
		List<Object> seeds = new ArrayList<>();

		Memory memory = currentProgram.getMemory();
		MemoryBlock romBlock = findRomBlock(memory);
		if (romBlock == null) {
			addWarning(warnings, "rom_block_missing",
				"nenhum bloco cobre 0x08000000; o import provavelmente falhou");
			report.put("warnings", warnings);
			return;
		}

		// Permissoes do bloco da ROM: leitura + execucao (necessario para desmontar).
		if (!romBlock.isExecute()) {
			romBlock.setPermissions(true, false, true);
			createdBlocks.add(describeBlock(romBlock));
		}

		long romSize = romBlock.getSize();
		report.put("rom_block", describeBlock(romBlock));
		if (romSize < ROM_BLOCK_MIN_ACCEPT) {
			addWarning(warnings, "rom_too_small",
				String.format(Locale.ROOT, "bloco da ROM com %d bytes (< %d)", romSize,
					ROM_BLOCK_MIN_ACCEPT));
		}
		if (romSize > ROM_MAX_SIZE) {
			addWarning(warnings, "rom_too_large",
				String.format(Locale.ROOT, "bloco da ROM com %d bytes (> 32 MB)", romSize));
		}

		// ---- mapa de memoria -------------------------------------------------
		for (Region region : REGIONS) {
			createRegion(memory, region, createdBlocks, existingBlocks, warnings);
		}
		if (withMirrors) {
			for (Region region : MIRROR_REGIONS) {
				createRegion(memory, region, createdBlocks, existingBlocks, warnings);
			}
		}
		report.put("blocks_created", createdBlocks);
		report.put("blocks_already_present", existingBlocks);

		// ---- cabecalho do cartucho -------------------------------------------
		Map<String, Object> header = new LinkedHashMap<>();
		if (romSize >= HEADER_LENGTH) {
			try {
				byte[] h = new byte[HEADER_LENGTH];
				int read = memory.getBytes(toAddr(ROM_BASE), h);
				if (read != HEADER_LENGTH) {
					addWarning(warnings, "header_short_read",
						"leitura do cabecalho retornou " + read + " de " + HEADER_LENGTH + " bytes");
				}
				header = parseHeader(h);
				if (romSize >= HEADER_LENGTH + 4) {
					header.put("word_at_0xC0",
						hex(memory.getInt(toAddr(ROM_BASE + HEADER_LENGTH)) & 0xFFFFFFFFL));
				}
			}
			catch (Exception e) {
				addWarning(warnings, "header_read_failed",
					e.getClass().getSimpleName() + ": " + e.getMessage());
			}
			report.put("header", header);
		}
		else {
			addWarning(warnings, "header_unavailable", "ROM menor que 0xC0 bytes");
		}

		// ---- rotulos documentados --------------------------------------------
		for (Object[] entry : LABELS) {
			long address = ((Number) entry[0]).longValue();
			String name = (String) entry[1];
			String confidence = (String) entry[2];
			String comment = (String) entry[3];
			labelResults.add(applyLabel(address, name, confidence, comment));
		}
		report.put("labels", labelResults);

		// ---- seeds de entrada --------------------------------------------------
		seedEntryPoints(memory, romSize, seeds, warnings);
		report.put("seeds", seeds);
		report.put("warnings", warnings);
	}

	private void createRegion(Memory memory, Region region, List<Object> created,
			List<Object> existing, Map<String, Object> warnings) {
		String name = region.name;
		try {
			MemoryBlock existingBlock = memory.getBlock(name);
			if (existingBlock != null) {
				existing.add(describeBlock(existingBlock));
				return;
			}
			Address start = toAddr(region.start);
			if (memory.getBlock(start) != null) {
				addWarning(warnings, "region_overlap",
					name + " nao criado: endereco " + hex(region.start) + " ja mapeado");
				return;
			}
			MemoryBlock block = memory.createUninitializedBlock(name, start, region.size, false);
			block.setPermissions(region.read, region.write, region.execute);
			block.setComment(region.note);
			Map<String, Object> info = describeBlock(block);
			info.put("note", region.note);
			created.add(info);
		}
		catch (Exception e) {
			addWarning(warnings, "region_create_failed",
				name + ": " + e.getClass().getSimpleName() + ": " + e.getMessage());
		}
	}

	private String applyLabel(long address, String name, String confidence, String comment) {
		Address addr = toAddr(address);
		try {
			Symbol symbol = createLabel(addr, name, true);
			String text = "[" + confidence + "] " + comment;
			setPlateComment(addr, text);
			String existing = currentProgram.getListing().getComment(
				ghidra.program.model.listing.CodeUnit.PLATE_COMMENT, addr);
			return hex(address) + " " + (symbol != null ? symbol.getName() : name) + " ("
				+ confidence + ")"
				+ (existing != null ? " +comment" : "");
		}
		catch (Exception e) {
			return hex(address) + " " + name + " FALHOU: " + e.getClass().getSimpleName() + ": "
				+ e.getMessage();
		}
	}

	private void seedEntryPoints(Memory memory, long romSize, List<Object> seeds,
			Map<String, Object> warnings) {
		int firstWord;
		try {
			firstWord = memory.getInt(toAddr(ROM_BASE));
		}
		catch (Exception e) {
			addWarning(warnings, "entry_read_failed", e.getClass().getSimpleName() + ": " + e.getMessage());
			return;
		}

		Map<String, Object> branch = new LinkedHashMap<>();
		branch.put("address", hex(ROM_BASE));
		branch.put("word", hex(firstWord & 0xFFFFFFFFL));
		Long target = armBranchTarget(ROM_BASE, firstWord);
		branch.put("decoded_target", target == null ? null : hex(target));
		seeds.add(branch);

		if (target == null) {
			addWarning(warnings, "entry_not_arm_branch",
				"primeira palavra nao e um B ARM (0xEA......); nenhum seed ARM criado");
			return;
		}

		if (!insideRom(target, romSize)) {
			addWarning(warnings, "entry_target_outside_rom",
				"alvo do B " + hex(target) + " fora do bloco da ROM");
			return;
		}

		Map<String, Object> armSeed = new LinkedHashMap<>();
		armSeed.put("address", hex(target));
		armSeed.put("mode", "ARM");
		armSeed.put("method", "branch-decode");
		armSeed.put("confidence", "CONFIRMADO");
		try {
			Function fn = createFunction(toAddr(target), "gba_entry_arm");
			armSeed.put("created", fn != null);
		}
		catch (Exception e) {
			armSeed.put("created", false);
			armSeed.put("error", e.getClass().getSimpleName() + ": " + e.getMessage());
			addWarning(warnings, "arm_seed_failed", e.getClass().getSimpleName() + ": " + e.getMessage());
		}
		seeds.add(armSeed);

		// Heuristica: `ldr rX, [pc, #imm]` seguido de ponteiro impar (Thumb).
		Long thumbTarget = armLdrLiteralThumbTarget(memory, target, romSize);
		if (thumbTarget != null) {
			Map<String, Object> thumbSeed = new LinkedHashMap<>();
			thumbSeed.put("address", hex(thumbTarget));
			thumbSeed.put("mode", "Thumb");
			thumbSeed.put("method", "arm-ldr-literal-bit0");
			thumbSeed.put("confidence", "HIPOTESE");
			try {
				setThumbContext(thumbTarget);
				disassemble(toAddr(thumbTarget));
				Function fn = createFunction(toAddr(thumbTarget), "gba_entry_thumb_guess");
				thumbSeed.put("created", fn != null);
			}
			catch (Exception e) {
				thumbSeed.put("created", false);
				thumbSeed.put("error", e.getClass().getSimpleName() + ": " + e.getMessage());
				addWarning(warnings, "thumb_seed_failed",
					e.getClass().getSimpleName() + ": " + e.getMessage());
			}
			seeds.add(thumbSeed);
		}
		else {
			addWarning(warnings, "thumb_seed_skipped",
				"nenhum ponteiro Thumb encontrado por ldr literal no alvo do B");
		}
	}

	/**
	 * Marca o contexto TMode (Thumb) em [addr, addr] para que a desmontagem use Thumb.
	 * O nome do registrador de contexto vem da linguagem carregada.
	 */
	private void setThumbContext(long address) throws Exception {
		Language language = currentProgram.getLanguage();
		Register tmode = language.getRegister("TMode");
		if (tmode == null) {
			tmode = language.getRegister("TBmode");
		}
		if (tmode == null) {
			throw new IllegalStateException(
				"registrador de contexto TMode nao encontrado na linguagem "
					+ language.getLanguageID());
		}
		Address addr = toAddr(address);
		currentProgram.getProgramContext().setValue(tmode, addr, addr, BigInteger.ONE);
	}

	// ---------------------------------------------------------------------
	// POST: verificacao e evidencias (roda depois da auto-analise)
	// ---------------------------------------------------------------------
	private void doPost(Map<String, Object> report) throws Exception {
		Map<String, Object> warnings = new LinkedHashMap<>();
		Memory memory = currentProgram.getMemory();
		MemoryBlock romBlock = findRomBlock(memory);

		List<Object> blocks = new ArrayList<>();
		for (MemoryBlock block : memory.getBlocks()) {
			blocks.add(describeBlock(block));
		}
		report.put("blocks", blocks);

		Map<String, Object> analysis = new LinkedHashMap<>();
		int functionCount = currentProgram.getFunctionManager().getFunctionCount();
		analysis.put("function_count", functionCount);

		List<Object> romFunctions = new ArrayList<>();
		if (romBlock != null) {
			FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
			int listed = 0;
			while (it.hasNext() && listed < MAX_LISTED_FUNCTIONS) {
				Function fn = it.next();
				long entry = fn.getEntryPoint().getOffset();
				if (!insideRom(entry, romBlock.getSize())) {
					continue;
				}
				Map<String, Object> info = new LinkedHashMap<>();
				info.put("name", fn.getName());
				info.put("entry", hex(entry));
				info.put("body_size", fn.getBody().getNumAddresses());
				romFunctions.add(info);
				listed++;
			}
			analysis.put("rom_functions_listed", romFunctions.size());
			analysis.put("rom_functions_truncated", listed >= MAX_LISTED_FUNCTIONS);
		}
		analysis.put("rom_functions", romFunctions);

		SymbolTable symbols = currentProgram.getSymbolTable();
		int symbolCount = 0;
		SymbolIterator sit = symbols.getAllSymbols(true);
		while (sit.hasNext()) {
			sit.next();
			symbolCount++;
		}
		analysis.put("symbol_count", symbolCount);
		analysis.put("reference_destination_count",
			currentProgram.getReferenceManager().getReferenceDestinationCount());
		analysis.put("reference_source_count",
			currentProgram.getReferenceManager().getReferenceSourceCount());

		List<String> anchorsFound = new ArrayList<>();
		List<String> anchorsMissing = new ArrayList<>();
		String[] anchors = { "gba_cart_header", "gba_game_title", "REG_KEYINPUT", "gBagSlots_slot0",
			"SetGpuReg", "gba_entry_arm" };
		for (String anchor : anchors) {
			List<Symbol> found = symbols.getGlobalSymbols(anchor);
			if (found != null && !found.isEmpty()) {
				anchorsFound.add(anchor + "@" + hex(found.get(0).getAddress().getOffset()));
			}
			else {
				anchorsMissing.add(anchor);
			}
		}
		analysis.put("anchors_found", anchorsFound);
		analysis.put("anchors_missing", anchorsMissing);
		if (!anchorsMissing.isEmpty()) {
			addWarning(warnings, "anchors_missing",
				"rotulos ausentes: " + anchorsMissing);
		}
		if (functionCount == 0) {
			addWarning(warnings, "no_functions",
				"nenhuma funcao no programa (analise desligada ou falhou)");
		}

		report.put("analysis", analysis);
		report.put("warnings", warnings);
	}

	// ---------------------------------------------------------------------
	// Logica pura (testavel sem programa): cabecalho e decodificacao de branch
	// ---------------------------------------------------------------------

	/** Alvo de um B ARM (0xEA......) ou null se a palavra nao for B. */
	static Long armBranchTarget(long pc, int word) {
		if (((word >>> 24) & 0xFF) != 0xEA) {
			return null;
		}
		int imm = word & 0xFFFFFF;
		if ((imm & 0x800000) != 0) {
			imm -= 0x1000000; // extensao de sinal de 24 bits
		}
		return (pc + 8L + (imm * 4L)) & 0xFFFFFFFFL;
	}

	/** Campos do cabecalho GBA (GBATEK secao 9.2) e verificacao do complemento. */
	static Map<String, Object> parseHeader(byte[] h) {
		Map<String, Object> out = new LinkedHashMap<>();
		if (h == null || h.length < HEADER_LENGTH) {
			out.put("available", false);
			return out;
		}
		out.put("available", true);
		out.put("title", asciiTrimmed(h, 0xA0, 12));
		out.put("game_code", asciiTrimmed(h, 0xAC, 4));
		out.put("maker_code", asciiTrimmed(h, 0xB0, 2));
		out.put("fixed_value_0xB2", hex(h[0xB2] & 0xFF));
		out.put("fixed_value_ok", (h[0xB2] & 0xFF) == 0x96);
		out.put("main_unit_code", hex(h[0xB3] & 0xFF));
		out.put("device_type", hex(h[0xB4] & 0xFF));
		out.put("software_version", h[0xBC] & 0xFF);
		out.put("complement_byte", hex(h[0xBD] & 0xFF));

		int sum = 0;
		for (int i = 0xA0; i <= 0xBC; i++) {
			sum += h[i] & 0xFF;
		}
		int expected = (-(sum + 0x19)) & 0xFF;
		out.put("complement_sum", hex(sum));
		out.put("complement_expected", hex(expected));
		out.put("complement_ok", expected == (h[0xBD] & 0xFF));
		out.put("entry_branch_word", hex(readIntLe(h, 0)));
		Long target = armBranchTarget(ROM_BASE, readIntLe(h, 0));
		out.put("entry_branch_target", target == null ? null : hex(target));
		return out;
	}

	static int readIntLe(byte[] b, int offset) {
		if (b == null || offset < 0 || offset + 4 > b.length) {
			return 0;
		}
		return (b[offset] & 0xFF) | ((b[offset + 1] & 0xFF) << 8) | ((b[offset + 2] & 0xFF) << 16)
			| ((b[offset + 3] & 0xFF) << 24);
	}

	static String asciiTrimmed(byte[] b, int offset, int length) {
		StringBuilder sb = new StringBuilder();
		for (int i = offset; i < offset + length && i < b.length; i++) {
			int c = b[i] & 0xFF;
			if (c == 0) {
				break;
			}
			sb.append(c >= 0x20 && c < 0x7F ? (char) c : '.');
		}
		return sb.toString().trim();
	}

	/**
	 * Se a instrucao em {@code armAddr} for `ldr rX, [pc, #imm]` e o literal for
	 * um ponteiro impar dentro da ROM, devolve o endereco Thumb (bit 0 limpo).
	 */
	Long armLdrLiteralThumbTarget(Memory memory, long armAddr, long romSize) {
		try {
			int word = memory.getInt(toAddr(armAddr));
			// ARM LDR (imediato): 1110 01 0 1 1 0 0 1 1111 Rd imm12  (0xE59Fxxxx)
			if ((word & 0xFFFFF000) != 0xE59F0000) {
				return null;
			}
			int imm12 = word & 0xFFF;
			long literalAddr = armAddr + 8L + imm12;
			if (!insideRom(literalAddr, romSize) || literalAddr + 4 > ROM_BASE + romSize) {
				return null;
			}
			int literal = memory.getInt(toAddr(literalAddr));
			long value = literal & 0xFFFFFFFFL;
			if ((value & 1L) == 0L) {
				return null;
			}
			long thumb = value & ~1L;
			if (!insideRom(thumb, romSize)) {
				return null;
			}
			return thumb;
		}
		catch (Exception e) {
			return null;
		}
	}

	// ---------------------------------------------------------------------
	// Self-test (vetores fixos; roda sem programa)
	// ---------------------------------------------------------------------
	private void runSelfTest() {
		List<String> failures = new ArrayList<>();
		List<String> passes = new ArrayList<>();

		// Vetor fixedo: cabecalho sintetico com titulo "POKEMON FIRE", codigo BPRE.
		byte[] header = new byte[HEADER_LENGTH];
		byte[] title = "POKEMON FIRE".getBytes(StandardCharsets.US_ASCII);
		System.arraycopy(title, 0, header, 0xA0, 12);
		System.arraycopy("BPRE".getBytes(StandardCharsets.US_ASCII), 0, header, 0xAC, 4);
		System.arraycopy("01".getBytes(StandardCharsets.US_ASCII), 0, header, 0xB0, 2);
		header[0xB2] = (byte) 0x96;
		header[0xBC] = 0;
		int sum = 0;
		for (int i = 0xA0; i <= 0xBC; i++) {
			sum += header[i] & 0xFF;
		}
		header[0xBD] = (byte) ((-(sum + 0x19)) & 0xFF);

		Map<String, Object> parsed = parseHeader(header);
		check(passes, failures, "header.title", "POKEMON FIRE", parsed.get("title"));
		check(passes, failures, "header.game_code", "BPRE", parsed.get("game_code"));
		check(passes, failures, "header.maker_code", "01", parsed.get("maker_code"));
		check(passes, failures, "header.fixed_value_ok", Boolean.TRUE, parsed.get("fixed_value_ok"));
		check(passes, failures, "header.complement_sum", "0x7F", parsed.get("complement_sum"));
		check(passes, failures, "header.complement_byte", "0x68", parsed.get("complement_byte"));
		check(passes, failures, "header.complement_ok", Boolean.TRUE, parsed.get("complement_ok"));

		// Cabecalho corrompido deve falhar a verificacao do complemento.
		byte[] corrupt = header.clone();
		corrupt[0xBD] = (byte) ((header[0xBD] + 1) & 0xFF);
		check(passes, failures, "header.complement_ok_corrupt", Boolean.FALSE,
			parseHeader(corrupt).get("complement_ok"));

		// Decodificacao de B ARM
		check(passes, failures, "branch.+0x2E", "0x080000C0",
			hexOrNull(armBranchTarget(0x08000000L, 0xEA00002E)));
		check(passes, failures, "branch.-1", "0x08000000",
			hexOrNull(armBranchTarget(0x08000000L, 0xEAFFFFFE)));
		check(passes, failures, "branch.0", "0x08000008",
			hexOrNull(armBranchTarget(0x08000000L, 0xEA000000)));
		check(passes, failures, "branch.not-b", null,
			hexOrNull(armBranchTarget(0x08000000L, 0xE92D4010)));

		println("[gba][self-test] " + passes.size() + " verificacoes OK, " + failures.size()
			+ " falha(s)");
		for (String pass : passes) {
			println("[gba][self-test]   OK   " + pass);
		}
		for (String failure : failures) {
			println("[gba][self-test]   FALHA " + failure);
		}
		if (!failures.isEmpty()) {
			throw new IllegalStateException("self-test falhou: " + failures);
		}
	}

	private void check(List<String> passes, List<String> failures, String label, Object expected,
			Object actual) {
		boolean ok = expected == null ? actual == null : expected.equals(actual);
		if (ok) {
			passes.add(label + " = " + actual);
		}
		else {
			failures.add(label + ": esperado " + expected + ", obtido " + actual);
		}
	}

	private String hexOrNull(Long value) {
		return value == null ? null : hex(value);
	}

	// ---------------------------------------------------------------------
	// Utilidades
	// ---------------------------------------------------------------------
	private MemoryBlock findRomBlock(Memory memory) {
		MemoryBlock block = memory.getBlock(toAddr(ROM_BASE));
		if (block == null) {
			for (MemoryBlock candidate : memory.getBlocks()) {
				if (candidate.getStart().getOffset() == ROM_BASE) {
					return candidate;
				}
			}
		}
		return block;
	}

	private static boolean insideRom(long address, long romSize) {
		return address >= ROM_BASE && address < ROM_BASE + romSize;
	}

	private static String hex(long value) {
		return String.format(Locale.ROOT, "0x%08X", value);
	}

	private Map<String, Object> describeBlock(MemoryBlock block) {
		Map<String, Object> info = new LinkedHashMap<>();
		info.put("name", block.getName());
		info.put("start", hex(block.getStart().getOffset()));
		info.put("size", block.getSize());
		info.put("end", hex(block.getEnd().getOffset()));
		info.put("read", block.isRead());
		info.put("write", block.isWrite());
		info.put("execute", block.isExecute());
		info.put("initialized", block.isInitialized());
		info.put("overlay", block.isOverlay());
		return info;
	}

	private void addWarning(Map<String, Object> warnings, String key, String message) {
		warnings.put(key, message);
		println("[gba] AVISO " + key + ": " + message);
	}

	// ---- JSON minimo (sem dependencias externas) ------------------------
	@SuppressWarnings("unchecked")
	private static String toJson(Object value, int indent) {
		String pad = repeat("  ", indent);
		String padIn = repeat("  ", indent + 1);
		if (value == null) {
			return "null";
		}
		if (value instanceof String) {
			return quote((String) value);
		}
		if (value instanceof Boolean || value instanceof Number) {
			return String.valueOf(value);
		}
		if (value instanceof Map) {
			Map<String, Object> map = (Map<String, Object>) value;
			if (map.isEmpty()) {
				return "{}";
			}
			StringBuilder sb = new StringBuilder("{\n");
			int i = 0;
			for (Map.Entry<String, Object> entry : map.entrySet()) {
				sb.append(padIn).append(quote(entry.getKey())).append(": ")
					.append(toJson(entry.getValue(), indent + 1));
				if (++i < map.size()) {
					sb.append(',');
				}
				sb.append('\n');
			}
			return sb.append(pad).append('}').toString();
		}
		if (value instanceof List) {
			List<Object> list = (List<Object>) value;
			if (list.isEmpty()) {
				return "[]";
			}
			StringBuilder sb = new StringBuilder("[\n");
			for (int i = 0; i < list.size(); i++) {
				sb.append(padIn).append(toJson(list.get(i), indent + 1));
				if (i + 1 < list.size()) {
					sb.append(',');
				}
				sb.append('\n');
			}
			return sb.append(pad).append(']').toString();
		}
		return quote(String.valueOf(value));
	}

	private static String quote(String text) {
		StringBuilder sb = new StringBuilder("\"");
		for (int i = 0; i < text.length(); i++) {
			char c = text.charAt(i);
			switch (c) {
				case '"':
					sb.append("\\\"");
					break;
				case '\\':
					sb.append("\\\\");
					break;
				case '\n':
					sb.append("\\n");
					break;
				case '\r':
					sb.append("\\r");
					break;
				case '\t':
					sb.append("\\t");
					break;
				default:
					if (c < 0x20) {
						sb.append(String.format(Locale.ROOT, "\\u%04x", (int) c));
					}
					else {
						sb.append(c);
					}
			}
		}
		return sb.append('"').toString();
	}

	private static String repeat(String unit, int count) {
		StringBuilder sb = new StringBuilder();
		for (int i = 0; i < count; i++) {
			sb.append(unit);
		}
		return sb.toString();
	}
}
