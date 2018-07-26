# Header 1

You can define a conftest.py in the top of your markdown file:

```python
# conftest.py

import pytest

@pytest.fixture
def example():
    return 1234
```

And you can have tests:

```python
# test_1.py

def test_1(example):
    assert example == 1234
```

There can be multiple code blocks in each section, and each code block can contain multiple tests:


```python
# test_2.py

def test_2(example):
    assert example == 1234

def test_3(example):
    assert example + 1 == 1235
```

## Header 2a

Defining a new child - it can see the parent conftest, even if other fixtures are defined.

```python
# conftest.py

import pytest

@pytest.fixture
def example2():
    return 4321
```

And then tests:

```python
# test_1.py

def test_1(example):
    assert example == 1234
```

### Header 3a

Defining a new child - 3 levels deep - it can see the parent conftest.

```python
# test_1.py

def test_1(example, example2):
    assert example == 1234
    assert example2 == 4321
```

## Header 2b

You can define a conftest.py in a heading. It can override conftest.py stuff in the parent section:

```python
# conftest.py

import pytest

@pytest.fixture
def example():
    return 1235
```

And you can have tests:

```python
# test_1.py

def test_1(example):
    assert example == 1235
```

## Header 2c

Defining a new sibling - it can see the root conftest but not its siblings.

```python
# test_1.py

def test_1(example):
    assert example == 1234
```
