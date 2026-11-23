-- 2D primitive pool (allocator 0x8004F664: struct at *0x8015238C, +0x10 base, +0x18 cap, +0x20 failed bytes,
-- +0x24 used, +0x34 failed calls): log the struct when the pointer changes and the peak use. No --debugger needed.
-- Use: emu.py ... --script tools/lua/pool2d.lua [--var FROM=1700] [--var DUMP=4760 (struct words +0..+0x38 per frame)]
local ffi = require("ffi")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local function u32(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
local last, peak = -1, {}
L.on_frame(function(f)
  if f < (FROM or 0) then return end
  local p = u32(0x8015238C)
  if p ~= last then
    last = p
    if p ~= 0 then
      L.log(string.format("POOL f=%d struct=%08X base=%08X cap=%X used=%X fail=%X/%d", f, p, u32(p + 0x10), u32(p + 0x18),
                          u32(p + 0x24), u32(p + 0x20), u32(p + 0x34)))
    end
  end
  if p ~= 0 and DUMP and f >= DUMP then
    local s = {}
    for o = 0, 0x38, 4 do s[#s + 1] = string.format("%X", u32(p + o)) end
    L.log(string.format("POOL dump f=%d %s", f, table.concat(s, " ")))
  end
  if p ~= 0 then
    local used = u32(p + 0x24)
    if used > (peak[p] or 0) then
      peak[p] = used
      if f % 10 == 0 or used > 0.9 * u32(p + 0x18) then
        L.log(string.format("POOL peak f=%d struct=%08X used=%X cap=%X fail=%d", f, p, used, u32(p + 0x18), u32(p + 0x34)))
      end
    end
  end
end)
