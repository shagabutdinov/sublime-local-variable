import sublime
import sublime_plugin
from Method import method
from Statement import statement
from LocalVariable import local_variable
import re

class DetachVariable(sublime_plugin.TextCommand):
  def run(self, edit):
    for selection in self.view.sel():
      self._detach(edit, selection)

  def _detach(self, edit, selection):
    info = self._get_info(selection)
    if info == None:
      return None

    assignments, entries = info
    conversions = self._get_conversions(assignments, entries)

    for index, conversion in enumerate(reversed(conversions)):
      self._process_conversion(edit, index, conversion)

    self._highligh(conversions)

  def _get_info(self, selection):
    variable = self._get_variable(selection)
    if variable == None:
      return

    variable_range, _ = variable
    scope = local_variable.get_scope(self.view, variable_range[0])
    assignments = local_variable.find_assignments(self.view, variable_range)
    if len(assignments) == 0 or self._is_variable_modified(assignments):
      return

    entries = local_variable.find_entries(self.view, variable_range)
    return assignments, entries

  def _get_conversions(self, assignments, entries):
    result = []
    for entry in entries:
      for assignment in reversed(assignments):
        if assignment['variable'] == entry:
          result.append(['assignment', entry, assignment['value']])
          break

        if assignment['variable'][0] < entry[0]:
          result.append(['entry', entry, assignment['value']])
          break

    return result

  def _process_conversion(self, edit, index, conversion):
    type, entry, assignment = conversion
    if type == 'entry':
      self._process_entry(edit, index, entry, assignment)
    else:
      self._process_assignment(edit, entry, assignment)

  def _process_entry(self, edit, index, entry, assignment):
    region = sublime.Region(*entry)
    replacement = self.view.substr(sublime.Region(*assignment))
    self.view.replace(edit, region, replacement)
    highlight = sublime.Region(region.a, region.a + len(replacement))
    self.view.add_regions('detach_variable_' + str(index), [highlight])

  def _process_assignment(self, edit, entry, assignment):
    variable_region = statement.get_token_delete_region(self.view, entry[0])
    tokens = statement.get_arguments(self.view, assignment[0], assignment)
    region = statement.get_token_delete_region(self.view, assignment[0], tokens)

    if variable_region.intersects(region):
      self.view.erase(edit, sublime.Region(variable_region.a, region.b))
    else:
      self.view.erase(edit, region)
      self.view.erase(edit, variable_region)

    line_region = self.view.line(entry[0])
    stripped_line = self.view.substr(line_region).strip()
    if stripped_line != '' and stripped_line != ';':
      return

    next_line = self.view.substr(self.view.line(line_region.b + 1))
    next_line_spaces = re.search(r'^\s*', next_line).end(0)
    next_line_start = line_region.b + 1 + next_line_spaces
    self.view.erase(edit, sublime.Region(entry[0], next_line_start))

  def _highligh(self, conversions):
    highlights = []
    for index, conversion in enumerate(conversions):
      highlights += self.view.get_regions('detach_variable_' + str(index))
      self.view.erase_regions('detach_variable_' + str(index))

    self.view.add_regions('detach_variable', highlights, 'string', '', 
      sublime.DRAW_EMPTY | sublime.DRAW_OUTLINED)

  def _is_variable_modified(self, assignments):
    for assignment in assignments:
      if assignment['type'] != '=' or assignment['dirty']:
        return True

    return False

  def _get_variable(self, selection):
    if not selection.empty():
      return selection, self.view.substr(selection)

    return local_variable.get_variable(self.view, selection.b)

class CleanHighlights(sublime_plugin.EventListener):
  def on_selection_modified_async(self, view):
    if view.command_history(0)[0] == 'detach_variable':
      return

    view.erase_regions('detach_variable')