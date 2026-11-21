-- Dump main RAM to OUT_RAM at frame DUMP_AT (default 10). Use: --script tools/lua/dumpram_at.lua --var "OUT_RAM='C:/x/ram.bin'"
local at = DUMP_AT or 10
L.on_frame(function(n)
  if n == at then L.dump_ram(OUT_RAM); L.log("ram dumped at " .. n) end
end)
