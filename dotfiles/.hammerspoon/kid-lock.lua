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

-- --- Trackpad gestures ---
--
-- Multitouch gestures are recognized by the driver and handled by Dock, below
-- where a session-level event tap sits, so the blocker cannot suppress them --
-- turning them off in the trackpad prefs is the only thing that does. These are
-- global system settings, so the previous values are snapshotted into
-- hs.settings before being zeroed: that snapshot is what restores them if
-- Hammerspoon exits while locked, and its presence also marks "gestures are
-- currently disabled by us", which keeps a fast lock/unlock/lock from
-- snapshotting the zeros we just wrote.

local GESTURE_SETTINGS_KEY = "kidLock.savedGestures"

local TRACKPAD_GESTURE_DOMAINS = {
  "com.apple.AppleMultitouchTrackpad",
  "com.apple.driver.AppleBluetoothMultitouch.trackpad",
}

-- These pick which gesture a finger count performs rather than switching it on
-- and off (2 = three fingers, 1 = four fingers, 0 = none).
local TRACKPAD_GESTURE_KEYS = {
  "TrackpadThreeFingerVertSwipeGesture",   -- Mission Control / App Expose
  "TrackpadThreeFingerHorizSwipeGesture",  -- switch spaces
  "TrackpadFourFingerVertSwipeGesture",
  "TrackpadFourFingerHorizSwipeGesture",
  "TrackpadFourFingerPinchGesture",        -- Launchpad
  "TrackpadFiveFingerPinchGesture",        -- Show Desktop
  "TrackpadTwoFingerFromRightEdgeSwipeGesture", -- Notification Centre
}

-- Zeroing the trackpad keys above only unchecks the boxes in System Settings;
-- the Dock goes on honouring these gestures until its own switches go false,
-- which is why they survived an otherwise complete lock. Unlike the trackpad
-- keys they are booleans, and stay live if written as ints -- hence `kind` on
-- every pref. Names are the Dock binary's own: `strings Dock.app/Contents/
-- MacOS/Dock | grep GestureEnabled` lists them as setShow*GestureEnabledPref:.
local DOCK_GESTURE_KEYS = {
  "showMissionControlGestureEnabled",  -- three-finger swipe up
  "showAppExposeGestureEnabled",       -- three-finger swipe down
  "showDesktopGestureEnabled",         -- five-finger spread
  "showLaunchpadGestureEnabled",       -- four-finger pinch
}

local GESTURE_PREFS = {}

for _, key in ipairs(DOCK_GESTURE_KEYS) do
  GESTURE_PREFS[#GESTURE_PREFS+1] = {domain = "com.apple.dock", key = key, kind = "bool"}
end

for _, domain in ipairs(TRACKPAD_GESTURE_DOMAINS) do
  for _, key in ipairs(TRACKPAD_GESTURE_KEYS) do
    GESTURE_PREFS[#GESTURE_PREFS+1] = {domain = domain, key = key, kind = "int"}
  end
end

local function readGestures()
  local reads = {}
  for _, pref in ipairs(GESTURE_PREFS) do
    -- `|| echo` keeps one output line per pref even when the key is unset,
    -- so the reply lines stay aligned with GESTURE_PREFS by index.
    reads[#reads+1] = string.format("defaults read %s %s 2>/dev/null || echo", pref.domain, pref.key)
  end

  local saved, i = {}, 1
  for line in (hs.execute(table.concat(reads, "; ")) or ""):gmatch("([^\n]*)\n") do
    local pref = GESTURE_PREFS[i]
    if pref then
      saved[pref.domain] = saved[pref.domain] or {}
      -- booleans read back as 0/1, so one numeric snapshot covers both kinds.
      saved[pref.domain][pref.key] = tonumber(line)
    end
    i = i + 1
  end
  return saved
end

local function writeArg(pref, value)
  if pref.kind == "bool" then
    return "-bool " .. (value ~= 0 and "true" or "false")
  end
  return string.format("-int %d", value)
end

-- saved = nil turns every gesture off; otherwise each key goes back to its
-- snapshotted value, or is deleted if it had none.
local function writeGestures(saved)
  local cmds = {}
  for _, pref in ipairs(GESTURE_PREFS) do
    local value = saved and saved[pref.domain] and saved[pref.domain][pref.key]
    if saved and not value then
      cmds[#cmds+1] = string.format("defaults delete %s %s 2>/dev/null", pref.domain, pref.key)
    else
      cmds[#cmds+1] = string.format("defaults write %s %s %s",
                                    pref.domain, pref.key, writeArg(pref, value or 0))
    end
  end
  cmds[#cmds+1] = "killall Dock 2>/dev/null" -- Dock re-reads the gesture prefs on launch
  hs.execute(table.concat(cmds, "; "))
end

local function disableGestures()
  if not locked then return end
  if hs.settings.get(GESTURE_SETTINGS_KEY) then return end -- already ours
  hs.settings.set(GESTURE_SETTINGS_KEY, readGestures())
  hs.printf("kid-lock: disabling %d gesture prefs (trackpad + Dock); restarting Dock",
            #GESTURE_PREFS)
  writeGestures(nil)
end

local function restoreGestures()
  if locked then return end
  local saved = hs.settings.get(GESTURE_SETTINGS_KEY)
  if not saved then return end
  hs.printf("kid-lock: restoring trackpad gestures; restarting Dock")
  writeGestures(saved)
  hs.settings.clear(GESTURE_SETTINGS_KEY)
end

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

-- Event taps
--
-- The cursor keeps gliding while locked: WindowServer draws the sprite from HID
-- input, below a session-level tap, so deleting motion events hides them from
-- apps without freezing the pointer. That's the intent -- the pointer moves,
-- nothing under it reacts.
local blocker = hs.eventtap.new(blockedEventTypes, function(e)
  if isUnlockEvent(e) then return false end
  if locked and e:getType() == hs.eventtap.event.types.keyDown then
    if ALLOWLIST_KEYCODES[e:getKeyCode()] then return false end
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
end

-- Core lock/unlock
function setLocked(on)
  if on and not locked then
    locked = true
    blocker:start()
    unlockTap:start()
    mediaTap:start()
    stopTimers()
    lockDeadline = os.time() + (AUTO_UNLOCK_MINUTES * 60)
    autoTimer = hs.timer.doAfter(AUTO_UNLOCK_MINUTES * 60, function() setLocked(false) end)
    tickTimer = hs.timer.doEvery(1, refreshCountdown) -- update mm:ss every second
    setMenuLocked(true)
    if alertId then hs.alert.closeSpecific(alertId) end
    alertId = hs.alert.show("Input Locked", 1.0)
    playSound(LOCK_SOUND_NAME)
    -- Deferred: the defaults writes and the Dock restart block for a moment,
    -- and the lock should feel immediate.
    hs.timer.doAfter(0.1, disableGestures)
  elseif (not on) and locked then
    locked = false
    blocker:stop()
    unlockTap:stop()
    mediaTap:stop()
    stopTimers()
    lockDeadline = nil
    setMenuLocked(false)
    if alertId then hs.alert.closeSpecific(alertId); alertId = nil end
    hs.alert.show("Input Unlocked", 1.0)
    playSound(UNLOCK_SOUND_NAME)
    hs.timer.doAfter(0.1, restoreGestures)
  end
end

-- Menu bar toggle
if menu then
  menu:setClickCallback(function() setLocked(not locked) end)
  setMenuLocked(false)
end

-- Global hotkey toggle
hs.hotkey.bind(UNLOCK_MODS, UNLOCK_KEY, function() setLocked(not locked) end)

-- A snapshot surviving into a fresh load means the last session was locked when
-- it exited or reloaded. Its taps died with it, so the machine is unlocked and
-- the gestures should come back.
restoreGestures()
