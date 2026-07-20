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
-- File list is fetched from GitHub's API at install time instead of being
-- hardcoded here -- a manually-maintained list has gone stale and caused a
-- real install failure three separate times as assets were added/removed
-- (missing enemy sprites, missing status bar, a 404 on deleted fire/bfire
-- aborting the whole install). This makes that whole bug class structurally
-- impossible: the list is always exactly what's actually in the repo.
local REPO = "Deaeath/CCDoom"
local BASE = "https://raw.githubusercontent.com/" .. REPO .. "/master/"
local API = "https://api.github.com/repos/" .. REPO .. "/contents/"
local DEST = "colossusdoom"
local TOP_LEVEL_FILES = { "Doom.lua", "Pine3D-minified.lua", "betterblittle.lua", "blittle", "README.md", "LICENSE" }
local FOLDERS = { "models", "images", "levels" }

local function status(text)
    term.setCursorPos(1, select(2, term.getCursorPos()))
    term.clearLine()
    term.write(text)
end

local function listRemoteFolder(folder)
    local handle, err = http.get(API .. folder .. "?cb=" .. os.epoch("utc"))
    if not handle then
        error(("Couldn't list %s/ from GitHub: %s"):format(folder, err or "?"))
    end
    local body = handle.readAll()
    handle.close()
    local entries = textutils.unserialiseJSON(body)
    if not entries then
        error("Couldn't parse GitHub API response for " .. folder .. "/")
    end
    local names = {}
    for _, entry in ipairs(entries) do
        if entry.type == "file" then
            names[#names + 1] = folder .. "/" .. entry.name
        end
    end
    return names
end

local function download(relPath, attempt)
    local url = BASE .. relPath .. "?cb=" .. os.epoch("utc") -- bust CDN cache
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

if fs.exists(DEST) then
    print("Removing existing " .. DEST .. "/ ...")
    fs.delete(DEST)
end

for _, folder in ipairs(FOLDERS) do
    fs.makeDir(fs.combine(DEST, folder))
end

print("Fetching current file list from GitHub...")
local FILES = {}
for _, f in ipairs(TOP_LEVEL_FILES) do FILES[#FILES + 1] = f end
for _, folder in ipairs(FOLDERS) do
    for _, relPath in ipairs(listRemoteFolder(folder)) do
        FILES[#FILES + 1] = relPath
    end
end

for i, relPath in ipairs(FILES) do
    status(("[%d/%d] %s"):format(i, #FILES, relPath))
    download(relPath, 1)
end

status("Done.")
print("")
print("Installed to /" .. DEST .. "/. Run with: " .. DEST .. "/Doom")
