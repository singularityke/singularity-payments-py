from singularity_payments.tests.fixtures.callback import successfull_stk_callback, failed_stk_callback
import pytest


def test_successfull_stk_callback():
    successfull_stk_callback()
    

def test_failed_stk_callback():
    with pytest.raises(Exception):
        failed_stk_callback()


