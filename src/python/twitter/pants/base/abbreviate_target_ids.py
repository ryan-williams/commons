__author__ = 'ryan'

import copy

def abbreviate_target_ids(arr):
  ""
  split_keys = [tuple(a.split('.')) for a in arr]

  split_keys_by_subseq = {}

  def subseq_map(arr, subseq_fn = None, result_cmp_fn = None):
    def subseq_map_rec(remaining_arr, subseq, indent = ''):
      if not remaining_arr:
        if subseq_fn:
          subseq_fn(arr, subseq)
        return subseq

      next_segment = remaining_arr.pop()
      next_subseq = tuple([next_segment] + list(subseq))

      skip_value = subseq_map_rec(remaining_arr, subseq, indent + '\t')

      add_value = subseq_map_rec(remaining_arr, next_subseq, indent + '\t')

      remaining_arr.append(next_segment)

      if result_cmp_fn:
        if result_cmp_fn(skip_value, add_value):
          return skip_value
        return add_value

      return None

    val = subseq_map_rec(list(arr), tuple())
    return val


  def add_subseq(arr, subseq):
    if subseq not in split_keys_by_subseq:
      split_keys_by_subseq[subseq] = set()
    if split_key not in split_keys_by_subseq[subseq]:
      split_keys_by_subseq[subseq].add(arr)

  for split_key in split_keys:
    subseq_map(split_key, add_subseq)

#  for subseq in split_keys_by_subseq:
#    print "(%s) -> [%s]" % (','.join([str(s) for s in subseq]), ','.join([str(s) for s in split_keys_by_subseq[subseq]]))

  def return_min_subseqs(subseq1, subseq2):
    collisions1 = split_keys_by_subseq[subseq1]
    collisions2 = split_keys_by_subseq[subseq2]
    if (len(collisions1) < len(collisions2) or
        (len(collisions1) == len(collisions2) and
         len(subseq1) <= len(subseq2))):
      return True
    return False

  min_subseq_by_key = {}

  for split_key in split_keys:
    min_subseq = subseq_map(split_key, result_cmp_fn=return_min_subseqs)
    if not min_subseq:
      raise Exception("No min subseq found for %s" % str(split_key))
    min_subseq_by_key['.'.join([str(segment) for segment in split_key])] = '.'.join(min_subseq)

  print ''
  for key, min_subseq in min_subseq_by_key.iteritems():

    print "  '%s': '%s'," % (min_subseq, key)

  return min_subseq_by_key


def print_shortened_deps(deps):
  mapping = abbreviate_target_ids(deps.keys())
  for key, obj in deps.iteritems():
    new_key = mapping[key]
    children = obj['children']
    new_children = [mapping[child] for child in children]
    obj['children'] = new_children
    print "  '%s': %s," % (new_key, str(obj))
