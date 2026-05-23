-- hs.hotkey.bind({"ctrl","alt","cmd"}, "f", function()
--   local out, ok = hs.execute([[defaults read -g com.apple.keyboard.fnState 2>/dev/null]], true)
--   local current = ok and (tostring(out):match("1") or tostring(out):lower():match("true")) ~= nil
--
--   local nextVal = not current
--   hs.execute(string.format([[defaults write -g com.apple.keyboard.fnState -bool %s]], nextVal and "true" or "false"), true)
--   hs.execute([[killall cfprefsd >/dev/null 2>&1 || true]], true)
--
--   hs.alert.show(nextVal
--     and "Function keys: F1-F12 (standard)\n(you may need to log out / restart)"
--     or  "Function keys: media/brightness keys\n(you may need to log out / restart)"
--   )
-- end)
-- ^ unfortunately this is really buggy on Sonoma

hs.hotkey.bind({"ctrl","alt","cmd"}, "f", function()
  hs.task.new("/usr/bin/open", nil, { "x-apple.systempreferences:com.apple.Keyboard?FunctionKeys" }):start()
end)
-- so this is the best we can do
