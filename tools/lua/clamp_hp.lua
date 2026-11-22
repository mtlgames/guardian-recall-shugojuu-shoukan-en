-- Clamp unit HP every frame (second --script beside warp.lua, or alone with --state-in):
--   --var ALLY_HP=1   present allies (USD 0-24) never above 1 HP: the enemy phase wipes the party (game over)
--   --var ENEMY_HP=1  present enemies (USD 25-64) never above 1 HP: any hit wins the map
-- USD array 0x800C3050, stride 0x64: +4 u16 flag (1 = present), +0x10 u16 HP (docs/re/debug.md "Units").
-- Map-side only: BATTLE copies stats in and writes them back, so a unit at 1 HP dies in its next battle.
local m = PCSX.getMemPtr()
local function r16(a) return m[a & 0x1FFFFF] + m[(a + 1) & 0x1FFFFF] * 256 end
local function w16(a, v) m[a & 0x1FFFFF] = v % 256; m[(a + 1) & 0x1FFFFF] = math.floor(v / 256) end
local function clamp(lo, hi, cap)
  for i = lo, hi do
    local u = 0x800C3050 + i * 0x64
    if r16(u + 4) == 1 and r16(u + 0x10) > cap then w16(u + 0x10, cap) end
  end
end
L.on_frame(function()
  if ALLY_HP then clamp(0, 24, ALLY_HP) end
  if ENEMY_HP then clamp(25, 64, ENEMY_HP) end
end)
