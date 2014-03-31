import random

class BaseFilter(object):
    """
    Keep a history of the added values and calcul the average and the standard
    deviation for filter based on it.
    """
    def __init__(self, size):
        super(Histo, self).__init__()
        self.size = size
        self.hist = []
        self.sum = 0
        self.sq_sum = 0

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

class LowpassFilter(BaseFilter):
    def __init__(self, alpha, size):
        BaseFilter.__init__(self, size)
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
            BaseFilter.add_value(value)
        else:
            filtered_value = self.hist[-1] * alpha + value * (1.0 - alpha)
            BaseFilter.add_value(filtered_value)

class NoiseFilter(BaseFilter):
    def __init__(self, deviation_scale, size):
        BaseFilter.__init__(self, size)
        self.deviation_scale = deviation_scale

    def add_value(self, value):
        """
        Add the new value in the history after applying a noise filter
        on it.
        Calculate the distance between the new value and the average. If this
        one is less than the squared standard deviation times *deviatin_scale*
        then the value is filtered and the current average is added instead.
        Else, the new value is added.
        """
        if (value - self.avg) ** 2 > self.deviation_scale * self.std:
            BaseFilter.add_value(self.avg)
        else:
            BaseFilter.add_value(value)

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

    @property
    def avg(self):
        return self.filters[-1].avg

    @property
    def std(self):
        return self.filters[-1].std

    @property
    def value(self):
        return self.filters[-1].value

    def add_value(self, value):
        for f in self.filters:
            value = f.add_value(value)

class Filter(object):
    """
    Automatic filtering based on history: if there's not enough change, no need
    to send the command.
    TODO actually, you do need to send the command.
    """

    def __init__(self, window_length=5, threshold=0.01):
        super(Filter, self).__init__()
        self.window_length = window_length
        self.threshold = threshold # Need at least x % change in value to be interesting
        self.history = []

    def apply(self, new_value):
        """
        Determine if this new value should be sent.
        Compute the mean value over a number of past values.
        If the change is significant, return this mean value, otherwise return None.
        """
        if len(self.history) < 2:
            self.history.append(new_value)
            return new_value, True

        # compute previous mean
        mean = 0.
        for i in xrange(self.window_length - 1):
            index = max(0, len(self.history) - i - 1)
            mean += self.history[index]
        previous = mean / float(self.window_length - 1)

        self.history.append(new_value)
        if len(self.history) > self.window_length:
            self.history = self.history[-self.window_length:]
        mean = (mean + new_value) / self.window_length

        value = abs(mean - previous)
        if previous != 0:
            value /= previous
        interesting = (value > self.threshold)
        return mean, interesting

class CompositeFilter(object):
    """Compose N Filter objects to filter N dimensional data"""

    def __init__(self, n):
        super(CompositeFilter, self).__init__()
        self.n = n
        self.filters = [Filter() for _ in xrange(n)]

    def apply(self, new_value):
        """
        new_value is expected to be n dimensional.
        If at least one dimension has changed enough, the whole vector is considered interesting.
        """
        result = []
        interesting = False
        for i in xrange(self.n):
            (r, valid) = self.filters[i].apply(new_value[i])
            result.append(r)
            if valid:
                interesting = True

        return result, interesting

if __name__ == '__main__':
    leFilter = CompositeFilter(3)
    for i in xrange(1, 10):
        r = [random.random(), random.random(), random.random()]
        result, interesting = leFilter.apply(r)
        #print(result, interesting)
