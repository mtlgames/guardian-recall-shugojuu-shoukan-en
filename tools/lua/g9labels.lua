-- G9 battle trait/skill labels (needs emu.py --debugger): from frame FROM, every EVERY frames (default 150) make a
-- label watcher fire (0x8016D734 v0 = 1) and give the new label object record index START, START+1, ... (wraps at 29).
-- Use: one.py battle_label (scene row) -- --debugger --script tools/lua/g9labels.lua --var FROM=39900
local m = PCSX.getMemPtr()
local frame, nextf, idx = 0, FROM or 0, START or 0
L.on_frame(function(n) frame = n end)
L.on_exec(0x8016D734, function()
  if frame < nextf then return end
  nextf = frame + (EVERY or 150)
  PCSX.getRegisters().GPR.n.v0 = 1
end)
-- 0x8016AE68 lw a0, 0xc(s0): the label init reads its record index; overwrite it first
L.on_exec(0x8016AE68, function()
  local s0 = PCSX.getRegisters().GPR.n.s0 & 0x1FFFFF
  m[s0 + 0xC], m[s0 + 0xD], m[s0 + 0xE], m[s0 + 0xF] = idx, 0, 0, 0
  L.log(string.format("label record %d at %d", idx, frame))
  idx = (idx + 1) % 29
end)
