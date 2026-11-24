-- Scenario sweep (text coverage): loop the event's first message op over every slot of its scenario block, so
-- each line goes through the real scenario box once (textcover.lua logs it). Needs emu.py --debugger and
-- ADVANCE (warp.lua presses circle to close each box). docs/re/debug.md "Event script interpreter".
-- Op 0x26 (handler 0x8001FE48) = 13 bytes: op, six u16 args; the last = block slot (0x80044F18 a0). It halts the
-- script until the box closes; the dispatcher then reads the next op at 0x8001B44C, where we rewind the PC.
-- Block layout: u32 count, u32 0, count x u32 offset (slot i at +4*i, slots 2..count+1; 0 = unused).
local m = PCSX.getMemPtr()
local function r8(a) return m[a % 0x200000] end
local function r16(a) return r8(a) + r8(a + 1) * 256 end
local function r32(a) return r16(a) + r16(a + 2) * 65536 end
local function w16(a, v) m[a % 0x200000] = v % 256; m[(a + 1) % 0x200000] = math.floor(v / 256) end
local BUF, PCA = 0x800B68F0, 0x800B59AA
local frame, P, slots, k, orig, done = 0, nil, nil, 0, nil, nil
L.on_frame(function(n)
  frame = n
  if done and n - done >= 60 then  -- end the run once the block is through (regen.py wants "final frame")
    done = nil; L.shot("final.png"); L.log("final frame " .. n); L.finish(0)
  end
end)

local function scen_buf()  -- lui/addiu pair at 0x80044F40 (our build moves the buffer: asm/hooks.asm SCEN_BUF)
  local hi, lo = r32(0x80044F40) % 65536, r32(0x80044F44) % 65536
  if lo >= 0x8000 then lo = lo - 0x10000 end
  return hi * 65536 + lo
end

L.on_exec(0x8001FE48, function()
  local pc = r16(PCA)
  if not P then
    if r8(BUF + pc - 1) ~= 0x26 then return end
    P = pc - 1
    orig = r16(BUF + P + 11)
    local b = scen_buf()
    local n, seen = r32(b), {}
    if n == 0 then n = 254 end  -- g23 entry 43: count 0 but 254 slots (docs/re/text.md)
    -- --var "SLOTS='39,58'": sweep just these script/ "slots" numbers (= table index i - 2), to re-cover changed text
    local only = nil
    if SLOTS then only = {}; for s in tostring(SLOTS):gmatch("%d+") do only[tonumber(s) + 2] = true end end
    slots = {}
    for i = 2, n + 1 do
      local o = r32(b + 4 * i)
      if o ~= 0 and o < 0x6A78 and not seen[o] and (not only or only[i]) then seen[o] = true; slots[#slots + 1] = i end
    end
    L.log(string.format("SWEEP start f=%d op@%04X buf=%08X count=%d slots=%d", frame, P, b, n, #slots))
  end
  if pc - 1 ~= P or not slots then return end
  k = k + 1
  if k <= #slots then
    w16(BUF + P + 11, slots[k])
  else
    w16(BUF + P + 11, orig)
    L.log(string.format("SWEEP done f=%d slots=%d", frame, #slots))
    slots = nil
    if not SWEEP_KEEP then done = frame end  -- --var SWEEP_KEEP=1: play on after the sweep
  end
end)

L.on_exec(0x8001B44C, function()  -- next op read: rewind onto the message op while slots remain
  if slots and r16(PCA) == P + 13 then w16(PCA, P) end
end)
