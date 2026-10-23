/* Memowrite launcher: starts the bundled engine with the memowrite package.
   Built twice: as memowrite.exe (console) and MemowriteStudio.exe (GUI). */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>
#include <stdlib.h>

#ifndef STUDIO
#define STUDIO 0
#endif

static const wchar_t *skip_argv0(const wchar_t *cmd) {
    if (*cmd == L'"') {
        cmd++;
        while (*cmd && *cmd != L'"') cmd++;
        if (*cmd == L'"') cmd++;
    } else {
        while (*cmd && *cmd != L' ' && *cmd != L'\t') cmd++;
    }
    while (*cmd == L' ' || *cmd == L'\t') cmd++;
    return cmd;
}

static void fail(const wchar_t *msg) {
#if STUDIO
    MessageBoxW(NULL, msg, L"Memowrite", MB_ICONERROR | MB_OK);
#else
    fwprintf(stderr, L"Memowrite: %ls\n", msg);
#endif
}

#if STUDIO
int WINAPI wWinMain(HINSTANCE h, HINSTANCE p, LPWSTR c, int show)
#else
int wmain(void)
#endif
{
    wchar_t dir[MAX_PATH * 2];
    DWORD n = GetModuleFileNameW(NULL, dir, MAX_PATH * 2);
    if (n == 0 || n >= MAX_PATH * 2) { fail(L"Could not find my own folder."); return 1; }
    wchar_t *slash = wcsrchr(dir, L'\\');
    if (slash) *slash = 0;

    wchar_t engine[MAX_PATH * 2 + 64];
    swprintf(engine, sizeof(engine) / sizeof(wchar_t), L"%ls\\runtime\\%ls", dir, STUDIO ? L"pythonw.exe" : L"python.exe");
    if (GetFileAttributesW(engine) == INVALID_FILE_ATTRIBUTES) {
        fail(L"The Memowrite engine is missing. Please run the Memowrite installer again.");
        return 1;
    }
    SetEnvironmentVariableW(L"PYTHONPATH", dir);
    SetEnvironmentVariableW(L"PYTHONNOUSERSITE", L"1");
    SetEnvironmentVariableW(L"PYTHONHOME", NULL);
    SetEnvironmentVariableW(L"MEMOWRITE_HOME", dir);
    {
        wchar_t lib[MAX_PATH * 2 + 64];
        swprintf(lib, sizeof(lib) / sizeof(wchar_t), L"%ls\\runtime\\tcl\\tcl8.6", dir);
        if (GetFileAttributesW(lib) != INVALID_FILE_ATTRIBUTES) SetEnvironmentVariableW(L"TCL_LIBRARY", lib);
        swprintf(lib, sizeof(lib) / sizeof(wchar_t), L"%ls\\runtime\\tcl\\tk8.6", dir);
        if (GetFileAttributesW(lib) != INVALID_FILE_ATTRIBUTES) SetEnvironmentVariableW(L"TK_LIBRARY", lib);
    }

    const wchar_t *rest = skip_argv0(GetCommandLineW());
    size_t len = wcslen(engine) + wcslen(rest) + 128;
    wchar_t *cmdline = (wchar_t *)malloc(len * sizeof(wchar_t));
    if (!cmdline) return 1;
    swprintf(cmdline, len, L"\"%ls\" -X utf8 -m memowrite %ls%ls", engine, STUDIO ? L"studio " : L"", rest);

    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));
    if (!CreateProcessW(engine, cmdline, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        fail(L"Could not start the Memowrite engine.");
        free(cmdline);
        return 1;
    }
    free(cmdline);
#if STUDIO
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return 0;
#else
    SetConsoleCtrlHandler(NULL, TRUE); /* let the engine handle Ctrl+C */
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD code = 0;
    GetExitCodeProcess(pi.hProcess, &code);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return (int)code;
#endif
}
