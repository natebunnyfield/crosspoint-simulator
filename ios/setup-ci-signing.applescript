-- setup-ci-signing.applescript — store this Mac's signing identities in the
-- simulator repo's Actions secrets, from Terminal.app.
--
-- Why Terminal and not a plain SSH command: `security export -t identities`
-- reads private keys out of the LOGIN keychain, which only a GUI session under
-- the logged-in user has unlocked. An SSH shell (or a sandboxed agent shell)
-- fails or exports nothing. Handing the command to Terminal.app sidesteps that
-- — the same trick as ios/deploy.applescript, which this mirrors.
--
-- From the phone (Terminus/Blink, or a Shortcuts "Run Script Over SSH" action):
--   ssh <mac> 'osascript ~/src/crosspoint-simulator/ios/setup-ci-signing.applescript'
--
-- Arguments pass through to the wrapper. A KEY=VALUE pair becomes an env var
-- (env vars on the osascript caller's shell are LOST otherwise); anything else
-- is forwarded as a script argument:
--   osascript ios/setup-ci-signing.applescript "--check"
--   osascript ios/setup-ci-signing.applescript "--and-build"
--
-- With no arguments the wrapper runs setup-ci-signing.sh --yes, which exports
-- EVERY code-signing identity in the login keychain as one password-protected
-- PKCS#12 and stores it as IOS_SIGNING_P12_B64 and IOS_SIGNING_P12_PASSWORD.
-- Pass --check first if you want to see the list without changing anything.
--
-- YOU STILL HAVE TO BE AT THE MAC. macOS asks, per private key, whether
-- `security` may export it, and those panels cannot be answered over SSH:
-- click Allow (or Always Allow) for each. Terminal is activated so the prompts
-- come to the front. Firing this from a phone and walking away leaves the
-- export sitting on an unanswered dialog, and the secrets unset.
--
-- Requirements (one-time): allow osascript/sshd-launched processes to control
-- Terminal under Privacy & Security > Automation; gh authenticated on the Mac
-- (`gh auth status`); and the Mac logged in and unlocked. AppleScript returns
-- once Terminal starts the command, not when it finishes.

on run argv
    set wrapperPath to "$HOME/src/crosspoint-simulator/ios/setup-ci-signing-from-repo.sh"

    set envPrefix to ""
    set scriptArgs to ""
    repeat with arg in argv
        set a to arg as text
        if a contains "=" then
            set envPrefix to envPrefix & (quoted form of a) & " "
        else
            set scriptArgs to scriptArgs & " " & (quoted form of a)
        end if
    end repeat

    set scriptCmd to ""
    if envPrefix is not "" then
        set scriptCmd to "env " & envPrefix
    end if
    set scriptCmd to scriptCmd & wrapperPath & scriptArgs

    tell application "Terminal"
        activate
        do script scriptCmd
    end tell
end run
