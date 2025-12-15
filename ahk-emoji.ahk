#Requires AutoHotkey v2.0
#SingleInstance Force
; #ErrorStdOut
#Warn All, MsgBox

Persistent
SetWorkingDir A_ScriptDir

SendEmojiKbdShowCommand() {
    try {
        p := Trim(FileRead(".local\emoji-kbd-daemon.port"))
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
        NumPut("UShort", DllCall("Ws2_32\htons", "UShort", Integer(p), "UShort"), a, 2)
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
            msgBox("Emoji Kbd window not showing.")
            return false
        }
    } catch {
        return false
    }
}

; Setup tray menu
TraySetIcon("emoji-kbd.ico")
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
    activeWindow := WinGetID("A")

    if not SendEmojiKbdShowCommand() {
        Run('.\venv\Scripts\python.exe guidmn.py SHOW', , "Hide")
        if not WinWait("Emoji Kbd ahk_class Qt6101QWindowToolSaveBits", , 5) {
            MsgBox("Cannot start Emoji Kbd Daemon")
            return
        }
    }

    if WinExist("Emoji Kbd ahk_class Qt6101QWindowToolSaveBits") {
        WinWaitClose("Emoji Kbd ahk_class Qt6101QWindowToolSaveBits")
    }

    if (A_Clipboard != "") {
        if (activeWindow and WinExist("ahk_id " . activeWindow)) {
            WinActivate("ahk_id " . activeWindow)
            if WinWaitActive("ahk_id " . activeWindow, , 2) {
                ; Send Shift-Insert to paste clipboard contents
                Send("+{Insert}")
            }
        }
    }
}

; Win-Dot: Show emoji keyboard and insert clipboard contents
#.:: ActShow()
; Change binding above to use different hotkey if desired
