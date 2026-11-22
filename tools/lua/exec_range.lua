-- Log the first executions inside an address range (find where code jumps into data). Needs emu.py --debugger.
-- One exec hook per word: keep W small (<= 0x400).
-- Use: emu.py CUE --debugger --out DIR --script tools/lua/exec_range.lua --var LO=0x8013DC00 --var W=0x200 [--var MAXHITS=8]
local frame, n = 0, 0
L.on_frame(function(f) frame = f end)
for a = LO, LO + W - 4, 4 do
  L.on_exec(a, function()
    n = n + 1
    if n > (MAXHITS or 8) then return end
    local r = PCSX.getRegisters()
    L.log(string.format("XRANGE f=%d pc=%08X ra=%08X sp=%08X v0=%08X a0=%08X s0=%08X", frame, r.pc % 2^32,
                        r.GPR.n.ra % 2^32, r.GPR.n.sp % 2^32, r.GPR.n.v0 % 2^32, r.GPR.n.a0 % 2^32, r.GPR.n.s0 % 2^32))
  end)
end
