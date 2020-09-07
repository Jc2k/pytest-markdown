import ast
from linecache import cache
import types

from _pytest.assertion.rewrite import rewrite_asserts
from _pytest.python import Module
import commonmark
import py
import pytest


def create_pytest_module(name, path, source, config):
    """Return a Module from source string with its assertions rewritten"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    rewrite_asserts(tree, py.path.local(path), config)

    try:
        co = compile(tree, path, "exec", dont_inherit=True)
    except SyntaxError:
        return

    mod = types.ModuleType(name)
    exec(co, mod.__dict__)

    # Also, seed the line cache, so pytest can show source code
    def getsource():
        return source

    cache[path] = (getsource,)

    return mod


class MarkdownItem(Module):
    def __init__(self, fspath, parent, code, nodeid=None):
        self._code_obj = create_pytest_module(
            fspath.basename, fspath.basename, code, parent.config
        )
        super().__init__(fspath, parent, nodeid=nodeid)

    def _getobj(self):
        return self._code_obj


def collect_literals_from_children(token):
    literals = []
    stack = [token.first_child]
    while stack:
        cur = stack.pop()
        if cur.literal:
            literals.append(cur.literal)
        if cur.nxt:
            stack.append(cur.nxt)
        if cur.first_child:
            stack.append(cur.first_child)
    return "".join(literals)


class MarkdownCollector:
    def __init__(self, item):
        super().__init__()
        self.item = item
        self.ast = commonmark.Parser().parse(self.item.fspath.open().read())
        self.stack = [
            (
                0,
                self.item,
                self.item.name,
            )
        ]
        self.collected = []

    def collect(self):
        self.stack = [
            (
                0,
                self.item,
                self.item.name,
            )
        ]
        self.collected = []

        walker = self.ast.walker()

        event = walker.nxt()
        while event is not None:
            if not event["entering"]:
                event = walker.nxt()
                continue

            func = "visit_" + event["node"].t
            if hasattr(self, func):
                getattr(self, func)(event["node"])

            event = walker.nxt()

        return self.collected

    def visit_heading(self, token):
        while self.stack[-1][0] >= token.level:
            self.stack.pop()

        name = collect_literals_from_children(token).lower().replace(" ", "-")
        nodeid = "::".join(s[2] for s in self.stack) + "::" + name
        self.stack.append(
            (
                token.level,
                pytest.Item.from_parent(self.stack[-1][1], name=name, nodeid=nodeid),
                name,
            )
        )

    def visit_code_block(self, token):
        if token.info != "python":
            return

        output = token.literal

        if output.startswith("\n"):
            return ""

        name = f"line_{token.sourcepos[0][0]}"

        if output.lower().strip().startswith("# conftest.py\n"):
            nodeid = self.stack[-1][1].nodeid
        else:
            nodeid = self.stack[-1][1].nodeid + "::" + name

        mi = MarkdownItem.from_parent(
            self.stack[-1][1],
            fspath=self.item.fspath,
            code=output,
            nodeid=nodeid,
        )
        self.collected.append(mi)

        return ""


class MarkdownFile(pytest.File):
    def collect(self):
        yield from MarkdownCollector(self).collect()


def pytest_collect_file(parent, path):
    if path.ext == ".md":
        return MarkdownFile.from_parent(parent, fspath=path)
