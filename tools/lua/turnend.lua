-- TURN END prompt variants (scene tac_turnend, ACTION task fn 0x801768B8): from frame AT (default 1) every frame set
-- the prompt task's guardians-left count (+0x16; the task struct holds its fn at +0, found by a RAM scan) to LEFT
-- (0 = "End the turn?" box with the End Turn / Retreat choice) and the retreat flag 0x80178EF2 to RETREAT
-- (1 = Retreat row; the game sets it for events 5, 8, 9, 13, 16, 19, 21, 22, 25, 27, 32, 33).
local m = PCSX.getMemPtr()
local function r8(a) return m[a & 0x1FFFFF] end
local function w16(a, v) m[a & 0x1FFFFF] = v % 256; m[(a + 1) & 0x1FFFFF] = math.floor(v / 256) end
local task
L.on_frame(function(n)
  if n < (AT or 1) then return end
  if LEFT and not task then
    for a = 0x80010000, 0x801FFFFC, 4 do
      if r8(a) == 0xB8 and r8(a + 1) == 0x68 and r8(a + 2) == 0x17 and r8(a + 3) == 0x80 then task = a end
    end
    L.log(string.format("TURN END task %s", task and string.format("%08X", task) or "not found"))
  end
  if LEFT and task then w16(task + 0x16, LEFT) end
  if RETREAT then w16(0x80178EF2, RETREAT) end
end)
