-- Log every GRETC.RLZ group load (loader 0x80014CCC): request struct, then the directory after lookup.
-- Use: emu.py CUE --out DIR --script tools/lua/gretc_probe.lua --frames N [--route ...]
local ffi = require("ffi")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local function u32(a) a = a % 0x200000; return mem[a] + mem[a+1]*256 + mem[a+2]*65536 + mem[a+3]*16777216 end
local function str(a) a = a % 0x200000; local t = {}; while mem[a] ~= 0 and #t < 40 do t[#t+1] = string.char(mem[a]); a = a + 1 end; return table.concat(t) end
local function hex(a, n) a = a % 0x200000; local t = {}; for i = 0, n-1 do t[#t+1] = string.format("%02x", mem[a+i]) end; return table.concat(t, " ") end
local frame = 0
L.on_frame(function(n) frame = n end)
L.on_exec(0x80014CCC, function()
  local a0 = PCSX.getRegisters().GPR.n.a0
  local w = {}
  for i = 0, 7 do w[#w+1] = string.format("%08x", u32(a0 + 4*i)) end
  local nm = u32(a0 + 4)
  L.log(string.format("LOAD f=%d req=%08x [%s] name=%s", frame, a0, table.concat(w, " "), nm >= 0x80000000 and str(nm) or "-"))
end)
L.on_exec(0x80014EC0, function()
  local s = 0x800B6720
  local ents, hdr = u32(s), u32(s + 0x20)
  local cnt = u32(hdr + 0x8c)
  L.log(string.format("DIR f=%d ents=%08x hdr=%08x count=%d sel=%08x nsel=%d", frame, ents, hdr, cnt, u32(s+8), u32(s+0xc)))
  L.log("  hdr " .. hex(hdr, 0x90))
  if DUMP and not dumped then dumped = true; L.dump_ram(DUMP) end
  for i = 0, math.min(cnt, 400) - 1 do
    local e = ents + i * 0x34
    L.log(string.format("  %3d %s %s", i, hex(e, 13), str(e + 13)))
  end
end)
