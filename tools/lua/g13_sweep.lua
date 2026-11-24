-- g13 sweep (text coverage): force UNN g13 entry G13 into the g13 buffer and send every used slot of it through the
-- game's indexed draw 0x80044624(a0 = slot, a1 = x, a2 = y), one slot per call, so textcover.lua logs each string.
-- Needs emu.py --debugger and a scene that calls 0x80044624 every frame (tac_think: 思考 help box).
-- Use: regen.py --only tac_think --cover --lua tools/lua/g13_sweep.lua --var G13=N --var FROM=<frame after warp>
-- Loader 0x80044BB4(a0 = entry) stores the buffer at gp+0xBF8; block = u32 count, u32 0, u32 offsets (slots
-- 2..count+1, 0 = unused), as g23 (docs/re/text.md).
local m = PCSX.getMemPtr()
local function r8(a) return m[a % 0x200000] end
local function r16(a) return r8(a) + r8(a + 1) * 256 end
local function r32(a) return r16(a) + r16(a + 2) * 65536 end
local frame, slots, k, done = 0, nil, 0, nil
L.on_frame(function(n)
  frame = n
  if done and n - done >= 30 then done = nil; L.shot("final.png"); L.log("final frame " .. n); L.finish(0) end
end)

L.on_exec(0x80044BB4, function()
  if frame < (FROM or 0) then return end
  PCSX.getRegisters().GPR.n.a0 = G13
end)

L.on_exec(0x80044624, function()
  if frame < (FROM or 0) or done then return end
  local r = PCSX.getRegisters().GPR.n
  if not slots then
    local b = r32((r.gp % 2^32) + 0xBF8)
    local n, seen = r32(b), {}
    if n == 0 or n > 1000 then return end  -- buffer not loaded yet
    slots = {}
    local first = r32(b + 4) == 0 and 2 or 1  -- entry 2 (item help): `u32 80` then 81 offsets, no 0 word
    for i = first, n + 1 do
      local o = r32(b + 4 * i) % 65536
      if o ~= 0 and not seen[o] then seen[o] = true; slots[#slots + 1] = i end
    end
    L.log(string.format("G13 start f=%d entry=%d buf=%08X count=%d slots=%d", frame, G13, b, n, #slots))
  end
  k = k + 1
  if k <= #slots then r.a0 = slots[k] else L.log(string.format("G13 done f=%d", frame)); done = frame end
end)
