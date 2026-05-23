-- Claude Code Model Indicator for Hammerspoon
-- Save as ~/.hammerspoon/claude-model.lua

local M = {}

local menubar = nil
local watcher = nil
local settingsPath = os.getenv("HOME") .. "/.claude/settings.json"
-- ^ claude's settings.json may be stored in a variety of places; mine's stored here

-- Model display configuration
local modelConfig = {
    opus = { icon = "🟢", title = "O", tooltip = "Claude Opus 4.5" },
    sonnet = { icon = "🟣", title = "S", tooltip = "Claude Sonnet 4.5" },
    haiku = { icon = "🟠", title = "H", tooltip = "Claude Haiku" },
    default = { icon = "⚪", title = "D", tooltip = "Claude Default" },
    opusplan = { icon = "🔵", title = "OP", tooltip = "Opus Plan + Sonnet" },
}

local function readSettings()
    local file = io.open(settingsPath, "r")
    if not file then
        return nil
    end
    local content = file:read("*a")
    file:close()

    local ok, settings = pcall(hs.json.decode, content)
    if ok and settings then
        return settings
    end
    return nil
end

local function updateMenubar()
    if not menubar then return end

    local settings = readSettings()
    local model = (settings and settings.model) or "default"
    local config = modelConfig[model] or modelConfig.default

    -- Use title (text) - works reliably
    menubar:setTitle(config.title)
    menubar:setTooltip(config.tooltip .. " (" .. model .. ")")

    -- Build menu items for quick switching info
    menubar:setMenu({
        { title = "Current: " .. model, disabled = true },
        { title = "-" },
        { title = "Settings: " .. settingsPath, disabled = true },
    })
end

local function watcherCallback(paths, flagTables)
    updateMenubar()
end

function M.start()
    if menubar then return end

    menubar = hs.menubar.new()
    print('menubar created', menubar)
    updateMenubar()

    -- Watch the settings directory for changes
    local settingsDir = os.getenv("HOME") .. "/.claude"
    watcher = hs.pathwatcher.new(settingsDir, watcherCallback)
    watcher:start()

    print("Claude model indicator started")
end

function M.stop()
    if watcher then
        watcher:stop()
        watcher = nil
    end
    if menubar then
        menubar:delete()
        menubar = nil
    end
    print("Claude model indicator stopped")
end

return M