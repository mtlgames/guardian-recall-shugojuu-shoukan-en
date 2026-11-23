-- Log who writes a RAM range (pc, ra, regs), first MAXHITS distinct pcs, from frame FROM. Needs emu.py --debugger.
-- Use: emu.py CUE --debugger --out DIR --script tools/lua/write_log.lua --var LO=0x801618B0 --var W=0x40 [--var FROM=4690]
local frame, seen, n = 0, {}, 0
L.on_frame(function(f) frame = f end)
L.on_write(LO, LO + (W or 4) - 1, function(addr)
  if frame < (FROM or 0) then return end
  local r = PCSX.getRegisters()
  local pc = r.pc % 2^32
  if seen[pc] or n >= (MAXHITS or 16) then return end
  seen[pc] = true
  n = n + 1
  L.log(string.format("WRITE f=%d addr=%08X pc=%08X ra=%08X sp=%08X a0=%08X a1=%08X v0=%08X v1=%08X", frame,
                      addr % 2^32, pc, r.GPR.n.ra % 2^32, r.GPR.n.sp % 2^32, r.GPR.n.a0 % 2^32, r.GPR.n.a1 % 2^32,
                      r.GPR.n.v0 % 2^32, r.GPR.n.v1 % 2^32))
end)
