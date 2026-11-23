-- Walk the game's malloc arena (descriptor 0x8015B608, +0x40 = first block) at frame AT (or every EVERY frames from
-- FROM): blocks are a circular list in address order, header 0x1C bytes: +0 next, +4 prev, +8 used, +0xC size incl.
-- header, +0x14 magic 0x55. Logs HEAP lines (used/free bytes, largest free block, top used end) and, with LIST=1,
-- one BLK line per block. No --debugger needed. Use: emu.py ... --script tools/lua/heap.lua --var AT=4330 [--var LIST=1]
local ffi = require("ffi")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local function u32(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
local function walk(f)
  local first = u32(0x8015B608 + 0x40)
  if first < 0x80000000 then return end
  local b, n, used, free, big, top = first, 0, 0, 0, 0, 0
  repeat
    local sz, inuse = u32(b + 0xC), u32(b + 8)
    if inuse ~= 0 then used = used + sz; top = math.max(top, b + sz) else free = free + sz; big = math.max(big, sz) end
    if LIST then L.log(string.format("BLK f=%d %08X size=%X %s", f, b, sz, inuse ~= 0 and "used" or "free")) end
    b, n = u32(b), n + 1
  until b == first or n > 4000 or b < 0x80000000
  L.log(string.format("HEAP f=%d blocks=%d used=%X free=%X largest_free=%X top_used_end=%08X", f, n, used, free, big, top))
end
L.on_frame(function(f)
  if f == (AT or -1) or (EVERY and f >= (FROM or 0) and f % EVERY == 0) then walk(f) end
end)
