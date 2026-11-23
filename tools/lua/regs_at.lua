-- Log every GPR (and pc) at frame AT, e.g. with dumpram_at.lua at the same frame to walk the stack of a hang.
-- Use: emu.py ... --script tools/lua/regs_at.lua --var AT=4300
local names = {"r0", "at", "v0", "v1", "a0", "a1", "a2", "a3", "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
               "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"}
L.on_frame(function(fr)
  if fr == (AT or 10) then
    local r = PCSX.getRegisters()
    local out = {string.format("REGS f%d pc=%08X", fr, r.pc % 2^32)}
    for i, n in ipairs(names) do
      out[#out + 1] = string.format("%s=%08X", n, r.GPR.r[i - 1] % 2^32)
    end
    L.log(table.concat(out, " "))
  end
end)
