import imp

import pytest
from _pytest.python import Module
from mistletoe.base_renderer import BaseRenderer


class MarkdownItem(Module):

    def __init__(self, name, file, code, nodeid=None):
        self._code_obj = imp.new_module(name)
        exec(code, self._code_obj.__dict__)
        super().__init__(name, file, nodeid=nodeid)

    def _getobj(self):
        return self._code_obj


class MarkdownCollector(BaseRenderer):

    def __init__(self, item):
        super().__init__()
        self.item = item
        self.stack = [(0, self.item, self.item.name,)]
        self.collected = []

    def render_heading(self, token):
        name = ''.join(self.render(c) for c in token.children).lower().replace(' ', '-')

        while self.stack[-1][0] >= token.level:
            self.stack.pop()

        nodeid = '::'.join(s[2] for s in self.stack) + '::' + name
        self.stack.append((
            token.level,
            pytest.Item(name, self.stack[-1][1], nodeid=nodeid),
            name
        ))

        return ''

    def render_block_code(self, token):
        if token.language != 'python':
            return ''

        output = ''.join(c.content for c in token.children)

        if output.startswith('\n'):
            return ''

        name = f'line_{token.start}'

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

    def collect(self, token):
        self.render(token)
        return self.collected


class MarkdownFile(pytest.File):

    def collect(self):
        fp = self.fspath.open()

        from mistletoe import Document
        with MarkdownCollector(self) as collector:
            for item in collector.collect(Document(fp)):
                yield item


def pytest_collect_file(parent, path):
    if path.ext == '.md':
        return MarkdownFile(path, parent)
