"""Persist Gmail credentials in macOS Keychain without secret command arguments."""
import ctypes,ctypes.util,json,os
from pathlib import Path
SERVICE=b'WELISPEAK SMTP Gmail'
CONFIG=Path(__file__).resolve().parent/'mail_settings.json'

def keychain(password=None):
 s=ctypes.CDLL(ctypes.util.find_library('Security'))
 cf=ctypes.CDLL(ctypes.util.find_library('CoreFoundation'))
 s.SecKeychainFindGenericPassword.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p)]
 s.SecKeychainFindGenericPassword.restype=ctypes.c_int32
 s.SecKeychainAddGenericPassword.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]
 s.SecKeychainAddGenericPassword.restype=ctypes.c_int32
 s.SecKeychainItemModifyAttributesAndData.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p]
 s.SecKeychainItemModifyAttributesAndData.restype=ctypes.c_int32
 s.SecKeychainItemFreeContent.argtypes=[ctypes.c_void_p,ctypes.c_void_p]
 cf.CFRelease.argtypes=[ctypes.c_void_p]
 # Account is read from non-secret settings; the secret never enters argv/stdout.
 account=json.loads(CONFIG.read_text())['user'].encode()
 length=ctypes.c_uint32();ptr=ctypes.c_void_p();item=ctypes.c_void_p()
 status=s.SecKeychainFindGenericPassword(None,len(SERVICE),SERVICE,len(account),account,ctypes.byref(length),ctypes.byref(ptr),ctypes.byref(item))
 if password is None:
  if status:raise RuntimeError('Keychain retrieval failed (OSStatus '+str(status)+')')
  try:return ctypes.string_at(ptr,length.value).decode()
  finally:
   s.SecKeychainItemFreeContent(None,ptr)
   if item:cf.CFRelease(item)
 value=password.encode()
 if status==0:
  s.SecKeychainItemFreeContent(None,ptr)
  try:status=s.SecKeychainItemModifyAttributesAndData(item,None,len(value),value)
  finally:
   if item:cf.CFRelease(item)
 elif status==-25300:
  status=s.SecKeychainAddGenericPassword(None,len(SERVICE),SERVICE,len(account),account,len(value),value,None)
 if status:raise RuntimeError('Keychain storage failed (OSStatus '+str(status)+')')
 return True

def install():
 required=['MAIL_HOST','MAIL_PORT','MAIL_USER','MAIL_FROM','MAIL_PASSWORD']
 if not all(os.environ.get(k) for k in required):raise RuntimeError('SMTP environment incomplete')
 if os.environ['MAIL_HOST'].lower().strip()!='smtp.gmail.com' or os.environ['MAIL_PORT'].strip()!='587':raise RuntimeError('Unexpected SMTP endpoint')
 config={'host':os.environ['MAIL_HOST'],'port':587,'user':os.environ['MAIL_USER'],'from':os.environ['MAIL_FROM'],'recipients':['ndriaffre@gmail.com'],'keychain_service':SERVICE.decode(),'daily_send_authorized':False,'timezone':'Africa/Abidjan','daily_time':None}
 fd=os.open(CONFIG,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f:json.dump(config,f,indent=2)
 keychain(os.environ['MAIL_PASSWORD'])
 assert keychain()==os.environ['MAIL_PASSWORD']
 print(json.dumps({'settings_saved':True,'keychain_roundtrip_verified':True,'recipient':'ndriaffre@gmail.com','daily_send_authorized':False}))
if __name__=='__main__':install()
