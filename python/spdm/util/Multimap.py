# https://code.activestate.com/recipes/577197-sortedcollection/
import collections
import pprint
from bisect import bisect_left, bisect_right

# from .logger import logger


class Multimap(object):
    '''
    Python equivalent of C++ stl::Multimap

     "Multimap is an associative container that contains a sorted list of key-value pairs,
     while permitting multiple entries with the same key. Sorting is done according to
     the comparison function Compare, applied to the keys. Search, insertion, and removal
     operations have logarithmic complexity." -- https://en.cppreference.com/w/cpp/container/multimap


    * Member classes
        value_compare   compares objects of type value_type  [not implemented]
    * Member functions
        (constructor)   constructs the map
        (destructor)    destructs the map
        operator=       assigns values to the container   [not implemented]
        get_allocator   returns the associated allocator  [not implemented]

    * Iterators
        begin,cbegin    returns an iterator to the beginning   [__iter__]
        end,cend        returns an iterator to the end
        rbegin,crbegin  returns a reverse iterator to the beginning
        rend,crend      returns a reverse iterator to the end
    * Capacity
        empty           checks whether the container is empty
        size            returns the number of elements  [__len__]
        max_size        returns the maximum possible number of elements
    * Modifiers
        clear           clears the contents
        insert          inserts elements or nodes (since C++17)  [__setitem__]
        emplace         (C++11) constructs element in-place  [not implemented]
        emplace_hint    (C++11) constructs elements in-place using a hint  [not implemented]
        try_emplace     (C++17) inserts in-place if the key does not exist, does nothing if the key exists [not implemented]
        erase           erases elements [__delitem__]
        swap            swaps the contents [not implemented]
        extract         (C++17) extracts nodes from the container [not implemented]
        merge           (C++17) splices nodes from another container [not implemented]
    * Lookup
        count           returns the number of elements matching specific key
        find            finds element with specific key
        contains        checks if the container contains element with specific key  [__contains__]
        equal_range     returns range of elements matching a specific key
        lower_bound     returns an iterator to the first element not less than the given key
        upper_bound     returns an iterator to the first element greater than the given key
    * Observers
        key_comp        returns the function that compares keys [not implemented]
        value_comp      returns the function that compares keys in objects of type value_type [not implemented]
    * Non-member functions
        operator==      lexicographically compares the values in the map [not implemented]
        operator!=
        operator<
        operator<=
        operator>
        operator>=

        std::swap(std::Multimap) specializes the std::swap algorithm (function template)  [not implemented]
        erase_if(std::map)  (C++20) Erases all elements satisfying specific criteria (function template)
    
    '''

    def __init__(self, data=None, key=None, ** kwargs):
        self._key = key or (lambda x: x[0])
        self._keys = []
        self._items = []
        self.insert(data)

    # Capacity
    def __repr__(self):
        return pprint.pformat(self._items)

    def __str__(self):
        return pprint.pformat(self._items)

    def empty(self) -> bool:
        return self.size() == 0

    def size(self) -> int:
        return len(self._items)

    def __len__(self):
        return self.size()

    def items(self):
        return self._items

    def values(self):
        return self._items

    def keys(self):
        return self._keys

    # Modifiers

    def clear(self):
        self.__init__([], self._key)

    def insert_many(self, kvs, before=True):
        if before:
            op = self.insert_before
        else:
            op = self.insert_after
        if isinstance(kvs, collections.abc.Mapping):
            self.insert_many(kvs.items(), before)
        else:
            for kv in kvs:
                op(kv)
        # else:
        #     raise TypeError(f"illegal argument type! {type(kvs)}")

    def insert_before(self, kv):
        'Insert a new item.  If equal keys are found, add to the left'
        k = self._key(kv)
        i = bisect_left(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, kv)

    def insert_after(self, kv):
        'Insert a new item.  If equal keys are found, add to the right'
        k = self._key(kv)
        i = bisect_right(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, kv)

    def insert(self, kv, before=False):
        if kv is None:
            return
        if before:
            op = self.insert_before
        else:
            op = self.insert_after
        op(kv)

    def remove(self, arg0, arg1=None):
        raise NotImplementedError("erase")

    # Lookup
    def count(self, k):
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return j - i

    def contains(self, k):
        return self.count(k) > 0

    def __contains__(self, k):
        return self.count(k) > 0

    def find(self, k):
        idx = bisect_left(self._keys, k)
        if idx < len(self._keys) and self._keys[idx] == k:
            return self._items[idx]
        else:
            return None

    def find_lower(self, key):
        return self[:self.upper_bound(key)]

    def find_upper(self, key):
        return self[self.lower_bound(key):]

    # class Iterator(collections.abc.Iterator,  collections.abc.ItemsView):
    #     def __init__(self, container, start, end=None, step=1):
    #         self._container = container
    #         self._max = len(self._container)
    #         self._min = 0
    #         self._start = start
    #         self._end = end
    #         self._reverse = reverse
    #         self._it = self._end if self._reverse else self._start

    #     def reverse(self):
    #         return Multimap.Iterator(self._container, self._start, self._end, not self._reverse)

    #     def __iter__(self):
    #         return self

    #     def __next__(self):
    #         if self._reverse and (self._it >= self._start):
    #             self._it = self._it - 1
    #             return self._container[self._it]
    #         elif (not self._reverse) and self._it < self._end:
    #             idx = self._it
    #             self._it = self._it + 1
    #             return self._container[idx]
    #         else:
    #             raise StopIteration()

    #     def __contains__(self, k):
    #         idx = bisect_left(self._container._keys, k,
    #                           self._start, self._end)
    #         return idx >= self._start and idx < self._end

    def lower_bound(self, k):
        '''bisec_left: The return value i is such that all e in a[:i] have e < x,
         and all e in a[i:] have e >= x. So if x already appears in the list,
          i points just before the leftmost x already there.'''
        return bisect_left(self._keys, k)

    def upper_bound(self, k):
        '''bisect_right: The return value i is such that all e in a[:i] have e <= x, and all e in a[i:]
         have e > x. So if x already appears in the list, i points just beyond the rightmost x already there
        '''
        return bisect_right(self._keys, k)

    def equal_range(self, k):
        '''returns all elements that key == k'''
        lo = bisect_left(self._keys, k)
        hi = bisect_right(self._keys, k)

        return self._items[lo:hi]

    def reverse_equal_range(self, k):
        '''returns all elements that key == k'''
        lo = bisect_left(self._keys, k)
        hi = bisect_right(self._keys, k)

        return self._items[hi:lo][::-1]

    def lower_range(self, k):
        '''returns all elements that key < k'''
        return self._items[:bisect_left(self._keys, k)]

    def upper_range(self, k):
        '''returns all elements that key > k'''
        return self._items[:bisect_right(self._keys, k)]

    def range(self, k_lo, k_hi):
        '''returns all elements that  k_lo<= key < k_hi'''

        lo = bisect_left(self._keys, k_lo)
        hi = bisect_left(self._keys, k_hi)

        return self._items[lo:hi]

    ###############################################

    def copy(self):
        return self.__class__(self, self._key)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    # def __repr__(self):
    #     return f"{self.__class__.__name__}({pprint.pformat(self._items)}, key={ getattr(self._key, '__name__', repr(self._key))})"

    # def __str__(self):
    #     return f"{self.__class__.__name__}({pprint.pformat(self._items)}, key={ getattr(self._key, '__name__', repr(self._key))})"
