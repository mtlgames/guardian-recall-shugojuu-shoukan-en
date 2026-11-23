-- Log game malloc calls (0x8006996C(size) -> v0) from frame FROM: size, caller, result; FAIL lines when v0 = 0.
-- Needs emu.py --debugger. Use: emu.py ... --debugger --script tools/lua/malloc_log.lua --var FROM=4200 [--var MAXHITS=400]
local frame, n, size = 0, 0, 0
L.on_frame(function(f) frame = f end)
L.on_exec(0x8006996C, function()
  size = PCSX.getRegisters().GPR.n.a0 % 2^32
end)
L.on_exec(0x8006998C, function()  -- jr ra: v0 = result, ra = caller
  if frame < (FROM or 0) then return end
  local r = PCSX.getRegisters().GPR.n
  local v0 = r.v0 % 2^32
  n = n + 1
  if v0 == 0 or n <= (MAXHITS or 400) then
    L.log(string.format("%s f=%d size=%X ra=%08X v0=%08X", v0 == 0 and "FAIL" or "MALLOC", frame, size,
                        r.ra % 2^32, v0))
  end
end)
