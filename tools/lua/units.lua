-- Log the USD unit array (0x800C3050, stride 0x64; docs/re/debug.md "Units") every EVERY frames (default 300):
-- index, flag (+4), unit_no (+6), Lv (+0), HP (+0x10), AP (+0x12), MP (+0x14) of each unit with a nonzero flag.
local m = PCSX.getMemPtr()
local function r8(a) return m[a & 0x1FFFFF] end
local function r16(a) return r8(a) + r8(a + 1) * 256 end
L.on_frame(function(n)
  if n % (EVERY or 300) ~= 0 then return end
  local out = {}
  for i = 0, 64 do
    local u = 0x800C3050 + i * 0x64
    if r16(u + 4) ~= 0 then
      out[#out + 1] = string.format("%d:f%d n%d L%d hp%d ap%d mp%d", i, r16(u + 4), r16(u + 6), r8(u),
                                    r16(u + 0x10), r16(u + 0x12), r16(u + 0x14))
    end
  end
  L.log(string.format("units @%d %s", n, table.concat(out, " ")))
end)
