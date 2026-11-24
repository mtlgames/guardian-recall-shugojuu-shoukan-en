-- Draw sweep (text coverage): whenever the generic draw 0x80043A64 is handed a string that a known pointer table
-- holds (unit types, items, traits, Psi, card labels...), hand it the table's next entry instead, so every entry
-- goes through the screen's real column once. Logs "TEXT <fnv32>" itself (textcover.lua's hook on the same address
-- runs first and sees the original pointer). Needs emu.py --debugger.
-- Use: regen.py --only SCENE --cover --lua tools/lua/draw_sweep.lua --var "SLOTS='<tools/cover_tables.py>'" --var FROM=N
-- SLOTS = groups split by ';', each a ','-list of pointer-slot RAM addresses (hex, no 0x).
-- [--var "VALS='<tools/cover_addrs.py action exe>'"]: groups of string addresses; run VALS overlay groups only in scenes
-- where that overlay is loaded (another overlay at the same addresses would be swapped for junk).
local ffi = require("ffi")
local bit = require("bit")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local function u8(a) return mem[bit.band(a, 0x1FFFFF)] end
local function u32(a) return u8(a) + u8(a + 1) * 256 + u8(a + 2) * 65536 + u8(a + 3) * 16777216 end
local groups = {}
for g in tostring(SLOTS):gmatch("[^;]+") do
  local t = {}
  for a in g:gmatch("%x+") do t[#t + 1] = tonumber(a, 16) end
  groups[#groups + 1] = {slots = t, k = 0}
end
-- VALS = groups of direct string addresses (tools/cover_addrs.py: code-referenced EXE/overlay messages), same format
for g in tostring(VALS or ""):gmatch("[^;]+") do
  local t = {}
  for a in g:gmatch("%x+") do t[#t + 1] = tonumber(a, 16) end
  groups[#groups + 1] = {vals = t, k = 0}
end
local frame, map, built, seen, subs = 0, {}, -1000, {}, 0
L.on_frame(function(n) frame = n end)

-- EVD=<evd_names hex> (work/asm/hooks.sym): the payload's evd unit-name table (u16 offsets from its base, the first
-- = 2 * count) as one more group, so map unit names sweep through the UNIT list name column
local evd = EVD and tonumber(tostring(EVD), 16)
local evd_group
local function rebuild()  -- value -> group; overlay tables change when an overlay loads
  map = {}
  if evd and not evd_group and u8(evd) + u8(evd + 1) > 0 then
    local n, t = (u8(evd) + u8(evd + 1) * 256) / 2, {}
    for i = 0, n - 1 do t[#t + 1] = evd + u8(evd + 2 * i) + u8(evd + 2 * i + 1) * 256 end
    evd_group = {vals = t, k = 0}
    groups[#groups + 1] = evd_group
    L.log(string.format("DRAWSWEEP evd names %d", n))
  end
  for gi, g in ipairs(groups) do
    for _, s in ipairs(g.vals or g.slots) do
      local v = g.vals and s or u32(s)
      if v >= 0x80000000 and v < 0x80200000 then map[v] = gi end
    end
  end
  built = frame
end

local function log_text(a)
  local h = 2166136261
  for i = 0, 255 do
    local b = u8(a + i)
    if b == 0 then
      if i == 0 then return end
      h = bit.tohex(h)
      if not seen[h] then seen[h] = true; L.log(string.format("TEXT %s f=%d at=%08X sweep", h, frame, a)) end
      return
    end
    h = bit.bxor(h, b)
    h = bit.tobit(bit.lshift(h, 24) + h * 403)
  end
end

L.on_exec(0x80043A64, function()
  if frame < (FROM or 0) then return end
  if frame - built >= 30 then rebuild() end
  local r = PCSX.getRegisters().GPR.n
  local gi = map[r.a2 % 2^32]
  if not gi then return end
  local g = groups[gi]
  local list = g.vals or g.slots
  for _ = 1, #list do  -- next slot holding a valid pointer
    g.k = g.k % #list + 1
    local v = g.vals and list[g.k] or u32(list[g.k])
    if v >= 0x80000000 and v < 0x80200000 then
      r.a2 = v; log_text(v); subs = subs + 1
      if subs % 500 == 1 then L.log(string.format("DRAWSWEEP f=%d subs=%d group=%d", frame, subs, gi)) end
      return
    end
  end
end)
