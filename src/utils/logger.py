class Colors:
  END = '\033[0m'
  ERROR = '\033[91m[ERROR] '
  INFO = '\033[94m[INFO] '
  WARN = '\033[93m[WARN] '

def get_color(msg_type):
  if msg_type == 'ERROR':
    return Colors.ERROR
  elif msg_type == 'INFO':
    return Colors.INFO
  elif msg_type == 'WARN':
    return Colors.WARN
  else:
    return Colors.END

def get_msg(msg, msg_type=None):
  color = get_color(msg_type)
  msg = ''.join([color, msg, Colors.END])
  return msg

def print_msg(msg, msg_type=None):
  msg = get_msg(msg, msg_type)
  print(msg)
