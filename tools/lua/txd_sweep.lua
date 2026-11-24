-- txd sweep (text coverage): when a txd string (GRETC txd file loaded in RAM) reaches the book sprintf 0x80017E40 (a3),
-- the txd markup renderer 0x800133D4 (a2) or sprintf 0x8006C9E4 (a2/a3), hand it the next still-unshown slot of the same file instead, so each
-- wanted string goes through the real renderer once. Logs "TEXT <fnv32>" itself, like draw_sweep.lua.
-- Needs emu.py --debugger. TXD = path of the list from `tools/txd_sweep.py LOGDIR OUT` (lines `name s:o,..|w,..`).
-- Use: regen.py --only SCENE --cover --lua tools/lua/txd_sweep.lua --var "TXD='C:/../want.txt'" [--var FROM=N]
local ffi = require("ffi")
local bit = require("bit")
local mem = ffi.cast("uint8_t*", PCSX.getMemPtr())
local function u8(a) return mem[bit.band(a, 0x1FFFFF)] end
local function u32(a) return u8(a) + u8(a + 1) * 256 + u8(a + 2) * 65536 + u8(a + 3) * 16777216 end

local files = {}
for line in assert(io.open(tostring(TXD), "r")):lines() do
  local name, so, w = line:match("^(%S+) ([^|]*)|(.*)$")
  if name then
    local f = {name = name, offs = {}, sig = {}, want = {}, k = 0, size = 0}
    for s, o in so:gmatch("(%d+):(%d+)") do
      s, o = tonumber(s), tonumber(o)
      f.offs[#f.offs + 1] = o
      if #f.sig < 3 then f.sig[#f.sig + 1] = {s, o} end
      if o > f.size then f.size = o end
    end
    f.size = f.size + 0x400  -- past the last string start
    for x in w:gmatch("%d+") do f.want[#f.want + 1] = tonumber(x) end
    if #f.want > 0 and #f.sig == 3 then files[#files + 1] = f end
  end
end

local frame, seen, subs = 0, {}, 0
L.on_frame(function(n) frame = n end)

local function sig_ok(f, b)
  for _, x in ipairs(f.sig) do
    if u32(b + 4 * x[1]) ~= x[2] then return false end
  end
  return true
end

local miss = {}  -- p -> frame of a failed lookup (stack buffers repeat every frame; a full scan per call is slow)
local function find(p)
  for _, f in ipairs(files) do
    if f.base and p >= f.base and p < f.base + f.size and sig_ok(f, f.base) then return f end
  end
  if miss[p] and frame - miss[p] < 600 then return end
  miss[p] = frame
  for _, f in ipairs(files) do
    for _, o in ipairs(f.offs) do
      local b = p - o
      if b >= 0x80000000 and sig_ok(f, b) then
        if f.base ~= b then L.log(string.format("TXDSWEEP %s base=%08X f=%d", f.name, b, frame)) end
        f.base = b
        return f
      end
    end
  end
end

local function log_text(a)
  local h = 2166136261
  for i = 0, 4095 do
    local b = u8(a + i)
    if b == 0 then
      if i == 0 then return end
      h = bit.tohex(h)
      if not seen[h] then seen[h] = true; L.log(string.format("TEXT %s f=%d at=%08X txdsweep", h, frame, a)) end
      return
    end
    h = bit.bxor(h, b)
    h = bit.tobit(bit.lshift(h, 24) + h * 403)
  end
end

local SHORT = 24  -- sprintf %s args get only strings up to this length: a long one overflows the label buffer (crash)
local function strlen(a)
  for i = 0, 4095 do if u8(a + i) == 0 then return i end end
  return 4096
end

-- hand reg the next wanted slot whose string is at most `cap` bytes (nil = any): copies into fixed buffers (book
-- sprintf, sprintf %s labels) overflow and crash the game when a longer string goes in
local function sweep(reg, cap)
  if frame < (FROM or 0) then return end
  local r = PCSX.getRegisters().GPR.n
  local p = r[reg] % 2^32
  if p < 0x80000000 or p >= 0x80200000 then return end
  local f = find(p)
  if not f then return end
  if not f.todo then
    f.todo = {}
    for _, s in ipairs(f.want) do
      local off = u32(f.base + 4 * s)
      if off ~= 0 then f.todo[#f.todo + 1] = {a = off, n = strlen(f.base + off)} end
    end
  end
  if cap == "orig" then cap = strlen(p) end
  for i, t in ipairs(f.todo) do
    if not cap or t.n <= cap then
      table.remove(f.todo, i)
      r[reg] = f.base + t.a
      log_text(f.base + t.a)
      subs = subs + 1
      if #f.todo == 0 then L.log(string.format("TXDSWEEP %s done f=%d", f.name, frame)) end
      return
    end
  end
end

L.on_exec(0x80017E40, function() sweep("a3", "orig") end)
-- sprintf(buf, fmt, a2, a3): DAY save-list labels (save.txd slot 4 * (stage + 0x80)) go in as %s args
L.on_exec(0x8006C9E4, function() sweep("a2", SHORT); sweep("a3", SHORT) end)
L.on_exec(0x800133D4, function() sweep("a2") end)
-- overlay 0x12 (title LOAD, card checks): "<a>" expansion of a save.txd message into a 0x410-byte stack buffer
L.on_exec(0x8016A468, function() if u32(0x80166218) == 0x12 then sweep("a1", 0x400) end end)
