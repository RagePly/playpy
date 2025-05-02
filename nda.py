from functools import singledispatchmethod
from operator import add

def product(ns):
    P = 1
    for n in ns: P *= n
    return P

class NDarray:
    def __init__(self, arr):
        self.dim = NDarray.shape(arr)
        self.size = product(self.dim)
        self.arr = arr

    def __len__(self):
        return self.size

    @singledispatchmethod
    def __getitem__(self, i): ...
    
    @__getitem__.register
    def _(self, idx: tuple):
        assert len(idx) == len(self.dim), "Dimension mismatch"
        el = self.arr
        for i in idx: el = el[i]
        return el

    @__getitem__.register
    def _(self, i: int):
        idx = []
        for ix in range(len(self.dim)):
            leap = product(self.dim[ix+1:])
            idx.append(i // leap)
            i = i % leap
        return self[*idx]

    def __add__(self, other):
        return NDarray.dispatch(self, other, add)

    def reshape(self, shape):
        return NDarray.with_shape(self, shape)

    @staticmethod
    def shape(arr):
        if not isinstance(arr, list):
            return tuple()
        return (len(arr), * NDarray.shape(arr[0])) 

    @staticmethod
    def with_shape(arr, shape):
        def _with_shape(g, shape):
            if not shape: return next(g)
            return [_with_shape(g, shape[1:]) for _ in range(shape[0])]
        return NDarray(_with_shape(iter(arr), shape))

    @staticmethod
    def dispatch(arr1, arr2, f):
        flat_res = []
        for id1, id2 in NDarray.expanded_dispatch_indices(arr1.dim, arr2.dim):
            l,r = arr1[id1], arr2[id2]
            flat_res.append(f(l,r))
        return NDarray.with_shape(flat_res, NDarray.expanded_shape(arr1.dim, arr2.dim))

    @staticmethod
    def expanded_dispatch_indices(shape1, shape2):
        assert len(shape1) == len(shape2), "Dimensionallity should match"

        def rdispatch(shape, shape1, shape2):
            if len(shape) == 0:
                yield tuple(), tuple()
            else:
                for i in range(shape[0]):
                    id1 = 0 if shape1[0] == 1 else i
                    id2 = 0 if shape2[0] == 1 else i
                    for ids1, ids2 in rdispatch(shape[1:], shape1[1:], shape2[1:]):
                        yield (id1, *ids1), (id2, *ids2)
        
        yield from rdispatch(NDarray.expanded_shape(shape1, shape2), shape1, shape2)

    @staticmethod
    def expanded_shape(shape1, shape2):
        assert len(shape1) == len(shape2), "Dimensionallity should match"
        if len(shape1) == 0:
            return tuple()
        elif shape1[0] == shape2[0] or shape2[0] == 1:
            return (shape1[0], *NDarray.expanded_shape(shape1[1:], shape2[1:]))
        elif shape1[0] == 1:
            return (shape2[0], *NDarray.expanded_shape(shape1[1:], shape2[1:]))
        assert False, "Dimension mismatch"


# Some tests
if __name__ == "__main__":
    # 4 * 2 * 3
    arr = [[[ 1, 2, 3], [ 4, 5, 6]],
           [[ 7, 8, 9], [10,11,12]],
           [[13,14,15], [16,17,18]],
           [[19,20,21], [22,23,24]]]
    nda = NDarray

    assert nda.shape(1) == tuple(), "A scalar has zero dimensions"
    assert nda(arr).dim == (4,2,3), "Dimensions for `arr` should be correct"
    assert nda(arr)[0, 1, 1] == 5, "Indexing should work"
    assert nda(arr)[22] == 23, "Flattened indexing should work"
    assert sum(nda(arr)) == 300, "Iteration should work"
    assert nda.with_shape([1,2,3,4], (2,2)).arr == [[1,2],[3,4]], "Shape building should work"
    assert nda([[1,2],[3,4],[5,6]]).reshape((2,3)).arr == [[1,2,3],[4,5,6]], "Reshaping should work"
    assert (nda([[1,2],[3,4]]) + nda([[4,3],[2,1]])).arr == [[5,5],[5,5]], "Dispatching should work"
    assert nda.expanded_shape((1,2), (2,1)) == (2,2), "Expanded shapes should be correct"
    assert (nda([1,2]).reshape((2,1)) + nda([1,2]).reshape((1,2))).arr == [[2, 3], [3, 4]], \
            "Dispatch on expanded nd-arrays should work"

