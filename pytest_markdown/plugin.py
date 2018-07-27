import imp

import CommonMark
import pytest
from _pytest.python import Module


class MarkdownItem(Module):

    def __init__(self, name, file, code, nodeid=None):
        self._code_obj = imp.new_module(name)
        exec(code, self._code_obj.__dict__)
        super().__init__(name, file, nodeid=nodeid)

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
    return ''.join(literals)


class MarkdownCollector(object):

    def __init__(self, item):
        super().__init__()
        self.item = item
        self.ast = CommonMark.Parser().parse(self.item.fspath.open().read())
        self.stack = [(0, self.item, self.item.name,)]
        self.collected = []

    def collect(self):
        self.stack = [(0, self.item, self.item.name,)]
        self.collected = []

        walker = self.ast.walker()

        event = walker.nxt()
        while event is not None:
            if not event['entering']:
                event = walker.nxt()
                continue

            func = 'visit_' + event['node'].t
            if hasattr(self, func):
                getattr(self, func)(event['node'])

            event = walker.nxt()

        return self.collected

    def visit_heading(self, token):
        while self.stack[-1][0] >= token.level:
            self.stack.pop()

        name = collect_literals_from_children(token).lower().replace(' ', '-')
        nodeid = '::'.join(s[2] for s in self.stack) + '::' + name
        self.stack.append((
            token.level,
            pytest.Item(name, self.stack[-1][1], nodeid=nodeid),
            name
        ))

    def visit_code_block(self, token):
        if token.info != 'python':
            return

        output = token.literal

        if output.startswith('\n'):
            return ''

        name = f'line_{token.sourcepos[0][0]}'

        if output.lower().strip().startswith('# conftest.py\n'):
            nodeid = self.stack[-1][1].nodeid
        else:
            nodeid = self.stack[-1][1].nodeid + '::' + name

        mi = MarkdownItem(
            name,
            self.stack[-1][1],
            output,
            nodeid=nodeid
        )
        self.collected.append(mi)

        return ''


class MarkdownFile(pytest.File):

    def collect(self):
        for item in MarkdownCollector(self).collect():
            yield item


def pytest_collect_file(parent, path):
    if path.ext == '.md':
        return MarkdownFile(path, parent)
