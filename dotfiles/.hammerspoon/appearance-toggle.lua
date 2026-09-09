-- toggles the system-wide light/dark appearance via System Events.
-- first run prompts for Automation permission (Hammerspoon -> System Events).
local function toggleAppearance()
    local ok, isDark = hs.osascript.applescript([[
        tell application "System Events"
            tell appearance preferences
                set dark mode to not dark mode
                return dark mode
            end tell
        end tell
    ]])
    if ok then
        hs.alert.show(isDark and "Dark mode" or "Light mode")
    else
        hs.alert.show("Failed to toggle appearance")
    end
end

hs.hotkey.bind({"cmd", "ctrl"}, "d", toggleAppearance)
