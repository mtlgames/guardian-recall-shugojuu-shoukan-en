-- Tactics-map stall breaker (emulator workaround). After an ally master's retire line, PCSX-Redux can leave
-- u16 0x8013CEEE with bits 0x14 set (normal 0x20; bit 4 halts the event script, docs/re/debug.md), so the map
-- ignores every button. Clearing them resumes the enemy phase. Probably an XA voice end that never arrives.
-- --var STALL=N: frames the bits must stay set before clearing (default 600, longer than any voice line).
local m = PCSX.getMemPtr()
local A = 0x8013CEEE & 0x1FFFFF
local since
L.on_frame(function(n)
  if m[A] & 0x14 == 0x14 then
    since = since or n
    if n - since >= (STALL or 600) then
      m[A] = m[A] & 0xEB; since = nil
      L.log("unstick: cleared 0x8013CEEE bits 0x14 at " .. n)
    end
  else since = nil end
end)
