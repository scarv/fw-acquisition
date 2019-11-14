
import secrets

SCASS_FLAG_RANDOMISE = (0x1 << 0)
SCASS_FLAG_INPUT     = (0x1 << 1)
SCASS_FLAG_OUTPUT    = (0x1 << 2)
SCASS_FLAG_TTEST_VAR = (0x1 << 3)

class TargetVar:
    """
    Represents a variable on the target device which can be managed
    by the SCASS Framework
    """

    def __init__(self, vid, name, size, flags):
        """
        Create a new target variable.
        """

        self._id   = vid
        self._name = name
        self._size = size
        self._flags= flags

        self._fixed_value   = None
        self._current_value = None

    def setFixedValue(self, v):
        """
        Set the fixed value which the target variable will take during
        a TTest.
        """
        assert(isinstance(v,bytes))
        assert(len(v) == self.size)

        self._fixed_value = v

    def randomiseValue(self):
        """
        Randomise the current value of the target variable.
        """
        self._current_value = secrets.token_bytes(self.size)

    def takeFixedValue(self):
        """
        Set the current value of the variable to it's TTest "fixed" value.
        """
        self._current_value = self._fixed_value

    @property
    def current_value(self):
        return self._current_value

    @property
    def fixed_value(self):
        return self._fixed_value

    @property
    def vid(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def flags(self):
        return self._flags

    @property
    def is_input(self):
        return (self._flags & SCASS_FLAG_INPUT) > 0

    @property
    def is_output(self):
        return (self._flags & SCASS_FLAG_OUTPUT) > 0

    @property
    def is_randomisable(self):
        return (self._flags & SCASS_FLAG_RANDOMISE) > 0

    @property
    def is_ttest_variable(self):
        return (self._flags & SCASS_FLAG_TTEST_VAR) > 0

