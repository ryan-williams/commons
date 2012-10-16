__author__ = 'ryan'

from mock import Mock

def p(x):
  print str(x)

attrs = {'info.side_effect': p}

def MockLogger():
  return Mock(**attrs)
