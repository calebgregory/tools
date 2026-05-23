---------------------------------------------------------------
-- Pomodoro (🍅 25m / 🥦 5m) with start/pause sounds + paused emoji
-- Hotkeys:
--   ⌃⌥⌘ P        -> start if paused/stopped; pause if running
--   ⌃⌥⌘⇧ P       -> advance to NEXT PHASE, PAUSED (full duration)
-- Menu click toggles start/pause.
---------------------------------------------------------------

-- === Config ===
local PHASES = {
  { name = "Focus", emoji = "🍅", paused_emoji = "🥀", seconds = 25 * 60 },
  { name = "Break", emoji = "🥦", paused_emoji = "🪴", seconds = 5 * 60 },
}

-- Sounds: try "Glass", "Pop", "Tink", "Submarine", "Funk", "Hero"
local START_SOUND_NAME = "Pop"
local PAUSE_SOUND_NAME = "Tink"

-- === State ===
local idx = 1                       -- current phase index (1..#PHASES)
local running = false               -- currently counting?
local remaining = PHASES[1].seconds -- seconds left in current phase
local deadline = nil                -- os.time() when phase ends (if running)
local tick = nil                    -- 1 Hz timer
local menu = hs.menubar.new(true)

-- === Helpers ===
local function fmt(sec)
  sec = math.max(0, math.floor(sec))
  local m = math.floor(sec / 60)
  local s = sec % 60
  return string.format("%d:%02d", m, s)
end

local function playSound(name)
  if not name or name == "" then return end
  local snd = hs.sound.getByName(name)
  if snd then snd:play() end
end

local function setMenu()
  local phase = PHASES[idx]
  local timeText = fmt(remaining)
  if running then
    -- Running: show phase emoji + countdown
    menu:setTitle(string.format("%s %s", phase.emoji, timeText))
    menu:setTooltip(string.format("%s — %s remaining (running). Click to pause.", phase.name, timeText))
  else
    -- Paused/stopped: show paused prefix + phase emoji + remaining
    menu:setTitle(string.format("%s", phase.paused_emoji))
    menu:setTooltip(string.format("%s — %s remaining (paused). Click to start.", phase.name, timeText))
  end
end

local function stopTick()
  if tick then tick:stop(); tick = nil end
end

local function advanceToNextPhasePaused()
  -- Move to next phase and reset to full duration, PAUSED
  idx = (idx % #PHASES) + 1
  remaining = PHASES[idx].seconds
  running = false
  deadline = nil
  stopTick()
  setMenu()
end

local function startTick()
  stopTick()
  tick = hs.timer.doEvery(1, function()
    if not running then return end
    remaining = math.max(0, deadline - os.time())
    setMenu()
    if remaining <= 0 then
      advanceToNextPhasePaused()
      playSound("Glass")
    end
  end)
end

local function startTimer()
  if running then return end
  if remaining <= 0 then remaining = PHASES[idx].seconds end
  running = true
  deadline = os.time() + remaining
  startTick()
  setMenu()
  playSound(START_SOUND_NAME)
end

local function pauseTimer()
  if not running then return end
  running = false
  remaining = math.max(0, deadline - os.time())
  deadline = nil
  stopTick()
  setMenu()
  playSound(PAUSE_SOUND_NAME)
end

local function toggleStartPause()
  if running then pauseTimer() else startTimer() end
end

-- Menu click toggles start/pause
if menu then
  menu:setClickCallback(toggleStartPause)
end

-- Initial paint
setMenu()

-- Hotkeys
hs.hotkey.bind({"ctrl","alt","cmd"}, "P", toggleStartPause)
hs.hotkey.bind({"ctrl","alt","cmd","shift"}, "P", advanceToNextPhasePaused)
