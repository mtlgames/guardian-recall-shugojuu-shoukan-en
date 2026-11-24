-- Log each execution of the given addresses with frame, ra, a0-a3 (needs emu.py --debugger).
-- Use: emu.py CUE --debugger --out DIR --script tools/lua/exec_log.lua --var "ADDRS='0x8003B1E8,0x8003B8C8'"
--      [--var MAXHITS=50] (per address)
local frame, hits = 0, {}
L.on_frame(function(n) frame = n end)
for a in tostring(ADDRS):gmatch("0x%x+") do
  local addr = tonumber(a)
  hits[addr] = 0
  L.on_exec(addr, function()
    if frame < (FROM or 0) then return end  -- --var FROM=N: only from frame N
    hits[addr] = hits[addr] + 1
    if hits[addr] > (MAXHITS or 50) then return end
    local r = PCSX.getRegisters().GPR.n
    L.log(string.format("EXEC %08X f=%d ra=%08X a0=%08X a1=%08X a2=%08X a3=%08X s0=%08X s1=%08X s2=%08X fp=%08X", addr,
                        frame, r.ra % 2^32, r.a0 % 2^32, r.a1 % 2^32, r.a2 % 2^32, r.a3 % 2^32, r.s0 % 2^32,
                        r.s1 % 2^32, r.s2 % 2^32, PCSX.getRegisters().GPR.r[30] % 2^32))
  end)
end
