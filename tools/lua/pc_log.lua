-- Hang diagnosis: log pc/ra every EVERY frames from frame FROM, and where the emulator pauses (game exception).
-- Use: emu.py CUE --out DIR --script tools/lua/pc_log.lua --var FROM=3800 --var EVERY=100
local n = 0
PC_LOG_PAUSE = PCSX.Events.createEventListener("ExecutionFlow::Pause", function(ev)
  n = n + 1
  local r = PCSX.getRegisters()
  L.log(string.format("PAUSE %d frame %d pc %08X ra %08X", n, L.frame, r.pc % 2^32, r.GPR.n.ra % 2^32))
  if n < 3 then PCSX.resumeEmulator() end
end)
L.on_frame(function(fr)
  if fr >= (FROM or 0) and fr % (EVERY or 100) == 0 then
    local r = PCSX.getRegisters()
    L.log(string.format("PC f%d pc %08X ra %08X", fr, r.pc % 2^32, r.GPR.n.ra % 2^32))
  end
end)
