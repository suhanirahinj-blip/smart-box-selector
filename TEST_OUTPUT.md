# Test Execution Output

**Command:**
```powershell
python manage.py test box_selection
```

**Environment:**
- Django 5.2.19
- Python 3.10.0
- SQLite

**Output:**
```text
Found 6 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
......
----------------------------------------------------------------------
Ran 6 tests in 0.070s

OK
Destroying test database for alias 'default'...
```

**Result:** All 6 automated tests passed successfully.

**Test coverage:**
1. Successful box recommendation.
2. No suitable box available.
3. Product rotation.
4. Maximum weight restriction.
5. Cheapest suitable box selection.
6. Recommendation API response.