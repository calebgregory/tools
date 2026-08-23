------------------------------------------------------------------
-- Kid-Lock (keyboard + mouse fully blocked) with countdown, sounds,
-- volume/media key allowance, menu toggle, auto-unlock timer.
--
-- While locked the menubar toggle is unreachable (clicks are eaten),
-- so the UNLOCK_MODS+UNLOCK_KEY hotkey is the only manual way out.
----------------------------------------------------------------

-- === Settings ===
local UNLOCK_MODS = {"ctrl","alt","cmd"}
local UNLOCK_KEY  = "L"
local AUTO_UNLOCK_MINUTES = 45

-- System sounds: try "Submarine", "Glass", "Pop", "Tink", "Funk", "Hero"
local LOCK_SOUND_NAME   = "Funk"
local UNLOCK_SOUND_NAME = "Tink"

-- === State ===
local locked        = false
local alertId       = nil
local autoTimer     = nil     -- one-shot auto-unlock timer
local tickTimer     = nil     -- countdown refresher (every second)
local lockDeadline  = nil     -- os.time() when it should auto-unlock
local pinnedMouse   = nil     -- corner the pointer is held at while locked
local restoreMouse  = nil     -- where the pointer was before locking
local pinTimer      = nil     -- backstop for cursor movement that doesn't reach the tap
local menu          = hs.menubar.new(true)

local EMOJI_LOCKED, EMOJI_UNLOCKED = "👶", "🫵"


-- Blocked events, named rather than inlined: a name this Hammerspoon build
-- doesn't know resolves to nil, and a nil in a table constructor ends the array
-- early -- hs.eventtap.new would then register only the types before the hole
-- and silently ignore the rest.
local BLOCKED_EVENT_NAMES = {
  "keyDown",
  "keyUp",
  -- "flagsChanged",

  "mouseMoved",

  "leftMouseDown",
  "leftMouseUp",
  "rightMouseDown",
  "rightMouseUp",
  "otherMouseDown",
  "otherMouseUp",

  "leftMouseDragged",
  "rightMouseDragged",
  "otherMouseDragged",

  "scrollWheel",
  -- magnify/rotate/swipe/pressure/directTouch are sub-types of gesture
  -- (hs.eventtap.event:getType(true)), not tappable types of their own --
  -- tapping "gesture" is what actually catches them.
  "gesture",
}

local function toEventTypes(names)
  local types, unknown = {}, {}
  for _, name in ipairs(names) do
    local t = hs.eventtap.event.types[name]
    if t then types[#types+1] = t else unknown[#unknown+1] = name end
  end
  if #unknown > 0 then
    hs.printf("kid-lock: ignoring unknown event types: %s", table.concat(unknown, ", "))
  end
  return types
end

local blockedEventTypes = toEventTypes(BLOCKED_EVENT_NAMES)

-- Some keyboards send F-keys for media; whitelist those when locked.
local ALLOWLIST_KEYCODES = {
  [hs.keycodes.map["f10"]] = true, -- mute
  [hs.keycodes.map["f11"]] = true, -- vol down
  [hs.keycodes.map["f12"]] = true, -- vol up
}

-- Also let system-defined media keys through (volume/brightness/play, etc.)
local mediaTap = hs.eventtap.new({hs.eventtap.event.types.systemDefined}, function(_)
  return false -- don't consume; allow system to handle
end)

-- --- Helpers ---

-- Build a normalized key for a list of modifier names
local function listKey(t)
  local copy = {table.unpack(t)}
  table.sort(copy)
  return table.concat(copy, "+")
end

-- Build a normalized key from hs event flags (only the ones that are true)
local function flagsKey(flags)
  local t = {}
  for k,v in pairs(flags) do if v then t[#t+1] = k end end
  table.sort(t)
  return table.concat(t, "+")
end

-- Precompute the target modifiers once
local UNLOCK_MODS_KEY = listKey(UNLOCK_MODS)

local function isUnlockEvent(e)
  return e:getType() == hs.eventtap.event.types.keyDown
     and flagsKey(e:getFlags()) == UNLOCK_MODS_KEY
     and hs.keycodes.map[UNLOCK_KEY:lower()] == e:getKeyCode()
end

local function playSound(name)
  if not name or name == "" then return end
  local snd = hs.sound.getByName(name)
  if snd then snd:play() end
end

local function fmtTimer(secs)
  secs = math.max(0, math.floor(secs))
  local m = math.floor(secs / 60)
  if m >= 1 then
    return string.format("%02dm", m)
  end
  local s = secs % 60
  return string.format("%02ds", s)
end

local function remainingSeconds()
  if not lockDeadline then return 0 end
  return math.max(0, lockDeadline - os.time())
end

local function setMenuLocked(isLocked)
  if not menu then return end
  if isLocked then
    local ttl = fmtTimer(remainingSeconds())
    menu:setTitle(EMOJI_LOCKED .. " " .. ttl)
    menu:setTooltip("Input Locked — " .. ttl .. " remaining (click to unlock)")
  else
    menu:setTitle(EMOJI_UNLOCKED)
    menu:setTooltip("Input Unlocked (click to lock)")
  end
end

local function refreshCountdown()
  if not locked then return end
  local secs = remainingSeconds()
  setMenuLocked(true)
  if secs <= 0 then
    -- Safety: in case doAfter didn’t fire yet, unlock here
    hs.timer.doAfter(0.01, function() setLocked(false) end)
  end
end

-- WindowServer draws the cursor from HID input, below a session-level event tap,
-- so deleting motion events only hides them from apps -- the pointer still glides.
-- Warping it back is what actually freezes it, and that requires letting motion
-- events through (see the blocker): absolutePosition() reads the event system's
-- location, which stops advancing if the motion events are deleted, leaving this
-- comparison always false and the cursor free to wander.
local function pinMouse()
  if not pinnedMouse then return end
  local p = hs.mouse.absolutePosition()
  if p.x ~= pinnedMouse.x or p.y ~= pinnedMouse.y then
    hs.mouse.absolutePosition(pinnedMouse)
  end
end

-- Parking the pointer in a corner means physical movement can only push it
-- inward, where the warp pulls it straight back -- the residual twitch stays
-- tucked out of the way instead of jittering mid-screen.
local function cornerPin()
  local frame = (hs.mouse.getCurrentScreen() or hs.screen.mainScreen()):fullFrame()
  return { x = frame.x + frame.w - 12, y = 11 }
end

local MOVE_EVENT_TYPES = {
  [hs.eventtap.event.types.mouseMoved]         = true,
  [hs.eventtap.event.types.leftMouseDragged]   = true,
  [hs.eventtap.event.types.rightMouseDragged]  = true,
  [hs.eventtap.event.types.otherMouseDragged]  = true,
}

-- Event taps
local blocker = hs.eventtap.new(blockedEventTypes, function(e)
  if isUnlockEvent(e) then return false end
  if locked and e:getType() == hs.eventtap.event.types.keyDown then
    if ALLOWLIST_KEYCODES[e:getKeyCode()] then return false end
  end
  if locked and MOVE_EVENT_TYPES[e:getType()] then
    pinMouse()
    return false -- propagate, so the event system's mouse location keeps tracking
  end
  return true
end)

local unlockTap = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(e)
  if locked and isUnlockEvent(e) then
    setLocked(false)
    return true  -- consume the key so it doesn't type "l" anywhere
  end
  return false
end)

-- Timer management
local function stopTimers()
  if autoTimer then autoTimer:stop(); autoTimer = nil end
  if tickTimer then tickTimer:stop(); tickTimer = nil end
  if pinTimer  then pinTimer:stop();  pinTimer  = nil end
end

-- Core lock/unlock
function setLocked(on)
  if on and not locked then
    locked = true
    blocker:start()
    unlockTap:start()
    mediaTap:start()
    stopTimers()
    restoreMouse = hs.mouse.absolutePosition()
    pinnedMouse = cornerPin()
    hs.mouse.absolutePosition(pinnedMouse)
    lockDeadline = os.time() + (AUTO_UNLOCK_MINUTES * 60)
    autoTimer = hs.timer.doAfter(AUTO_UNLOCK_MINUTES * 60, function() setLocked(false) end)
    tickTimer = hs.timer.doEvery(1, refreshCountdown) -- update mm:ss every second
    pinTimer  = hs.timer.doEvery(0.005, pinMouse)
    setMenuLocked(true)
    if alertId then hs.alert.closeSpecific(alertId) end
    alertId = hs.alert.show("Input Locked", 1.0)
    playSound(LOCK_SOUND_NAME)
  elseif (not on) and locked then
    locked = false
    blocker:stop()
    unlockTap:stop()
    mediaTap:stop()
    stopTimers()
    lockDeadline = nil
    pinnedMouse = nil
    if restoreMouse then
      hs.mouse.absolutePosition(restoreMouse)
      restoreMouse = nil
    end
    setMenuLocked(false)
    if alertId then hs.alert.closeSpecific(alertId); alertId = nil end
    hs.alert.show("Input Unlocked", 1.0)
    playSound(UNLOCK_SOUND_NAME)
  end
end

-- Menu bar toggle
if menu then
  menu:setClickCallback(function() setLocked(not locked) end)
  setMenuLocked(false)
end

-- Global hotkey toggle
hs.hotkey.bind(UNLOCK_MODS, UNLOCK_KEY, function() setLocked(not locked) end)
