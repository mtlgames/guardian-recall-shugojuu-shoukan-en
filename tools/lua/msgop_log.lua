-- Log event-script message ops (0x26 at 0x8001FE48, 0x43 at 0x8001FF20) with their script bytes, and the
-- scenario box opener 0x80044F18 (a0 = block slot). Needs emu.py --debugger. docs/re/debug.md "Event script".
local m = PCSX.getMemPtr()
local function r8(a) return m[a & 0x1FFFFF] end
local function r16(a) return r8(a) + r8(a + 1) * 256 end
local BUF, PCA = 0x800B68F0, 0x800B59AA
local frame = 0
L.on_frame(function(n) frame = n end)
local function bytes(at, n)
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = string.format("%02X", r8(at + i)) end
  return table.concat(t)
end
for _, a in ipairs({ 0x8001FE48, 0x8001FF20 }) do
  L.on_exec(a, function()
    local pc = r16(PCA)
    L.log(string.format("OP %08X f=%d pc=%04X bytes=%s", a, frame, pc, bytes(BUF + pc - 1, 16)))
  end)
end
for _, a in ipairs({ 0x80044F18, 0x80044FC4 }) do
  L.on_exec(a, function()
    local r = PCSX.getRegisters().GPR.n
    L.log(string.format("BOX %08X f=%d a0=%d a1=%d ra=%08X", a, frame, r.a0 % 65536, r.a1 % 65536, r.ra % 2^32))
  end)
end
