### To publish to pypi.

Do not forget to up the version number in `pyproject.toml`.

'''
ms@mma moneycounter % python3 -m build
ms@mma moneycounter % python3 -m twine upload  dist/*
'''