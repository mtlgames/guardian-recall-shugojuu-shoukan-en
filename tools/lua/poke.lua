-- Apply RAM writes at frame AT (default 1): --var "POKE='0xADDR=0xVAL*N;0xADDR=0xVAL:1'" (same syntax as warp.lua
-- writes: :1/:2/:4 width, default u16, or *N bytes of VAL). For runs from a savestate (--state-in).
local m = PCSX.getMemPtr()
local function w8(a, v) m[a & 0x1FFFFF] = v % 256 end
-- EVERY=1: re-apply on every frame from AT on (hold a state the game would clear).
L.on_frame(function(n)
  if n ~= (AT or 1) and not (EVERY and n > (AT or 1)) then return end
  for a, v, w, c in tostring(POKE):gmatch("(0x%x+)=(0x%x+):?(%d*)%*?(%w*)") do
    a, v = tonumber(a), tonumber(v)
    local len = c ~= "" and tonumber(c) or tonumber(w ~= "" and w or "2")
    for i = 0, len - 1 do w8(a + i, c ~= "" and v or math.floor(v / 256 ^ i)) end
  end
  if n == (AT or 1) then L.log("poke applied at " .. n) end
end)
