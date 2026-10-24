"""Native transition registration tests. No BAF agent or model is constructed."""

import ast
import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Union


ROOT = Path(__file__).resolve().parents[3]


def native_transition_classes():
    """Compile original first-party registration classes without NLP imports."""
    exception_source = ROOT / "baf/exceptions/exceptions.py"
    exceptions = ast.parse(exception_source.read_text(encoding="utf-8"))
    error_classes = [copy.deepcopy(item) for item in exceptions.body
                     if isinstance(item, ast.ClassDef)
                     and item.name in {"StateNotFound", "ConflictingAutoTransitionError"}]
    scope = {"Callable": Callable, "Union": Union}
    exec(compile(ast.fix_missing_locations(ast.Module(body=error_classes, type_ignores=[])), str(exception_source), "exec"), scope)
    source = ROOT / "baf/core/transition/transition.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    transition = copy.deepcopy(next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "Transition"))
    scope.update({"Event": object, "Condition": object})
    exec(compile(ast.fix_missing_locations(ast.Module(body=[transition], type_ignores=[])), str(source), "exec"), scope)
    source = ROOT / "baf/core/transition/transition_builder.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    builder = copy.deepcopy(next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "TransitionBuilder"))
    scope.update({"inspect": __import__("inspect"), "partial": __import__("functools").partial,
                  "Conjunction": object})
    exec(compile(ast.fix_missing_locations(ast.Module(body=[builder], type_ignores=[])), str(source), "exec"), scope)
    return scope


class StateRecord:
    """Plain state registry data; not a BAF agent or an LLM test fixture."""

    def __init__(self, name):
        self.name = name
        self.transitions = []
        self._agent = None

    def _t_name(self):
        return f"t_{len(self.transitions) + 1}"

    def _check_global_state(self, _):
        pass

    def go_to(self, _):
        raise AssertionError("no runtime state transition is executed")


class NativeTransitionAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = native_transition_classes()

    def setUp(self):
        self.start = StateRecord("start")
        self.finish = StateRecord("finish")
        owner = SimpleNamespace(name="static-registry", states=[self.start, self.finish])
        self.start._agent = self.finish._agent = owner
        self.Builder = self.native["TransitionBuilder"]
        self.Error = self.native["ConflictingAutoTransitionError"]

    def test_single_auto_transition_is_allowed(self):
        self.Builder(self.start).go_to(self.finish)
        self.assertTrue(self.start.transitions[0].is_auto())

    def test_single_event_transition_is_allowed(self):
        self.Builder(self.start, event=object()).go_to(self.finish)
        self.assertFalse(self.start.transitions[0].is_auto())

    def test_event_then_auto_is_rejected(self):
        self.Builder(self.start, event=object()).go_to(self.finish)
        with self.assertRaises(self.Error):
            self.Builder(self.start).go_to(self.finish)
        self.assertEqual(len(self.start.transitions), 1)

    def test_condition_then_auto_is_rejected(self):
        self.Builder(self.start, condition=object()).go_to(self.finish)
        with self.assertRaises(self.Error):
            self.Builder(self.start).go_to(self.finish)
        self.assertEqual(len(self.start.transitions), 1)

    def test_auto_then_event_already_rejected(self):
        self.Builder(self.start).go_to(self.finish)
        with self.assertRaises(self.Error):
            self.Builder(self.start, event=object()).go_to(self.finish)

    def test_second_auto_already_rejected(self):
        self.Builder(self.start).go_to(self.finish)
        with self.assertRaises(self.Error):
            self.Builder(self.start).go_to(self.finish)

    def test_unknown_destination_rejected(self):
        missing = StateRecord("unknown")
        with self.assertRaises(self.native["StateNotFound"]):
            self.Builder(self.start).go_to(missing)


if __name__ == "__main__":
    unittest.main()
