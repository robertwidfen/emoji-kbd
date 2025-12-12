#Requires AutoHotkey v2.0
#SingleInstance Force

SetWorkingDir A_ScriptDir

; Setup tray menu
TraySetIcon("emoji-kbd.ico")
A_IconTip := "Emoji Keyboard"
A_TrayMenu.Delete()
A_TrayMenu.Add("&Show", ActShow)
A_TrayMenu.Add()
A_TrayMenu.Add("Emoji &Keyboard by RWF", ActCredits)
A_TrayMenu.Add("&Reload", ActReload)
A_TrayMenu.Add()
A_TrayMenu.Add("E&xit", ActExit)
A_TrayMenu.Default := "&Show"

ActReload(*) {
    Reload
}
ActExit(*) {
    ExitApp
}
ActCredits(*) {
    Run("https://github.com/robertwidfen/emoji-kbd")
}
ActShow(*) {
    activeWindow := WinGetID("A")

    Run('.\venv\Scripts\python.exe guidmn.py SHOW', , "Hide")

    WinWait("Emoji Keyboard")

    WinWaitClose("Emoji Keyboard")

    ; Return to original window if it still exists
    if (activeWindow and WinExist("ahk_id " . activeWindow)) {
        WinActivate("ahk_id " . activeWindow)
        WinWaitActive("ahk_id " . activeWindow, , 2)
    }
    Send("+{Insert}")
}

; Win-Dot: Show emoji keyboard and insert clipboard contents
#.:: ActShow()