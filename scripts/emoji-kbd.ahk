#Requires AutoHotkey v2.0
#SingleInstance Force
#ErrorStdOut
#Warn All, MsgBox

Persistent
SetWorkingDir A_ScriptDir . "\.."

if EnvGet("EMOJI_KBD_DEV") {
    state_dir := A_ScriptDir . ".local\"
    log_file := "*"
}
else {
    state_dir := EnvGet("USERPROFILE") . "\.local\state\emoji-kbd\"
    log_file := state_dir . "emoji-kbd.log"
}

if !DirExist(state_dir) {
    DirCreate(state_dir)
}

Log_Info(msg) {
    FileAppend(FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss") . " " . msg . "`n", log_file)
}

Log_Info("Starting emoji-kbd.ahk")

SendEmojiKbdShowCommand() {
    try {
        port_file := state_dir . "emoji-kbd-daemon.port"
        if !FileExist(port_file) {
            MsgBox("Port file '" . port_file . "' not found.", "Error", "Icon!")
            return false
        }
        Log_Info("Port file: " . port_file)
        port := Trim(FileRead(port_file))
        Log_Info("Port: " . port)
        wsaData := Buffer(400, 0)  ; Proper WSAData buffer size
        if (DllCall("Ws2_32\WSAStartup", "UShort", 0x202, "Ptr", wsaData) != 0) {
            return false
        }
        s := DllCall("Ws2_32\socket", "Int", 2, "Int", 1, "Int", 6, "Ptr")
        if (s = -1 or s = 0) {
            DllCall("Ws2_32\WSACleanup")
            return false
        }
        a := Buffer(16, 0)
        NumPut("UShort", 2, a)
        NumPut("UShort", DllCall("Ws2_32\htons", "UShort", Integer(port), "UShort"), a, 2)
        NumPut("UInt", DllCall("Ws2_32\inet_addr", "AStr", "127.0.0.1", "UInt"), a, 4)
        if (DllCall("Ws2_32\connect", "Ptr", s, "Ptr", a, "Int", 16, "Int") != 0) {
            DllCall("Ws2_32\closesocket", "Ptr", s)
            DllCall("Ws2_32\WSACleanup")
            return false
        }
        msg := "SHOW`n"
        if (DllCall("Ws2_32\send", "Ptr", s, "AStr", msg, "Int", StrLen(msg), "Int", 0, "Int") = -1) {
            DllCall("Ws2_32\closesocket", "Ptr", s)
            DllCall("Ws2_32\WSACleanup")
            return false
        }
        DllCall("Ws2_32\closesocket", "Ptr", s)
        DllCall("Ws2_32\WSACleanup")
        if WinWait("Emoji Kbd ahk_class Qt6101QWindowToolSaveBits", , 1) {
            return true
        }
        else {
            Log_Info("Emoji Kbd window not showing.")
            return false
        }
    } catch as err {
        Log_Info("Error: SendEmojiKbdShowCommand " . A_LastError . "`n" . err.Message . "`n" . err.Stack)
        return false
    }
}

; Setup tray menu
TraySetIcon("res/emoji-kbd.ico")
A_IconTip := "Emoji Kbd"
A_TrayMenu.Delete()
A_TrayMenu.Add("&Show", ActShow)
A_TrayMenu.Add()
A_TrayMenu.Add("Emoji &Kbd by RWF", ActCredits)
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
    try {
        activeWindow := WinGetID("A")
    } catch TargetError {
        activeWindow := 0
    }

    if not SendEmojiKbdShowCommand() {
        Run('.\.venv\Scripts\python.exe src/guidmn.py SHOW', , "Hide")
        
        if not WinWait("Emoji Kbd ahk_class Qt6101QWindowToolSaveBits", , 11) {
            MsgBox("Cannot start Emoji Kbd Daemon. Check '" . log_file . "'.", "Error", "Icon!")
            return
        }
    }

    if WinExist("Emoji Kbd ahk_class Qt6101QWindowToolSaveBits") {
        WinWaitClose("Emoji Kbd ahk_class Qt6101QWindowToolSaveBits")
        if (A_Clipboard != "") {
            if (activeWindow and WinExist("ahk_id " . activeWindow)) {
                WinActivate("ahk_id " . activeWindow)
                WinWaitActive("ahk_id " . activeWindow, , 2)
            }
            else {
                MouseGetPos(, , &windowUnderMouse)
                if windowUnderMouse
                    WinActivate("ahk_id " . windowUnderMouse)
            }
            if WinExist("A") {
                ; Send Shift-Insert to paste clipboard contents
                Send("+{Insert}")
                ; Change binding above to use different paste key sequence
            }
        }
    }
}

; Win-Dot: Show Emoji Kbd and insert clipboard contents
#.:: ActShow()
; Change binding above to use different hotkey
