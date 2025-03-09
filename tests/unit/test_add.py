from pyback.core.utils import add


class TestHandlers:
    def test_add_util(self):
        """Test the add function from the utils module"""
        assert add(5, 3) == 8
