-- Log every frame where a u32 changes. WATCH = "0xADDR,..."; "*0xADDR" reads the u32 the pointer at ADDR points to
-- (ACTION's menu state fn: "*0x800B656C"). Use: emu.py ... --script tools/lua/watch_u32.lua --var "WATCH='*0x800B656C'"
local m = PCSX.getMemPtr()
local function r32(a)
  a = a % 0x200000
  return m[a] + m[a + 1] * 256 + m[a + 2] * 65536 + m[a + 3] * 16777216
end
local list, last = {}, {}
for s in tostring(WATCH):gmatch("[^,]+") do list[#list + 1] = s end
L.on_frame(function(n)
  for _, s in ipairs(list) do
    local p = s:sub(1, 1) == "*"
    local a = tonumber(p and s:sub(2) or s)
    local v = p and r32(r32(a)) or r32(a)
    if v ~= last[s] then L.log(string.format("f=%d %s = %08X", n, s, v)); last[s] = v end
  end
end)
