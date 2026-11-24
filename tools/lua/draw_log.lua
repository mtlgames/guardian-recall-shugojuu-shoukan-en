-- Log each distinct (x, y, string) the generic draw 0x80043A64 is handed (a0 = x, a1 = y, a2 = string): "DRAW x y text".
-- Needs emu.py --debugger. [--var FROM=N] skips earlier frames. ASCII only (English build); other bytes as \xNN.
local ffi = require("ffi")
local bit = require("bit")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local frame, seen = 0, {}
L.on_frame(function(n) frame = n end)
L.on_exec(0x80043A64, function()
  if frame < (FROM or 0) then return end
  local r = PCSX.getRegisters().GPR.n
  local a, s = r.a2 % 2^32, {}
  for i = 0, 63 do
    local b = mem[bit.band(a + i, 0x1FFFFF)]
    if b == 0 then break end
    s[#s + 1] = (b >= 32 and b < 127) and string.char(b) or string.format("\\x%02X", b)
  end
  local key = (r.a0 % 65536) .. " " .. (r.a1 % 65536) .. " " .. table.concat(s)
  if not seen[key] then
    seen[key] = true
    L.log(string.format("DRAW %d %d %s", r.a0 % 65536, r.a1 % 65536, table.concat(s)))
  end
end)
