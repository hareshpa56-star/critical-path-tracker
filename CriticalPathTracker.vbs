Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "start_server.bat", 0, False
WScript.Sleep 1500
WshShell.Run "http://localhost:8080", 0, False
