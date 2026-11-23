-- Set registers when an address executes (needs emu.py --debugger):
--   --var "HOOKS='0xADDR:reg=val,reg=val;0xADDR2:reg=val'" [--var TIMES=1] [--var FROM=frame]
-- TIMES = hits per address (default 1); overlays share one base, so use FROM for overlay addresses.
-- Uses (docs/windows.md): Ap-cost "Restore" popup = tac_power_cost + '0x80033854:s4=0,s3=2' (Luck sent down the
-- restore path); "Obtained '%s'" = tac_item + poke 0x80157FAB=0x1:1 + '0x80060194:s3=59;0x800603B0:s0=30' (item
-- use -> gift case 0x3B, item 30 = Scarlet Wing Necklace).
local frame = 0
L.on_frame(function(n) frame = n end)
for addr, regs in tostring(HOOKS):gmatch("(0x%x+):([^;]+)") do
  local left = TIMES or 1
  L.on_exec(tonumber(addr), function()
    if left <= 0 or frame < (FROM or 0) then return end
    if left == (TIMES or 1) then L.log("setreg " .. addr .. " " .. regs .. " at " .. frame) end
    left = left - 1
    local r = PCSX.getRegisters().GPR.n
    for k, v in regs:gmatch("(%w+)=(%w+)") do r[k] = tonumber(v) end
  end)
end
