# TODO - Future Improvements

## Code Architecture

### Refactor: Extract Core Converter Module
**Priority:** Medium
**Version:** 2.0.0
**Status:** ✅ COMPLETED (2026-01-09)

**Previous Structure:**
```
a2j_gui.py          # Contains BOTH core logic + GUI (1300 lines)
  └─ AlembicToJSXConverter class (core converter)
  └─ AlembicToJSXGUI class (GUI wrapper)

a2j.py              # CLI that imports from "gui" file
  └─ from a2j_gui import AlembicToJSXConverter
```

**Current Structure:**
```
alembic_converter.py    # Pure module - just the converter logic (✅ DONE)
  └─ AlembicToJSXConverter class

a2j_gui.py             # GUI wrapper (✅ DONE)
  └─ from alembic_converter import AlembicToJSXConverter
  └─ AlembicToJSXGUI class

a2j.py                 # CLI wrapper (✅ DONE)
  └─ from alembic_converter import AlembicToJSXConverter
```

**Benefits:**
- ✅ Clearer separation of concerns
- ✅ Neither CLI nor GUI is "dependent" on the other
- ✅ Module name clearly indicates it's shared core logic
- ✅ More maintainable - core logic changes in one place
- ✅ Could easily add third interface (web API, plugin, etc.) without weird imports
- ✅ Better architecture for testing

**Implementation Steps:**
1. ✅ Create new file: `alembic_converter.py`
2. ✅ Move `AlembicToJSXConverter` class from `a2j_gui.py` to `alembic_converter.py`
3. ✅ Update `a2j_gui.py` to import from `alembic_converter`
4. ✅ Update `a2j.py` to import from `alembic_converter`
5. ⚠️ Test both CLI and GUI to ensure parity (USER SHOULD TEST)
6. ✅ Update documentation (README.md, build_executable.py)

**Testing Checklist (User should verify):**
- [ ] GUI produces identical output to v1.0.0
- [ ] CLI produces identical output to v1.0.0
- [ ] All coordinate transformations working correctly
- [ ] OBJ export functioning
- [ ] Multi-DCC support (SynthEyes, Nuke, etc.) still working
- [ ] Windows executable builds correctly
- [ ] macOS setup.sh still works

---

## Future Features

### Add Progress Callbacks for Large Files
**Priority:** Low
**Version:** TBD

For very large Alembic files with hundreds of objects, add progress reporting to CLI mode.

---

## Documentation

### Add Examples Directory
**Priority:** Low
**Version:** TBD

Add example Alembic files and expected JSX output for testing/demonstration purposes.

---

_Last Updated: 2026-01-09_
