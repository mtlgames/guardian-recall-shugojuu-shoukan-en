-- QA: give guardians other Forms / traits. Each frame from FROM (default 1), every unit (0x8013E650 + i * 0x7C)
-- whose stat record ([unit + 0x44]) has type 0 (守護獣, halfword +0x1E) gets the next value of TYPES (comma list,
-- default 14,2,12,1,19,26: Overlord Shooter Phantom Battle Divine Super), one per distinct record, kept after.
-- Type = index into the table 0x8009BC34 (ring > UNIT Guardian tab "Type", 情報 type row). QA only.
local m = PCSX.getMemPtr()
local function r8(a) return m[a & 0x1FFFFF] end
local function r16(a) return r8(a) + r8(a + 1) * 256 end
local function r32(a) return r16(a) + r16(a + 2) * 65536 end
local types, given, n = {}, {}, 0
for v in tostring(TYPES or "14,2,12,1,19,26"):gmatch("%d+") do types[#types + 1] = tonumber(v) end
L.on_frame(function(f)
  if f < (FROM or 1) then return end
  for i = 0, 63 do
    local p = r32(0x8013E650 + i * 0x7C + 0x44)
    if p >= 0x80000000 and p < 0x80200000 then
      if given[p] == nil and r16(p + 0x1E) == 0 and n < #types then
        n = n + 1; given[p] = types[n]
        L.log(string.format("unit %d record %08X type -> %d", i, p, types[n]))
      end
      if given[p] then m[(p + 0x1E) & 0x1FFFFF] = given[p]; m[(p + 0x1F) & 0x1FFFFF] = 0 end
    end
  end
end)
