-- GPU packet-buffer use per frame: at the buffer swap (0x80045480) log packet ptr (0x801617C0) - current buffer
-- base (gp+0xC3C); the packet area is base+0x211C .. base+0x1699C (docs/re/text.md "Packet buffer"). Needs --debugger.
-- Use: emu.py ... --debugger --script tools/lua/packet_use.lua [--var FROM=4600] [--var EVERY=10]
local ffi = require("ffi")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local function u32(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
local frame, peak, n = 0, 0, 0
L.on_frame(function(f) frame = f end)
L.on_exec(0x80045480, function()
  if frame < (FROM or 0) then return end
  local gp = PCSX.getRegisters().GPR.n.gp % 2^32
  local used = u32(0x801617C0) - u32(gp + 0xC3C)
  n = n + 1
  if used > peak then peak = used; L.log(string.format("PACKET peak f=%d used=0x%X (end 0x1699C)", frame, used)) end
  if n % (EVERY or 60) == 0 then L.log(string.format("PACKET f=%d used=0x%X", frame, used)) end
end)
