import inspect

from CustomModules import Mechanics as Module

functions = inspect.getmembers(Module, inspect.isfunction)
print(functions)