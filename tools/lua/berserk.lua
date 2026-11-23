-- Berserk Alert popup (EXE 0x8002DD70; needs emu.py --debugger): on entry to the unit action fn 0x8002D674 (runs after
-- a unit acts: scene tac_turnend + ADVANCE, ~f5550) set its state 0x800C3038 = 0xB with sub-state +2 = 1, for the
-- first HOLD calls (default 60) and set frame-counter bit 0x10 (the box blinks on it): the fn then draws "Berserk
-- Alert" once (it runs one frame there; shoot with emu.py --shots 5554,5555,5556).
local m = PCSX.getMemPtr()
local function w16(a, v) m[a & 0x1FFFFF] = v % 256; m[(a + 1) & 0x1FFFFF] = math.floor(v / 256) % 256 end
local frame, left = 0, HOLD or 60
L.on_frame(function(n) frame = n end)
L.on_exec(0x8002D674, function()
  if left <= 0 then return end
  if left == (HOLD or 60) then L.log("berserk: forced at " .. frame) end
  w16(0x800C3038, 0xB)
  w16(0x800C303A, 1)
  m[0x800B5E64 & 0x1FFFFF] = m[0x800B5E64 & 0x1FFFFF] | 0x10  -- frame counter: the box shows on bit 4
  left = left - 1
end)
