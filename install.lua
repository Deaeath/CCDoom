-- install.lua: installs ColossusCraft's fork of CCDoom
-- (https://github.com/Deaeath/CCDoom) onto this computer, into ./colossusdoom/.
--
-- Get this file onto a CC:Tweaked computer with:
--   wget https://raw.githubusercontent.com/Deaeath/CCDoom/master/install.lua install
-- then run: install
--
-- Downloads are SEQUENTIAL, not parallel -- CCDoom's original pastebin
-- installer fires all ~33 files at once via recursive parallel.waitForAll,
-- which floods raw.githubusercontent.com with a burst of simultaneous
-- connections from the same IP; GitHub's CDN throttles/resets bursts like
-- that, which is what "Failed to download X after 3 attempts" actually
-- means -- it's not a broken URL or a server HTTP-rules block (both were
-- checked: the URL serves fine standalone, computercraft-server.toml has
-- no rule denying github). One file at a time avoids the burst entirely.
--
local BASE = "https://raw.githubusercontent.com/Deaeath/CCDoom/master/"
local DEST = "colossusdoom"

local width = term.getSize()

local FOLDERS = { "models", "images", "levels" }

local FILES = {
    "Doom.lua", "Pine3D-minified.lua", "betterblittle.lua", "blittle",
    "README.md", "LICENSE",
    "models/corpse", "models/doorx", "models/doorz", "models/emerald",
    "models/enemy1", "models/enemy2", "models/wallx", "models/wallxz", "models/wallz",
    "levels/level1", "levels/level2", "levels/level3", "levels/level4",
    "levels/level5", "levels/level6", "levels/level7", "levels/level8", "levels/level9",
    "images/bfire", "images/bgun", "images/bgunf", "images/bheart",
    "images/fire", "images/gun", "images/gunf", "images/heart", "images/logo",
}

local function status(text)
    term.setCursorPos(1, select(2, term.getCursorPos()))
    term.clearLine()
    term.write(text)
end

local function download(relPath, attempt)
    local url = BASE .. relPath
    local handle, err = http.get(url, nil, true) -- binary mode, images aren't text
    if not handle then
        if attempt >= 3 then
            error(("Giving up on %s after 3 attempts: %s"):format(relPath, err or "unknown error"))
        end
        status(("Retry %d/3: %s (%s)"):format(attempt + 1, relPath, err or "?"))
        sleep(0.5)
        return download(relPath, attempt + 1)
    end
    local data = handle.readAll()
    handle.close()
    local file = fs.open(fs.combine(DEST, relPath), "wb")
    file.write(data)
    file.close()
end

term.clear()
term.setCursorPos(1, 1)
print("ColossusCraft Doom Installer")
print("(fork of CCDoom by Xella, https://github.com/Deaeath/CCDoom)")
print("")

for _, folder in ipairs(FOLDERS) do
    fs.makeDir(fs.combine(DEST, folder))
end

for i, relPath in ipairs(FILES) do
    status(("[%d/%d] %s"):format(i, #FILES, relPath))
    download(relPath, 1)
end

status("Done.")
print("")
print("Installed to /" .. DEST .. "/. Run with: " .. DEST .. "/Doom")
