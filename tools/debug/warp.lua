-- Cold-boot warp to any scene in tools/debug/scenes.tsv (PCSX-Redux, emu.py --script). Notes: docs/re/debug.md.
--   emu.py build/disc1/<cue> --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='ev20'" --frames 4600
--   or --var "EVENT='20'" (any target, see below) [--var "WRITES='0x8013DE46=0x1'"] [--var "WROUTE='6 down;30 -'"].
--   --var ADVANCE=90: press circle every 90 frames once the route is done (ADVANCE_KEY to change the button).
--   --var DEBUG_TICK=1 logs the probe counter, task and overlay every 30 frames.
-- How: the main loop (0x800219F4) calls the u32 task fn at 0x8013CEE0 every frame, in every overlay. The EXE's
-- leftover event-select task 0x8001A3E8 starts an event by writing the event number (u16) to 0x8013CEE4 and the
-- starter fn 0x8001A25C to the task. We do the same once the loop is live, which a cold boot reaches by mashing
-- START: logos -> title (NEW GAME) -> the 天/地 route choice (disc 1) or the first disc-2 event.
local m = PCSX.getMemPtr()
local function r8(a) return m[a & 0x1FFFFF] end
-- plain arithmetic: LuaJIT bit ops are signed 32-bit, so 0x80000000 + x would compare as negative
local function r16(a) return r8(a) + r8(a + 1) * 256 end
local function r32(a) return r16(a) + r16(a + 2) * 65536 end
local function w8(a, v) m[a & 0x1FFFFF] = v % 256 end
local function w16(a, v) w8(a, v); w8(a + 1, math.floor(v / 256)) end
local function w32(a, v) w16(a, v % 65536); w16(a + 2, math.floor(v / 65536)) end
local function poke_code(at, words) for i, c in ipairs(words) do w32(at + 4 * (i - 1), c) end end
WARP = { r8 = r8, r16 = r16, r32 = r32, w8 = w8, w16 = w16, w32 = w32 }

local TASK, EVNO, IDLE, STARTER = 0x8013CEE0, 0x8013CEE4, 0x8001A5A0, 0x8001A25C
local STUB = 0x8000F000            -- RAM zero above the kernel (docs/re/text.md free space)
local PROBE, CNT = STUB + 0x40, 0x8000F0F0
-- PROBE: a task that only bumps the u32 at CNT (lui t0,0x8001; lw t1,-0xF10(t0); nop; addiu t1,1; jr ra; sw)
local PROBE_CODE = { 0x3C088001, 0x8D09F0F0, 0, 0x25290001, 0x03E00008, 0xAD09F0F0 }
-- overlays load whole at 0x80166218 with their u32 id first: TITLE 5, BRAIN 7, JAPAN 0x0C (travel map that opens
-- most events), ACTION 0x0D (field), RSEL 0x0E (route choice), DAY 0x12 (disc check / swap), BATTLE 0x15
local OVL, OVL_ACTION, OVL_JAPAN = 0x80166218, 0x0D, 0x0C

-- scenes.tsv: name, disc, target, writes ("0xADDR=0xVAL[:1|2|4];..."), route ("frames buttons;..."), frames, note.
-- target:  N        start event N (1..70)
--          call:A[:ARG]  call game function A(ARG) once from the main loop (a mode setter: BRAIN = 0x8004C9C0)
--          V>op:HEX  event-script bytes run at the interpreter's PC inside event V (op:23000100000000 = DAY menu)
--          V>T      start field event V first, then T from inside it: anything that goes through the DAY
--                   intermission (disc check) crashes when started from the route-choice screen (its RSEL tasks)
--          idle     no warp: stop on the screen the boot reaches (route choice)
--          ovl:X    no warp: mash START only until overlay X loads, then run the route (ovl:16 = title screen)
--          boot     no warp and no START mashing: the route runs from power-on (title screen, title menus)
local function target(t, s)
  t = tostring(t)
  if t == "boot" or t == "idle" then s[t] = true; s.event = 0; return s end
  local ov = t:match("^ovl:(%x+)$")
  if ov then s.ovl, s.event = tonumber(ov, 16), 0; return s end
  local via, rest = t:match("^(%d+)>(.+)$")
  if via then s.via, t = tonumber(via), rest end
  local op = t:match("^op:(%x+)$")
  if op then s.op, s.event = op, 0; return s end
  local a, g = t:match("^call:(0x%x+):?(%w*)$")  -- ARG: decimal or 0x hex (32-bit)
  if a then s.call, s.arg, s.event = tonumber(a), tonumber(g), 0 else s.event = tonumber(t) end
  return s
end
local scene = target(EVENT or CALL or "idle", { writes = WRITES or "", route = WROUTE or "" })
if SCENE then
  local path = SCENES or (OUT:match("^(.-)/work/") .. "/tools/debug/scenes.tsv")
  local f = assert(io.open(path, "r"), "cannot open " .. path)
  scene = nil
  for line in f:lines() do
    local c = {}
    for col in (line .. "\t"):gmatch("([^\t]*)\t") do c[#c + 1] = col end
    if c[1] == SCENE then scene = target(c[3], { writes = c[4] or "", route = c[5] or "" }) end
  end
  f:close()
  assert(scene, "scene not in scenes.tsv: " .. SCENE)
end

-- writes: "0xADDR=0xVAL[:1|2|4]" (default u16) or "0xADDR=0xVAL*N" (N bytes of VAL), ";"-separated
local function apply_writes(spec)
  for a, v, w, n in spec:gmatch("(0x%x+)=(0x%x+):?(%d*)%*?(%w*)") do
    if n ~= "" then
      for i = 0, tonumber(n) - 1 do w8(tonumber(a) + i, tonumber(v)) end
    else
      local W = ({ ["1"] = w8, ["4"] = w32 })[w] or w16
      W(tonumber(a), tonumber(v))
    end
  end
end
-- "0xADDR<0xVAL": clamp, every frame from the warp on, the u16 at ADDR to at most VAL (unit HP: a master at 1 HP
-- dies in her next battle, while BATTLE's write-back of 0 is left alone)
local clamps = {}
for a, v in scene.writes:gmatch("(0x%x+)<(0x%x+)") do clamps[#clamps + 1] = { tonumber(a), tonumber(v) } end
local function apply_clamps()
  for _, c in ipairs(clamps) do if r16(c[1]) > c[2] then w16(c[1], c[2]) end end
end
-- route steps: "FRAMES BUTTONS"; "stop:X+N" ends the run (final shot, --state-out) N frames after overlay X loads;
-- "stopeq:0xADDR=0xVAL+N" N frames after the u16 at ADDR becomes VAL (having been something else first)
local function queue_route()
  for step in scene.route:gmatch("[^;]+") do
    local fr, keys = step:match("^%s*(%d+)%s+(%S+)")
    if fr then L.press(keys, tonumber(fr)) end
    local so, sn = step:match("^%s*stop:(%x+)%+(%d+)")
    if so then scene.stop_ovl, scene.stop_after = tonumber(so, 16), tonumber(sn) end
    local ma, mv, mn = step:match("^%s*stopeq:(0x%x+)=(0x%x+)%+(%d+)")
    if ma then scene.stop_mem, scene.stop_val, scene.stop_after = tonumber(ma), tonumber(mv), tonumber(mn) end
  end
end
local stop_seen, stop_armed
local function check_stop(o, n)
  if scene.stop_mem and not stop_seen then
    local v = r16(scene.stop_mem)
    if v ~= scene.stop_val then stop_armed = true; return end
    if not stop_armed then return end
    stop_seen = n; L.log(string.format("stop: %08X = %X at %d", scene.stop_mem, v, n))
  end
  if not scene.stop_ovl and not stop_seen then return end
  if not stop_seen and o ~= scene.stop_ovl then return end
  if not stop_seen then stop_seen = n; L.log(string.format("stop overlay %X at %d", o, n)) end
  if n - stop_seen >= scene.stop_after then
    L.shot("final.png"); L.log("final frame " .. n)
    if STATE_OUT then L.save_state(STATE_OUT) end
    L.finish(0)
  end
end
local function start(ev) w16(EVNO, ev); w32(TASK, STARTER) end

-- "live": frames in a row with a PROBE bump in the last 4 (the loop can run below 60 fps)
local last_cnt, last_bump, live, last_ovl = -1, -100, 0, -1
local stage, warped_at = scene.boot and "done" or "boot", nil
if scene.boot then queue_route(); L.log("boot scene: route from power-on") end
L.on_frame(function(n)
  if (stage == "boot" or stage == "hop") and r32(TASK) == IDLE then
    poke_code(PROBE, PROBE_CODE)  -- (re)written each time: the boot clears low RAM
    w32(TASK, PROBE)
  end
  local o = r32(OVL)
  if o ~= last_ovl then L.log(string.format("overlay %X at %d", o, n)); last_ovl = o end
  check_stop(o, n)
  local c = r32(CNT)
  if c ~= last_cnt then last_bump, last_cnt = n, c end
  live = (n - last_bump <= 4) and live + 1 or 0
  if DEBUG_TICK and n % 30 == 0 then
    L.log(string.format("%d cnt %d live %d task %08X ovl %X", n, c, live, r32(TASK), o))
  end
  local ready = r32(TASK) == PROBE and live >= 60 and L.route_done()  -- route_done: no held START reaches the event

  if stage == "boot" and scene.ovl then
    if o == scene.ovl then
      stage = "running"; apply_writes(scene.writes); queue_route()
      L.log(string.format("overlay scene %X reached at %d", o, n))
    elseif n % 40 == 0 then L.press("start", 6) end
  elseif stage == "boot" then
    if ready then
      if scene.idle then
        w32(TASK, IDLE); stage = "running"; queue_route()
        L.log(string.format("idle scene ready at %d", n))
      elseif scene.via then
        start(scene.via); stage, warped_at = "hop", n
        L.log(string.format("warp: via event %d at frame %d", scene.via, n))
      else stage = "ready" end
    elseif n % 40 == 0 then L.press("start", 6) end
  elseif stage == "hop" then
    -- the route-choice loop (RSEL) keeps ticking until the hop event's JAPAN/ACTION overlay takes over
    if ready and (o == OVL_ACTION or o == OVL_JAPAN) then
      stage = "ready"; L.log(string.format("hop event live at %d (overlay %X)", n, o))
    end
  end

  if stage == "ready" then
    apply_writes(scene.writes)
    if scene.op then
      -- inject event-script bytes at the interpreter's PC (u16 at gp+0xC6 into the buffer 0x800B68F0)
      local pc = 0x800B68F0 + r16(PCSX.getRegisters().GPR.n.gp % 2^32 + 0xC6)
      for i = 1, #scene.op, 2 do w8(pc + (i - 1) / 2, tonumber(scene.op:sub(i, i + 1), 16)) end
      w32(TASK, IDLE)
      L.log(string.format("warp: script op %s at %08X, frame %d", scene.op, pc, n))
    elseif scene.call then
      -- stub: task = idle, a0 = arg, then tail-call the target, which returns into the main loop
      local t, g = scene.call, scene.arg or 0
      poke_code(STUB, { 0x3C088014, 0x3C098001, 0x3529A5A0, 0xAD09CEE0,           -- sw IDLE -> 0x8013CEE0
                        0x3C0A0000 + math.floor(t / 65536), 0x354A0000 + t % 65536,  -- t2 = target
                        0x3C040000 + math.floor(g / 65536), 0x34840000 + g % 65536,  -- a0 = arg (lui/ori)
                        0x01400008, 0 })                                             -- jr t2
      w32(TASK, STUB)
      L.log(string.format("warp: call %08X(%d) at frame %d", t, scene.arg or 0, n))
    else
      start(scene.event)
      L.log(string.format("warp: event %d at frame %d", scene.event, n))
    end
    stage, warped_at = "warped", n
    queue_route()
  elseif stage == "warped" and r32(TASK) ~= STARTER and r32(TASK) ~= STUB then
    stage = "running"
    L.log(string.format("%s %d started (task %08X) at %d", scene.call and "call" or "event",
                        scene.call and 0 or r16(EVNO), r32(TASK), n))
  elseif (stage == "running" or stage == "done") and ADVANCE and L.route_done() and n % ADVANCE == 0 then
    L.press(ADVANCE_KEY or "circle", 6)
  end
  if stage == "warped" or stage == "running" then apply_clamps() end
end)
