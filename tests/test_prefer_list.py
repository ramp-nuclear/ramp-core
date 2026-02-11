from string import ascii_lowercase
from ramp_core.serializable import _prefer_list
from hypothesis import given
import hypothesis.strategies as st


@given(st.text(alphabet=ascii_lowercase, min_size=1))
def test_prefer_list_for_str_is_str(sold):
    s = _prefer_list(sold)
    assert type(s) == type(sold)
    assert s == sold


@given(st.lists(elements=st.integers(), min_size=1).map(tuple))
def test_prefer_list_for_tuple_is_list(x):
    y = _prefer_list(x)
    assert type(y) == list
    assert all(yv == xv for yv, xv in zip(y, x))


