import sublime
import sublime_plugin

import re
from LocalVariable.local_variable import get_partial_statement, find_entries

try:
  from Method import method
  from Expression import expression
  from Statement import statement
except ImportError:
  sublime.error_message("Dependency import failed; please read readme for " +
   "LocalVariable plugin for installation instructions; to disable this " +
   "message remove this plugin")


class ExtractVariable(sublime_plugin.TextCommand):

  def run(self, edit):
    entries = None
    if len(self.view.sel()) > 1:
      entries = []
      for overlap in self.view.sel():
        entries.append([overlap.begin(), overlap.end()])

    self._extract(edit, self.view.sel()[0], entries)

  def _extract(self, edit, sel, entries):
    if sel.empty():
      variable = get_partial_statement(self.view, sel.b)
    else:
      variable = [sel.a, sel.b]

    if variable == None:
      return None

    if entries == None:
      entries = find_entries(self.view, variable, False)

    if len(entries) == 0:
      entries = [variable]

    line_info = self._get_line_for_variables(entries)
    if line_info == None:
      return

    line, indentation = line_info
    self._create_variable(edit, line, entries, indentation)

  def _get_line_for_variables(self, entries):
    start = entries[0][0]
    root_statement = statement.get_root_statement(self.view, start)
    if root_statement == None:
      return None

    start = root_statement[0]
    line, _ = self.view.rowcol(start)
    indentation = self.get_indentation(start)

    if not self.is_lesser_indentation_required(entries):
      return line, indentation

    while True:
      previous_start = self.view.line(start).begin() - 1
      if previous_start < 0:
        return None

      current = self.get_indentation(previous_start)
      if len(current) < len(indentation):
        line, _ = self.view.rowcol(self.view.line(previous_start).begin())
        return line, current

      start = previous_start

  def is_lesser_indentation_required(self, entries):
    if len(entries) == 1:
      return False

    start_line, _ = self.view.rowcol(entries[0][0])
    lines = self.view.substr(self.view.line(sublime.Region(entries[0][0],
      entries[len(entries) - 1][1])))

    indentation = None
    for index, line in enumerate(lines.split("\n")):
      if line.strip() == '':
        continue

      point = self.view.text_point(start_line + index, 0)
      in_nesting = expression.find_match(self.view, point, r'[\])]',
        {'range': [point, point + 512]})

      if in_nesting:
        continue

      if statement.is_arguments(self.view, point):
        continue

      current = len(self.get_indentation(line))

      if indentation == None : # first overlap
        indentation = current
      if current < indentation:
        return True

    return False

  def get_indentation(self, point):
    if isinstance(point, str):
      line = point
    else:
      line = self.view.substr(self.view.line(point))

    return re.search(r'^\s*', line).group(0)

  def _create_variable(self, edit, line, entries, indentation):
    value = self.view.substr(sublime.Region(*entries[0]))

    for index, overlap in enumerate(reversed(entries)):
      self.view.replace(edit, sublime.Region(*overlap), '')
      self.view.add_regions('local_variable_placeholder_' + str(index),
        [sublime.Region(overlap[0], overlap[0])])

    line_region = self.view.line(self.view.text_point(line, 0))
    point = line_region.begin() - 1
    definition = indentation + ' = ' + value + "\n"
    if line != 0:
      definition = "\n" + definition

    self.view.replace(edit, sublime.Region(point, point + 1), definition)
    point += len(indentation) + 1
    self.view.add_regions('local_variable_placeholder_last',
      [sublime.Region(point, point)])

    self.view.sel().clear()
    regions = []
    for index, _ in enumerate(entries):
      regions += self.view.get_regions('local_variable_placeholder_' +
        str(index))

    regions += self.view.get_regions('local_variable_placeholder_last')
    self.view.sel().add_all(regions)