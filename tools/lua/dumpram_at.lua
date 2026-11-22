-- Dump main RAM to OUT_RAM at frame DUMP_AT (default 10). Use: --script tools/lua/dumpram_at.lua --var "OUT_RAM='C:/x/ram.bin'"
-- DUMP_AT may be a list "10,900,1800": each dump goes to OUT_RAM with "_<frame>" before the extension.
local at = {}
for f in tostring(DUMP_AT or 10):gmatch("%d+") do at[tonumber(f)] = true end
local multi = tostring(DUMP_AT or ""):find(",")
L.on_frame(function(n)
  if at[n] then
    local p = multi and OUT_RAM:gsub("(%.%w+)$", "_" .. n .. "%1") or OUT_RAM
    L.dump_ram(p); L.log("ram dumped at " .. n .. " -> " .. p)
  end
end)
