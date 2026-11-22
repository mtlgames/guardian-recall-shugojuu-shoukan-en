-- Log how many bytes are non-zero in the story-state blocks a GRS/GRD load restores (docs/re/debug.md), every
-- EVERY frames (default 300), plus the overlay id and event number. Use beside warp.lua to see what initialises them.
local m = PCSX.getMemPtr()
local BLOCKS = { { 0x80136BD0, 0x26 }, { 0x80141398, 0x3C }, { 0x800C4A20, 0x230 }, { 0x8013E550, 0x100 },
                 { 0x80152258, 0x200 } }
local function nz(a, n) local c = 0; for i = 0, n - 1 do if m[(a + i) & 0x1FFFFF] ~= 0 then c = c + 1 end end; return c end
local function r32(a) a = a & 0x1FFFFF; return m[a] + m[a + 1] * 256 + m[a + 2] * 65536 + m[a + 3] * 16777216 end
L.on_frame(function(n)
  if n % (EVERY or 300) ~= 0 then return end
  local s = {}
  for _, b in ipairs(BLOCKS) do s[#s + 1] = string.format("%X:%d", b[1], nz(b[1], b[2])) end
  L.log(string.format("story %d ovl %X ev %d | %s", n, r32(0x80166218), r32(0x8013CEE4) % 65536, table.concat(s, " ")))
end)
