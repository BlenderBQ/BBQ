import random

class BaseFilter(object):
    """
    Keep a history of the added values and calcul the average and the standard
    deviation for filter based on it.
    """
    def __init__(self, size):
        super(BaseFilter, self).__init__()
        self.size = size
        self.hist = []
        self.sum = 0
        self.sq_sum = 0

    def empty(self):
        self.hist = []
        self.sum = 0
        self.sq_sum = 0

    def around(self, origin, distance):
        return abs(self.value - origin) <= distance

    @property
    def avg(self):
        if len(self.hist) == 0:
            return 0
        return self.sum * 1.0 / len(self.hist)

    @property
    def std(self):
        if len(self.hist) == 0:
            return 0
        return (self.sq_sum - self.sum) * 1.0 / len(self.hist)

    @property
    def derivative(self):
        if len(self.hist) == 0:
            return 0
        return (self.value - self.hist[0]) * 1.0 / 10

    @property
    def value(self):
        if not self.hist:
            return 0
        return self.hist[-1]

    def add_value(self, value):
        self.sum += value
        self.sq_sum += value ** 2
        self.hist += [value]

        if len(self.hist) > self.size:
            self.sum -= self.hist[0]
            self.sq_sum -= self.hist[0] ** 2
            self.hist = self.hist[1:]

class MixedFilter(object):
    """
    Decorate the *BaseFilter* class for using a list of different filters.
    When a value is added, the initial value is put inside the first filter of
    the list and then the filtered value is added in the second, ... to the
    last filter.
    """

    def __init__(self, filters):
        assert len(filters) != 0 # Happy JM ?
        self.filters = filters

    def empty(self):
        for f in self.filters:
            f.empty()

    def around(self, origin, distance):
        return self.filters[-1].around(origin, distance)

    @property
    def avg(self):
        return self.filters[-1].avg

    @property
    def std(self):
        return self.filters[-1].std

    @property
    def derivative(self):
        return self.filters[-1].derivative

    @property
    def value(self):
        return self.filters[-1].value

    def add_value(self, value):
        for f in self.filters:
            f.add_value(value)
            value = f.value

class LowpassFilter(BaseFilter):
    def __init__(self, alpha):
        BaseFilter.__init__(self, 2)
        self.alpha = alpha

    def add_value(self, value):
        """
        Add the new value in the history after applying a simple lowpass filter
        on it.
        The lowpass filter affects only the new and the last element. It does a
        ponderated average between them with a weight of *alpha*for the last
        value and *1 - alpha* for the new.
        """
        if len(self.hist) < 2:
            BaseFilter.add_value(self, value)
        else:
            filtered_value = self.hist[-1] * self.alpha + value * (1.0 - self.alpha)
            BaseFilter.add_value(self, filtered_value)

class NoiseFilter(BaseFilter):
    def __init__(self, deviation_scale, deviation_offset, size):
        BaseFilter.__init__(self, size)
        self.deviation_scale = deviation_scale
        self.deviation_offset = deviation_offset

    def add_value(self, value):
        """
        Add the new value in the history after applying a noise filter
        on it.
        Calculate the distance between the new value and the average. If this
        one is less than the squared standard deviation times *deviatin_scale*
        then the value is filtered and the current average is added instead.
        Else, the new value is added.
        """
        if (value - self.avg) ** 2 > \
                self.deviation_scale * (self.std + self.deviation_offset):
            BaseFilter.add_value(self, self.avg)
        else:
            BaseFilter.add_value(self, value)
