__author__ = 'ryan'

class MockProcess(object):

  def __init__(self, target, return_vals):
    self.target = target
    self.return_vals = return_vals

  def poll(self):
    return self.return_vals.pop()

