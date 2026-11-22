-- Log CPU stores of VALUE into [LO, HI] (who clobbers a stack slot or pointer). Needs emu.py --debugger.
-- Decodes the store at pc to read the stored register. Use: --script tools/lua/write_val.lua
--   --var LO=0x801FFF80 --var HI=0x801FFFFF --var VALUE=0x8013DE00 [--var FROM=3400] [--var MAXHITS=10]
local frame, n = 0, 0
L.on_frame(function(f) frame = f end)
local m = PCSX.getMemPtr()
local function r32(a) a = a % 0x200000; return m[a] + m[a + 1] * 256 + m[a + 2] * 65536 + m[a + 3] * 16777216 end
L.on_write(LO, HI, function(addr)
  if frame < (FROM or 0) or n >= (MAXHITS or 10) then return end
  local r = PCSX.getRegisters()
  local pc = r.pc % 2^32
  local rt = math.floor(r32(pc) / 65536) % 32
  local v = r.GPR.r[rt] % 2^32
  if v == VALUE then
    n = n + 1
    L.log(string.format("WRITE f=%d pc=%08X addr=%08X val=%08X ra=%08X sp=%08X", frame, pc, addr % 2^32, v,
                        r.GPR.n.ra % 2^32, r.GPR.n.sp % 2^32))
  end
end)
