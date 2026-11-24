-- Text coverage probe (needs emu.py --debugger): logs "TEXT <fnv32>" once per distinct string the game reads, where
-- the hash is FNV-1a 32 of the bytes from the string's first byte up to its 0x00 (tools/strings_tsv.py hashes each
-- script id the same way into build/strings.tsv; textcover.py matches the two). Content keys survive relocation and
-- the reused text buffers (scenario, g13, txd heap).
-- Sources: read breakpoints on the static text ranges (EXE strings, scenario + g13 buffers, overlays, payload table +
-- string pool; this also catches sprintf format strings), and exec hooks on the renderers that take a pointer
-- (generic draw 0x80043A64 a2, txd markup 0x800133D4 a2, g13 indexed draw 0x80044680 s3).
-- Use: emu.py CUE --debugger --script tools/debug/warp.lua --script tools/lua/textcover.lua ... (regen.py --cover)
local ffi = require("ffi")
local bit = require("bit")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local frame, seen, last = 0, {}, {}
L.on_frame(function(n) frame = n end)

local function u8(a) return mem[bit.band(a, 0x1FFFFF)] end

local function take(a)
  a = a % 2^32
  if a < 0x80000000 or a >= 0x80200000 then return end
  local t = last[a]
  if t and frame - t < 60 then return end  -- same start re-read every frame: hash it once a second
  last[a] = frame
  local h = 2166136261
  for i = 0, 4095 do
    local b = u8(a + i)
    if b == 0 then
      if i == 0 then return end
      h = bit.tohex(h)
      if not seen[h] then seen[h] = true; L.log(string.format("TEXT %s f=%d at=%08X", h, frame, a)) end
      return
    end
    h = bit.bxor(h, b)
    h = bit.tobit(bit.lshift(h, 24) + h * 403)  -- h * 16777619 mod 2^32
  end
end

-- a read counts only at a string start: the byte before is 0x00 (NUL/padding) or 0x0A (scenario filler)
local function on_read(addr)
  local p = u8(addr - 1)
  if p ~= 0 and p ~= 0x0A then return end
  local pc = PCSX.getRegisters().pc % 2^32
  if pc >= 0x800CAC00 and pc < 0x800CAC40 then return end  -- boot stub copying the payload (asm/hooks.asm)
  take(addr)
end
-- read breakpoints only where printf format strings live (EXE menus/messages, overlays, string pool): the name
-- records (0x800B3A50..) and the scenario/g13 buffers are read every frame by the map code, which cost 5x speed
for _, r in ipairs({{0x80010000, 0x80012760}, {0x80162F8C, 0x80162FE8}, {0x8016621C, 0x80169048},
                    {0x801F4000, 0x801F7FFF}}) do
  L.on_read(r[1], r[2] - 1, on_read)
end
-- 0x80017E40 a3: txd book pages (OPTION dictionary etc.) sprintf "&e()%s&d()" onto the stack before 0x800133D4
-- 0x80166D50 a2: DIC.BIN page layout (overlay base+0xB38; other overlays at that base hash junk, matching no id)
-- 0x8016A468 a1: overlay 0x12 (title LOAD / card checks) expands "<a>" in a save.txd message into a stack buffer
-- before 0x800133D4, so the drawn bytes differ from the stored ones (other overlays there: junk hashes, no id)
for _, h in ipairs({{0x80043A64, "a2"}, {0x800133D4, "a2"}, {0x80044680, "s3"}, {0x80017E40, "a3"},
                    {0x80166D50, "a2"}, {0x8016A468, "a1"}}) do
  local reg = h[2]
  L.on_exec(h[1], function() take(PCSX.getRegisters().GPR.n[reg]) end)
end
-- evd op 0x34 (unit name, 0x8001E278 = j evd_name_hook, v0 = unit record): the hook stores the English pointer at
-- unit +0x10; read it on the next frame. Counts a name as reached when the map loads it (the generic draw shows it
-- only in unit menus).
local units = {}
L.on_exec(0x8001E278, function() units[#units + 1] = PCSX.getRegisters().GPR.n.v0 end)
L.on_frame(function()
  for i = #units, 1, -1 do
    local a, p = units[i], 0
    for j = 3, 0, -1 do p = p * 256 + u8(a + 0x10 + j) end
    take(p); units[i] = nil
  end
end)
L.on_exec(0x80043DA4, function()  -- scenario box: a0 = box, string at [a0 + 8]
  local a = PCSX.getRegisters().GPR.n.a0
  local p = 0
  for i = 3, 0, -1 do p = p * 256 + u8(a + 8 + i) end
  take(p)
end)
