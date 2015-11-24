import sublime
import sublime_plugin

from LocalVariable.local_variable import find_entries

try:
  from Expression import expression
except ImportError as error:
  sublime.error_message("Dependency import failed; please read readme for " +
   "LocalVariable plugin for installation instructions; to disable this " +
   "message remove this plugin; message: " + str(error))
  raise error

class RenameVariable(sublime_plugin.TextCommand):
  def run(self, edit):
    if len(self.view.sel()) == 0:
      return

    sel = self.view.sel()[0]
    if not sel.empty():
      variable = [sel.a, sel.b]
    else:
      line_region = self.view.line(sel.b)
      line_start, line_end = line_region.begin(), line_region.end()

      start = expression.find_match(self.view, sel.b, '[^\w$@]|^', {'backward': True,
        'range': [line_start, sel.b], 'string': True, 'nesting': True,
        'comment': True})

      end = expression.find_match(self.view, sel.b, '[^\w?!]|$',
        {'range': [sel.b, line_end], 'string': True, 'nesting': True,
        'comment': True})

      if start == None or end == None or start == end:
        return

      variable = [start.end(0) + line_start, end.start(0) + sel.b]

    entries = find_entries(self.view, variable)
    if len(entries) == 0:
      return

    self.view.sel().clear()
    for entry in entries:
      self.view.sel().add(sublime.Region(*entry))
