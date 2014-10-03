# Sublime LocalVariable plugin

The glorious local variable plugin. Provides extract/detach variable refactoring
and API for other plugins to work with variables.


### Demo

![Demo](https://raw.github.com/shagabutdinov/sublime-local-variable/master/demo/demo.gif "Demo")


### Installation

This plugin is part of [sublime-enhanced](http://github.com/shagabutdinov/sublime-enhanced)
plugin set. You can install sublime-enhanced and this plugin will be installed
automatically.

If you would like to install this package separately check "Installing packages
separately" section of [sublime-enhanced](http://github.com/shagabutdinov/sublime-enhanced)
package.


### Features

1. Extract variable - create new variable from method call or from selected text

2. Detach variable - destroy variable and replace all usage with what was
assigned to this variable

3. Rename variable - expand cursors to all variable occurrences in current
method

It also inserts mark so you can come back to location before editing was started
by hitting "goto mark" (see "[sublime-named-mark](http://github.com/shagabutdinov/sublime-named-mark)"
package for keyboard shortcut).

### Usage

##### Extract variable

  ```
  # before
  call1(call(|)) # <- cursor here
  call2(call())

  # after
  | = call() # <- cursors here
  call1(|) # <- cursors here
  call2(|) # <- cursors here

  # after typing variable name
  variable = call()
  call1(variable)
  call2(variable)
  ```

##### Detach variable

  ```
  # before
  variable| = call1() # <- cursor here
  call2(variable)
  call3(variable)

  # after
  call2(call1())
  call3(call1())
  ```

##### Rename variable

  ```
  # before
  call1(variable|) # <- cursor here
  call2(variable)

  # after
  call1({variable}) # <- selections here
  call2({variable}) # <- selections here
  ```


### Commands

| Description      | Keyboard shortcut | Command palette        |
|------------------|-------------------|------------------------|
| Extract variable | ctrl+alt+x        | LocalVariable: Extract |
| Detach variable  | ctrl+shift+x      | LocalVariable: Detach  |
| Rename variable  | alt+shift+x       | LocalVariable: Rename  |