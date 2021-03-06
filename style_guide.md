# Style guide

Below is a rough style guide to keep in mind when developing/maintaining code. This is more for my benefit so I remember why things are a certain way.

- Always use 4-space indents in Python and shell scripts
- Try to obey pep8 styling [https://www.python.org/dev/peps/pep-0008/] for Python scripts. This can be done by running `python -m flake8 <path to file>`
- For terminal colours,
  - print warnings in bold yellow
  - print statements signifying ongoing processes or printing the config file in cyan
  - exceptions or built-in Python errors (`ValueError` etc.) in green
  - print statements signifying important finished processes in magenta
- Decide on whether to use snake case (`this_is_the_file`) or camel case (`ThisIsTheFile/thisIsTheFile`) in files and code. Different types can be used in different situations
- Add shebangs to executable Python and shell scripts
- Add imports to Python scripts in alphabetical order
