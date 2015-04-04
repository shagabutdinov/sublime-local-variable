import sublime
import sublime_plugin

import re

try:
  from Expression import expression
  from Statement import statement
  from Method import method as method_parser
except ImportError:
  sublime.error_message("Dependency import failed; please read readme for " +
   "LocalVariable plugin for installation instructions; to disable this " +
   "message remove this plugin")

VARIABLE = r'[$@]?\w+[?!]?(?!\s*\()'

def get_variable(view, point):
  token = statement.get_token(view, point)
  if token == None:
    return None

  _, token = token
  if not is_variable(view, token):
    return None

  return token, view.substr(sublime.Region(*token))

# "partial statement" it is something, that is not variable itself
def get_partial_statement(view, point):
  nesting = expression.get_nesting(view, point)

  as_argument = (
    nesting != None and
    statement.get_statement(view, nesting[0]) ==
      statement.get_statement(view, nesting[1])
  )

  if as_argument:
    argument = statement.get_argument(view, point)
    if argument != None:
      _, argument = argument

    argument = prepare_argument(view, argument, point)
    if argument == None or is_variable(view, argument):
      token = statement.get_parent_token(view, point)
      return prepare_argument(view, token, point)

    return argument
  else:
    tokens = statement.get_tokens(view, point)
    if tokens == None:
      return None

    _, token = statement.get_token(view, point, tokens)
    if token == None or not is_variable(view, token):
      return token

    tokens_range = [tokens[0][0], tokens[len(tokens) - 1][1]]
    assignment_match = expression.find_match(view, tokens_range[0],
      r'=[^=]\s*', {'range': tokens_range})
    if assignment_match != None:
      tokens_range[0] += assignment_match.end(0)
    return tokens_range

def is_variable(view, token):
  if 'string' in view.scope_name(token[0]):
    return False

  token_value = view.substr(sublime.Region(*token))
  if re.search(r'^[$@]?\w+$', token_value) == None:
    return False

  if not _is_variable(view, token):
    return False

  return True

def _is_variable(view, token):
  scope_name = view.scope_name(token[0])
  is_keyword = (
    ('constant' in scope_name and not 'symbol' in scope_name) or
    'control' in scope_name or
    'operator' in scope_name or
    'string' in scope_name
  )

  if is_keyword:
    return False

  next_16_chars = view.substr(sublime.Region(token[1], token[1] + 16))
  if re.search(r'^\s*\(', next_16_chars):
    return False

  return True

def prepare_argument(view, argument, point):
  if argument == None:
    return None

  hash_match = expression.find_match(view, argument[0],
    r'((\S|^)(?<!:):(?!:)|=>|=)\s*', {'range': argument})

  if hash_match == None:
    return argument

  delimeter_point = argument[0] + hash_match.end(0)
  if point >= delimeter_point:
    return None

  argument[0] = delimeter_point
  return argument

def find_variables(view, point, header = True, scope = None):
  if scope == None:
    scope = get_scope(view, point, header)

  options = {'range': scope, 'nesting': True}
  expr = _get_variable_expression(VARIABLE)
  matches = expression.find_matches(view, scope[0], expr, options)

  result = []
  for match in matches:
    region = [scope[0] + match.start(1), scope[0] + match.end(1)]
    if not _is_variable(view, region):
      continue

    result.append(region)

  return result

def find_entries(view, variable, header = True, scope = None):
  if scope == None:
    scope = get_scope(view, variable[0], header)

  variable_name = view.substr(sublime.Region(*variable))

  options = {'range': scope, 'nesting': True}
  expr = _get_variable_expression('(' + re.escape(variable_name) + ')')
  matches = expression.find_matches(view, scope[0], expr, options)

  result = []
  for match in matches:
    region = [scope[0] + match.start(2), scope[0] + match.end(2)]
    if not _is_variable(view, region):
      continue
    result.append(region)

  return result

# slow
def find_all_assignments(view, point, scope = None):
  variables = find_variables(view, point, False, scope)
  result = _get_header_assignments(view, point)

  cache = []
  for variable in variables:
    info = get_assignment_info(view, variable, cache)
    if info == None:
      continue

    result += info

  return result

def find_assignments(view, variable, scope = None):
  result, entries = [], find_entries(view, variable, False, scope)

  cache = []
  for entry in entries:
    assignment = get_assignment_info(view, entry, cache)
    if assignment == None:
      continue

    result += assignment

  return result

def _get_header_assignments(view, point):
  method_info = method_parser.extract_method(view, point)
  if method_info == None:
    return

  _, method = method_info

  method_region = sublime.Region(method['start'], method['end'])
  parenthethis = re.search(r'^[^\n]*\(', view.substr(method_region))
  if parenthethis == None:
    return []

  tokens = statement.get_tokens(view, method['start'] + parenthethis.end(0))
  result = []
  for token in tokens:
    if not is_variable(view, token):
      continue

    result.append({
      'variable': token,
      'value': None,
      'dirty': False,
    })

  return result

def get_assignment_info(view, entry, cache = []):
  container, tokens = None, None
  for cached in cache:
    if cached['statement'][0] <= entry[0] and entry[1] <= cached['statement'][1]:
      container = cached['statement']
      tokens = cached['tokens']
      break

  if container == None or tokens == None:
    container = statement.get_root_statement(view, entry[1])
    tokens = statement.get_tokens(view, entry[1])
    if container != None and tokens != None:
      cache.append({'statement': container, 'tokens': tokens})

  if tokens == None or len(tokens) == 0 or tokens[0][0] != entry[0]:
    return None

  delimeter_index, delimeter = None, None
  for index, current in enumerate(tokens[:-1]):
    next = tokens[index + 1]
    delimeter_value = view.substr(sublime.Region(current[1], next[0]))
    delimeter = re.search(r'^\s*([+*\-/:]?=)(?!=)\s*', delimeter_value)
    if delimeter != None:
      delimeter_index = index
      break

  if delimeter == None:
    return None

  left, right = tokens[:delimeter_index + 1], tokens[delimeter_index + 1:]
  right_container = [right[0][0], right[-1][1]]
  right = statement.get_arguments(view, right[0][0], right_container)
  type = delimeter.group(1)
  if len(left) != len(right):
    if len(right) == 1:
      result = _get_assignments(view, type, left, right[-1])
    else:
      result = None
  else:
    result = _get_assignment_info_recurive(view, type, left, right)

  return result

def _get_assignment_info_recurive(view, type, left_tokens, right_tokens):
  result = []
  for index, left in enumerate(left_tokens):
    right = right_tokens[index]

    left_value = view.substr(sublime.Region(*left))
    left_match = re.search(r'^(list\(|\(|\[)', left_value)

    right_value = view.substr(sublime.Region(*right))
    right_match = re.search(r'^(array\(|\(|\[)', right_value)

    if left_match != None and right_match != None:
      left_sub_tokens = statement.get_arguments(view, left[1] +
        left_match.end(0), statement = left)

      right_sub_tokens = statement.get_arguments(view, right[1] +
        right_match.end(0), statement = right)

      is_tokens_not_parsable = (
        left_sub_tokens == None or
        right_sub_tokens == None or
        len(left_sub_tokens) != len(right_sub_tokens)
        # e.g. 1, (2, 3) = f1(), [f2()]
      )

      if is_tokens_not_parsable:
        continue

      result += _get_assignment_info_recurive(view, type, left_sub_tokens,
        right_sub_tokens)

      continue

    result += _get_assignments(view, type, left, right)

  return result

def _get_assignments(view, type, left, right):
  if isinstance(left[0], list):
    variables = left
  else:
    left_value = view.substr(sublime.Region(*left))
    left_match = re.search(r'^list\(|\(|\[', left_value)
    if left_match != None:
      variables = statement.get_tokens(view, left[1] +
        left_match.end(0), statement = left)
    else:
      variables = [left]

  is_dirty = len(variables) > 1

  result = []
  for variable in variables:
    variable_value = view.substr(sublime.Region(*variable))
    variable_length = re.search(r'[$@]?\w+(!|\?)?', variable_value).end(0)
    result.append({
      'variable': [variable[0], variable[0] + variable_length],
      'value': right,
      'type': type,
      'dirty': is_dirty,
    })

  return result

# temporary; should calculate variable scope
def get_scope(view, point, header = True):
  return get_root_scope(view, point, header)

def get_root_scope(view, point, header = True):
  method = method_parser.extract_method(view, point)
  if method == None:
    return [0, view.size()]

  _, method = method
  if header:
    return [method['start'], method['end']]

  return [method['body_start'], method['body_end']]

def _get_variable_expression(name):
  result = r'(?:^|[^\w\.])(?:var\s*)?(' + name + r')(?!\s*\()(?=\W|$)'
  return result