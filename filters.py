import random

class Filter(object):
    """Automatic filtering based on history: if there's not enough change, no need to send the command"""

    def __init__(self, window_length=5, threshold=0.01):
        super(Filter, self).__init__()
        self.window_length = window_length
        self.threshold = threshold # Need at least 1% change in value to be interesting
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

        value = abs(mean - previous) / previous
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
        print(result, interesting)
