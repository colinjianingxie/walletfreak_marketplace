"""Keep the vault key in macOS Keychain, without a separate WalletFreak password."""
import ctypes
import hashlib
import os
import sys


def device_key(root, create=False):
    if sys.platform != 'darwin':
        # Explicit local-device storage on other platforms; never part of exports.
        path = root / 'credentials-device.key'
        if path.is_symlink(): raise ValueError('Refusing a symlink credential key.')
        if not path.exists() and create:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as f: f.write(os.urandom(32))
        if path.stat().st_mode & 0o077: raise ValueError('Credential key must be readable only by your OS user.')
        key = path.read_bytes()
    else:
        security = ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
        service = b'WalletFreak local vault'
        account = hashlib.sha256(str(root.resolve()).encode()).hexdigest().encode()
        length, data = ctypes.c_uint32(), ctypes.c_void_p()
        find = security.SecKeychainFindGenericPassword
        find.argtypes = [ctypes.c_void_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_void_p),ctypes.c_void_p]
        find.restype = ctypes.c_int32
        result = find(None,len(service),service,len(account),account,ctypes.byref(length),ctypes.byref(data),None)
        if result == -25300 and create:
            key = os.urandom(32)
            add = security.SecKeychainAddGenericPassword
            add.argtypes = [ctypes.c_void_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_void_p]
            add.restype = ctypes.c_int32
            result = add(None,len(service),service,len(account),account,len(key),ctypes.c_char_p(key),None)
            if result: raise ValueError('Could not save the vault key in macOS Keychain. Allow access in the system prompt.')
        elif result:
            raise ValueError('Could not access the vault key. Unlock your macOS login Keychain and allow WalletFreak access.')
        else:
            try: key = ctypes.string_at(data,length.value)
            finally:
                security.SecKeychainItemFreeContent.argtypes = [ctypes.c_void_p,ctypes.c_void_p]
                security.SecKeychainItemFreeContent(None,data)
    if len(key) != 32: raise ValueError('Invalid device key; existing sign-ins were retained.')
    return key
