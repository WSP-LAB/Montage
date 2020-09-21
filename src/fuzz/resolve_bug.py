class ResolveBug(Exception):
  def __init__(self, msg):
    Exception.__init__(self, msg)

def error(msg):
  raise ResolveBug(msg)
