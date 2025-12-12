#Requires AutoHotkey v2.0
#SingleInstance Force

SetWorkingDir A_ScriptDir

; Win-Dor: Show emoji keyboard and insert clipboard contents
#.::
{
    activeWindow := WinGetID("A")

    Run('.\venv\Scripts\python.exe guidmn.py SHOW', , "Hide")

    WinWait("Emoji Keyboard")

    WinWaitClose("Emoji Keyboard")

    ; Return to original window and paste
    WinActivate("ahk_id " . activeWindow)
    WinWaitActive("ahk_id " . activeWindow, , 2)
    Send("+{Insert}")
}
