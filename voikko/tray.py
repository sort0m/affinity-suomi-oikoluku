"""Small native Windows notification icon; no GUI framework or polling timer."""
import ctypes as C
from ctypes import wintypes as W
import os


LRESULT = C.c_ssize_t
WNDPROC = C.WINFUNCTYPE(LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)


class WNDCLASS(C.Structure):
    _fields_ = [('style', W.UINT), ('lpfnWndProc', WNDPROC),
                ('cbClsExtra', C.c_int), ('cbWndExtra', C.c_int),
                ('hInstance', W.HINSTANCE), ('hIcon', W.HICON),
                ('hCursor', W.HANDLE), ('hbrBackground', W.HANDLE),
                ('lpszMenuName', W.LPCWSTR), ('lpszClassName', W.LPCWSTR)]


class NOTIFYICONDATA(C.Structure):
    _fields_ = [('cbSize', W.DWORD), ('hWnd', W.HWND), ('uID', W.UINT),
                ('uFlags', W.UINT), ('uCallbackMessage', W.UINT), ('hIcon', W.HICON),
                ('szTip', W.WCHAR * 128), ('dwState', W.DWORD), ('dwStateMask', W.DWORD),
                ('szInfo', W.WCHAR * 256), ('uVersion', W.UINT),
                ('szInfoTitle', W.WCHAR * 64), ('dwInfoFlags', W.DWORD),
                ('guidItem', C.c_byte * 16), ('hBalloonIcon', W.HICON)]


def signature(dll, name, result, *arguments):
    function = getattr(dll, name)
    function.restype, function.argtypes = result, arguments
    return function


class TrayIcon:
    CALLBACK = 0x8001
    CLOSE = 0x0010
    DESTROY = 0x0002
    OPEN_FOLDER = 1
    EXIT = 2

    def __init__(self, folder, icon_path):
        self.folder = folder
        self.hwnd = None
        self.icon = None
        self.registered = False
        self.error = None
        self.user = C.WinDLL('user32', use_last_error=True)
        self.shell = C.WinDLL('shell32', use_last_error=True)
        kernel = C.WinDLL('kernel32', use_last_error=True)
        self.instance = signature(kernel, 'GetModuleHandleW', W.HMODULE, W.LPCWSTR)(None)
        signature(self.user, 'RegisterClassW', W.WORD, C.POINTER(WNDCLASS))
        signature(self.user, 'UnregisterClassW', W.BOOL, W.LPCWSTR, W.HINSTANCE)
        signature(self.user, 'CreateWindowExW', W.HWND, W.DWORD, W.LPCWSTR, W.LPCWSTR,
                  W.DWORD, C.c_int, C.c_int, C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID)
        signature(self.user, 'DefWindowProcW', LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
        signature(self.user, 'DestroyWindow', W.BOOL, W.HWND)
        signature(self.user, 'PostQuitMessage', None, C.c_int)
        signature(self.user, 'PostMessageW', W.BOOL, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
        signature(self.user, 'GetMessageW', C.c_int, C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT)
        signature(self.user, 'TranslateMessage', W.BOOL, C.POINTER(W.MSG))
        signature(self.user, 'DispatchMessageW', LRESULT, C.POINTER(W.MSG))
        signature(self.user, 'RegisterWindowMessageW', W.UINT, W.LPCWSTR)
        signature(self.user, 'LoadImageW', W.HANDLE, W.HINSTANCE, W.LPCWSTR, W.UINT,
                  C.c_int, C.c_int, W.UINT)
        signature(self.user, 'DestroyIcon', W.BOOL, W.HICON)
        signature(self.user, 'CreatePopupMenu', W.HMENU)
        signature(self.user, 'AppendMenuW', W.BOOL, W.HMENU, W.UINT, C.c_size_t, W.LPCWSTR)
        signature(self.user, 'DestroyMenu', W.BOOL, W.HMENU)
        signature(self.user, 'GetCursorPos', W.BOOL, C.POINTER(W.POINT))
        signature(self.user, 'SetForegroundWindow', W.BOOL, W.HWND)
        signature(self.user, 'TrackPopupMenu', W.UINT, W.HMENU, W.UINT,
                  C.c_int, C.c_int, C.c_int, W.HWND, W.LPVOID)
        signature(self.shell, 'Shell_NotifyIconW', W.BOOL, W.DWORD, C.POINTER(NOTIFYICONDATA))
        self.taskbar_created = self.user.RegisterWindowMessageW('TaskbarCreated')
        self.class_name = f'AffinityVoikkoTray-{os.getpid()}'
        self.callback = WNDPROC(self._window_proc)
        self.window_class = WNDCLASS(lpfnWndProc=self.callback, hInstance=self.instance,
                                     lpszClassName=self.class_name)
        self.data = NOTIFYICONDATA()
        try:
            if not self.user.RegisterClassW(C.byref(self.window_class)):
                raise C.WinError(C.get_last_error())
            self.registered = True
            self.icon = self.user.LoadImageW(None, str(icon_path), 1, 0, 0, 0x10 | 0x40)
            if not self.icon:
                raise C.WinError(C.get_last_error())
            # Hidden top-level window receives Explorer restart broadcasts.
            self.hwnd = self.user.CreateWindowExW(0, self.class_name, 'Affinity-oikoluku', 0,
                                                  0, 0, 0, 0, None, None, self.instance, None)
            if not self.hwnd:
                raise C.WinError(C.get_last_error())
            self.data = NOTIFYICONDATA(cbSize=C.sizeof(NOTIFYICONDATA), hWnd=self.hwnd,
                                       uID=1, uFlags=1 | 2 | 4,
                                       uCallbackMessage=self.CALLBACK, hIcon=self.icon,
                                       szTip='Affinity-oikoluku käynnissä')
            if not self.shell.Shell_NotifyIconW(0, C.byref(self.data)):
                raise RuntimeError('Affinity-oikoluvun ilmaisinalueen kuvaketta ei voitu lisätä.')
        except Exception:
            self.dispose()
            raise

    def _menu(self):
        menu = self.user.CreatePopupMenu()
        if not menu:
            raise C.WinError(C.get_last_error())
        try:
            self.user.AppendMenuW(menu, 1, 0, 'Affinity-oikoluku on käynnissä')
            self.user.AppendMenuW(menu, 0x800, 0, None)
            self.user.AppendMenuW(menu, 0, self.OPEN_FOLDER, 'Avaa skriptikansio')
            self.user.AppendMenuW(menu, 0, self.EXIT, 'Sammuta Affinity-oikoluku')
            point = W.POINT()
            self.user.GetCursorPos(C.byref(point))
            self.user.SetForegroundWindow(self.hwnd)
            command = self.user.TrackPopupMenu(menu, 0x100 | 0x80 | 2,
                                               point.x, point.y, 0, self.hwnd, None)
            self.user.PostMessageW(self.hwnd, 0, 0, 0)
            if command == self.OPEN_FOLDER:
                os.startfile(self.folder)
            elif command == self.EXIT:
                self.user.DestroyWindow(self.hwnd)
        finally:
            self.user.DestroyMenu(menu)

    def _window_proc(self, hwnd, message, wparam, lparam):
        try:
            if message == self.CALLBACK:
                if lparam in (0x202, 0x205, 0x7B):  # Left/right release; context menu.
                    self._menu()
                return 0
            if message == self.taskbar_created:
                self.shell.Shell_NotifyIconW(0, C.byref(self.data))
                return 0
            if message == self.CLOSE:
                self.user.DestroyWindow(hwnd)
                return 0
            if message == self.DESTROY:
                self.shell.Shell_NotifyIconW(2, C.byref(self.data))
                self.hwnd = None
                self.user.PostQuitMessage(0)
                return 0
            return self.user.DefWindowProcW(hwnd, message, wparam, lparam)
        except Exception as error:
            self.error = error
            self.user.DestroyWindow(hwnd)
            return 0

    def run(self):
        message = W.MSG()
        while True:
            result = self.user.GetMessageW(C.byref(message), None, 0, 0)
            if result == 0:
                break
            if result == -1:
                raise C.WinError(C.get_last_error())
            self.user.TranslateMessage(C.byref(message))
            self.user.DispatchMessageW(C.byref(message))
        if self.error:
            raise self.error

    def close(self):
        """Safe from the HTTP worker when stopped via the existing CMD file."""
        if self.hwnd:
            self.user.PostMessageW(self.hwnd, self.CLOSE, 0, 0)

    def dispose(self):
        if self.hwnd:
            self.user.DestroyWindow(self.hwnd)
        if self.icon:
            self.user.DestroyIcon(self.icon)
            self.icon = None
        if self.registered:
            self.user.UnregisterClassW(self.class_name, self.instance)
            self.registered = False
