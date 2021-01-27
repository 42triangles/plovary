# General notes:
# * Real keys are actual keys in the system
# * Pseudo keys are groups of keys, any real key is also a valid pseudo key
# * By default, "key" refers to (to make usage easier & shorter):
#    * in input position: A pseudo key
#    * in output position: A real key

import sys
from typing import *
from enum import Enum
from itertools import chain


__all__ = [
    "System",
    "Chord",
    "to_multi_chord", "to_plover_str",
    "add", "sub", "prefix", "suffix", "surround", "concat",
    "reverse_concat",
    "Dictionary",
    "EnglishSystem", "EnglishChord", "system",
    "digit_keys", "digits",
    "single_digit_only", "double_digit_only", "hundred00",
    "double_digit_only_hundred00", "hundred1z",
    "double_digit_only_hundred1z", "single_and_double_digit",
    "single_and_double_digit_hundred00",
    "single_and_double_digit_hundred1z", "hundreds", "numbers",
    "fingertyping_lowercase_no_asterisk",
    "fingertyping_uppercase_no_p_no_asterisk",
    "fingertyping_uppercase_p_no_asterisk",
    "fingertyping_no_asterisk", "fingertyping_lowercase",
    "fingertyping_uppercase_no_p", "fingertyping_uppercase_p",
    "fingertyping",
]


write_warnings: bool = True  # Set this to false to disable warnings on stderr


def warn(s: str) -> None:
    if write_warnings:
        print("WARNING: " + s, file=sys.stderr)


T = TypeVar("T")


def unwrap_optional_or(a: Optional[T], b: T) -> T:
    return a if a is not None else b


def sliding_window(
    iterable: Iterable[T],
    *,
    size: int
) -> Generator[Tuple[T, ...], None, None]:
    out: Tuple[T, ...] = ()
    for i in iterable:
        out += (i,)
        if len(out) == size:
            yield out
            out = out[1:]


# `int` for now since the normal `typing` module doesn't provide a type for
# something that can be compared
def is_sorted(iterable: Iterable[int]) -> bool:
    return all(a <= b for a, b in sliding_window(iterable, size=2))


SystemT = TypeVar("SystemT", bound='System')


class System(object):
    sys_name: ClassVar[Optional[str]] = None
    sys_key_order: ClassVar[List[str]]
    sys_unordered_keys: ClassVar[List[str]] = []
    sys_combining_keys: ClassVar[List[str]] = []
    sys_optional_replacements: ClassVar[Dict[str, List[str]]] = {}
    sys_mandatory_replacements: ClassVar[Dict[str, List[str]]] = {}

    name: Optional[str]

    key_order: List[str]  # Includes a hyphen!
    all_keys: List[str]

    left_keys: List[str]
    left_middle_keys: List[str]
    middle_keys: List[str]
    right_middle_keys: List[str]
    right_keys: List[str]

    unordered_keys: List[str]
    combining_keys: List[str]

    # Optional replacements are only parsed, not emitted in outputs. This is
    # to allow users to use "pseudo steno" to write out their chords.
    optional_replacements: Dict[str, List[str]]
    # Mandatory replacements are not only parsed, but also emitted in outputs.
    # Their order is depending on that of their first ordered key.
    # Not that hyphen emitting is decided based on the base keys; as such this
    # can act as a middle key when emitted if it contains a middle key, but it
    # *cannot* act as such by only having keys on both sides.
    mandatory_replacements: Dict[str, List[str]]

    left_pseudo_keys: List[str]
    left_middle_pseudo_keys: List[str]
    middle_pseudo_keys: List[str]
    right_middle_pseudo_keys: List[str]
    right_pseudo_keys: List[str]
    pseudo_key_order: List[str]

    _empty_chord: 'Chord[Any]'

    def __init__(self,
        key_order: Optional[List[str]]=None,
        *,
        name: Optional[str]=None,
        unordered_keys: Optional[List[str]]=None,
        combining_keys: Optional[List[str]]=None,
        optional_replacements: Optional[Dict[str, List[str]]]=None,
        mandatory_replacements: Optional[Dict[str, List[str]]]=None,
    ) -> None:
        self.name = unwrap_optional_or(name, self.sys_name)
        self.key_order = unwrap_optional_or(key_order, self.sys_key_order)
        self.all_keys = [i for i in self.key_order if i != "-"]
        self.unordered_keys = (
            unwrap_optional_or(unordered_keys, self.sys_unordered_keys)
        )
        self.combining_keys = (
            unwrap_optional_or(combining_keys, self.sys_combining_keys)
        )
        self.optional_replacements = unwrap_optional_or(
            optional_replacements,
            self.sys_optional_replacements
        )
        self.mandatory_replacements = unwrap_optional_or(
            mandatory_replacements,
            self.sys_mandatory_replacements
        )

        self.left_keys = [i for i in self.all_keys if i.endswith("-")]
        self.right_keys = [i for i in self.all_keys if i.startswith("-")]
        middle_keys_and_hyphen = [
            i
            for i in self.key_order
            if "-" not in i or i == "-" and i not in self.unordered_keys
        ]
        hyphen_idx = middle_keys_and_hyphen.index("-")
        self.left_middle_keys = middle_keys_and_hyphen[:hyphen_idx]
        self.right_middle_keys = middle_keys_and_hyphen[hyphen_idx + 1:]
        self.middle_keys = self.left_middle_keys + self.right_middle_keys

        for i in (self.optional_replacements, self.mandatory_replacements):
            for j in i.values():
                self.assert_real_keys_ordered(*j)

        replacements = [
            i
            for i in list(self.optional_replacements.keys()) +
                list(self.mandatory_replacements.keys())
            if not self.key_unordered(i)
        ]

        def pseudo_keys_where(
            base: List[str],
            predicate: Callable[[str], bool]
        ) -> List[str]:
            out = base + [i for i in replacements if predicate(i)]
            out.sort(key=self.key_index)
            return out

        self.left_pseudo_keys = pseudo_keys_where(
            self.left_keys,
            lambda i: i.endswith("-")
        )
        self.left_middle_pseudo_keys = pseudo_keys_where(
            self.left_middle_keys,
            lambda i:
                "-" not in i and any(j in self.left_middle_keys for j in i)
        )
        self.right_middle_pseudo_keys = pseudo_keys_where(
            self.right_middle_keys,
            lambda i:
                "-" not in i and not any(j in self.left_middle_keys for j in i)
        )
        self.middle_pseudo_keys = (
            self.left_middle_pseudo_keys + self.right_middle_pseudo_keys
        )
        self.right_pseudo_keys = pseudo_keys_where(
            self.right_keys,
            lambda i: i.startswith("-")
        )
        self.pseudo_key_order = (
            self.left_pseudo_keys + self.middle_pseudo_keys +
            self.right_pseudo_keys
        )

        self._empty_chord = self.chord()

    def assert_real_key(self, *keys: str) -> None:
        for key in keys:
            if key not in self.all_keys:
                raise ValueError(f"{key!r} is not a key in {self!r}")

    def real_key_index(self, key: str) -> int:
        self.assert_real_key(key)
        return self.key_order.index(key)

    def real_keys_ordered(
        self,
        *keys: str,
        ignore_unordered: bool=False
    ) -> bool:
        """
        Returns `True` if the arguments are all in steno order.
        Being the same key counts as being in order.
        """
        self.assert_real_key(*keys)
        if not ignore_unordered:
            keys = tuple(i for i in keys if i not in self.unordered_keys)
        return is_sorted(map(self.real_key_index, keys))

    def assert_real_keys_ordered(
        self,
        *keys: str,
        ignore_unordered: bool=False
    ) -> None:
        if not self.real_keys_ordered(*keys, ignore_unordered=ignore_unordered):
            raise ValueError(
                f"{', '.join(repr(i) for i in keys)} are not in steno order " +
                f"in {self!r}"
            )

    def assert_key(self, *keys: str) -> None:
        for key in keys:
            is_real_key = key in self.all_keys 
            is_pseudo_key = (
                key in self.optional_replacements or
                key in self.mandatory_replacements
            )
            if not is_real_key and not is_pseudo_key:
                raise ValueError(
                    f"{key!r} is not a valid pseudo key in {self!r}"
                )

    def expand_key(self, key: str) -> List[str]:
        self.assert_key(key)
        if key in self.all_keys:
            return [key]
        elif key in self.optional_replacements:
            return self.optional_replacements[key]
        else:
            return self.mandatory_replacements[key]

    def key_unordered(self, key: str) -> bool:
        return all(
            i in self.unordered_keys
            for i in self.expand_key(key)
        )

    def key_index(self, key: str) -> int:
        for i in self.expand_key(key):
            if i not in self.unordered_keys:
                return self.real_key_index(i)
        return self.real_key_index(self.expand_key(key)[0])

    def keys_ordered(self, *keys: str, ignore_unordered: bool=False) -> bool:
        self.assert_key(*keys)
        if not ignore_unordered:
            keys = tuple(i for i in keys if not self.key_unordered(i))
        return is_sorted(map(self.key_index, keys))

    def chord_of_real_keys(
        self: SystemT,
        keys: Iterable[str]
    ) -> 'Chord[SystemT]':
        return Chord(self, keys)

    def chord(self: SystemT, *keys: str) -> 'Chord[SystemT]':
        return self.chord_of_real_keys(
            chain.from_iterable(self.expand_key(i) for i in keys)
        )

    # This is only a property to make it properly typeable :)
    @property
    def empty_chord(self: SystemT) -> 'Chord[SystemT]':
        return self._empty_chord

    def single_real_key(self: SystemT, key: str) -> 'Chord[SystemT]':
        return self.chord(key)

    def single_key(self: SystemT, key: str) -> 'Chord[SystemT]':
        return self.chord(*self.expand_key(key))

    def parse(self: SystemT, chord: str) -> 'Chord[SystemT]':
        left = chord
        out: List[str] = []

        def try_consume_one(pseudo_key: str) -> bool:
            nonlocal left
            nonlocal out

            without_hyphen = pseudo_key.replace("-", "")
            if left.startswith(without_hyphen):
                left = left[len(without_hyphen):]
                out += self.expand_key(pseudo_key)
                return True
            else:
                return False

        all_unordered = (
            self.unordered_keys +
            [
                i
                for i in list(self.optional_replacements.keys()) +
                    list(self.mandatory_replacements.keys())
                if self.key_unordered(i)
            ]
        )

        def try_consume_unordered() -> None:
            while True:
                done = True
                for i in all_unordered:
                    if try_consume_one(i):
                        done = False
                if done:
                    return

        def try_consume_all(keys: List[str]) -> None:
            for i in keys:
                try_consume_unordered()
                try_consume_one(i)

        try_consume_all(self.left_pseudo_keys + self.left_middle_pseudo_keys)
        try_consume_unordered()

        if left.startswith("-"):
            left = left[len("-"):]

        try_consume_all(self.right_middle_pseudo_keys + self.right_pseudo_keys)
        try_consume_unordered()

        as_set = frozenset(out)

        # If this is `True`, the chord wasn't valid. In this case `left` could
        # already be empty though; for example `F` would be parsed to `-F`,
        # even though it's not valid due to the missing hyphen - this is what
        # we detect here.
        hyphen_maybe_missing = (
            "-" not in chord and  # there is no hyphen
            not as_set & set(self.middle_keys) and  # there are no middle keys
            as_set & set(self.right_keys)  # but there *are* right keys
        )

        if hyphen_maybe_missing or left != "":
            info = (
                " (it may be missing a hyphen)" if hyphen_maybe_missing else ""
            )
            raise ValueError(
                f"The chord {chord!r} is not valid{info} in {self!r}"
            )

        if not self.real_keys_ordered(*out):
            warn(
                f"Some pseudo keys might not be in steno order in {chord!r} " +
                f"in {self!r}"
            )

        return self.chord(*out)
    
    def parse_many(
        self: SystemT,
        sequence: str
    ) -> Tuple['Chord[SystemT]', ...]:
        return tuple(self.parse(i) for i in sequence.split("/"))

    def parsed_single_dict(
        self: SystemT,
        dict_: Dict[str, T]
    ) -> 'Dictionary[Chord[SystemT], T]':
        return Dictionary((self.parse(k), v) for k, v in dict_.items())

    def parsed_seq_dict(
        self: SystemT,
        dict_: Dict[str, T]
    ) -> 'Dictionary[Tuple[Chord[SystemT], ...], T]':
        return Dictionary((self.parse_many(k), v) for k, v in dict_.items())

    @overload
    def toggle(
        self: SystemT, key: Union[str, 'Chord[SystemT]'],
        value: T,
        *,
        default: T
    ) -> 'Dictionary[Chord[SystemT], T]': ...
    @overload
    def toggle(
        self: SystemT,
        key: Union[str, 'Chord[SystemT]'],
        value: str,
        *,
        default: str=""
    ) -> 'Dictionary[Chord[SystemT], str]': ...
    def toggle(
        self: SystemT,
        key: Union[str, 'Chord[SystemT]'],
        value: T,
        *,
        default: Any=""
    ) -> 'Dictionary[Chord[SystemT], T]':
        as_chord = (
            key if isinstance(key, Chord) else self.parse(key)
        )
        return Dictionary({
            as_chord: value,
            self.empty_chord: default,
        })

    def __repr__(self) -> str:
        if self.name is not None:
            return f"System(name={self.name!r})"
        else:
            return (
                f"System({self.key_order!r}, " +
                "unordered_keys={self.unordered_keys!r}, " + 
                "optional_replacements={self.optional_replacements!r}, " + 
                "mandatory_replacements={self.mandatory_replacements!r})"
            )


class Chord(Generic[SystemT]):
    def __init__(self, system: SystemT, keys: Iterable[str]) -> None:
        self.system: Final[SystemT] = system
        self.keys: Final[FrozenSet[str]] = frozenset(keys)
        self.system.assert_real_key(*self.keys)

    @property
    def left_keys(self) -> FrozenSet[str]:
        return self.keys & set(self.system.left_keys)

    @property
    def left_middle_keys(self) -> FrozenSet[str]:
        return self.keys & set(self.system.left_middle_keys)

    @property
    def middle_keys(self) -> FrozenSet[str]:
        return self.keys & set(self.system.middle_keys)

    @property
    def right_middle_keys(self) -> FrozenSet[str]:
        return self.keys & set(self.system.right_middle_keys)

    @property
    def right_keys(self) -> FrozenSet[str]:
        return self.keys & set(self.system.right_keys)

    def _to_str(self, replacements: Mapping[str, List[str]]={}) -> str:
        matching_replacements = [
            (k, v)
            for k, v in replacements.items()
            if set(v) <= self.keys
        ]

        outputs = (
            [k for k, _ in matching_replacements] +
            [
                i
                for i in self.keys
                if not any(i in j for _, j in matching_replacements)
            ]
        )

        needs_dash = (
            (self.keys & set(self.system.right_keys)) and
            not (self.keys & set(self.system.middle_keys))
        )
        if needs_dash:
            outputs.append("-")

        outputs.sort(
            key=lambda x:
                self.system.key_index(x)
                if x != "-"
                else self.system.key_order.index("-")
        )

        return "".join("-" if i == "-" else i.replace("-", "") for i in outputs)

    def assert_same_system(self, other: 'Chord[SystemT]') -> None:
        if self.system is not other.system:
            raise ValueError(
                f"{self!r} and {other!r} are not from the same system"
            )

    def to_multi_chord(self) -> Tuple['Chord[SystemT]', ...]:
        return (self,)

    def overlaps(self, other: 'Chord[SystemT]') -> bool:
        self.assert_same_system(other)
        return bool(self.keys & other.keys)

    def overlaps_noncombining(self, other: 'Chord[SystemT]') -> bool:
        self.assert_same_system(other)
        return bool(self.keys & other.keys - set(self.system.combining_keys))

    def assert_no_overlapping_noncombining(
        self,
        other: 'Chord[SystemT]'
    ) -> None:
        if self.overlaps_noncombining(other):
            raise ValueError(f"{self!r} and {other!r} overlap")

    def is_superset(self, other: 'Chord[SystemT]') -> bool:
        self.assert_same_system(other)
        return self.keys >= other.keys

    def assert_is_superset(self, other: 'Chord[SystemT]') -> None:
        if not self.is_superset(other):
            raise ValueError(f"{self!r} is not a superset of {other!r}")

    def mask(self, other: 'Chord[SystemT]') -> 'Chord[SystemT]':
        return self.system.chord(*(self.keys & other.keys))

    def lax_combine(self, other: 'Chord[SystemT]') -> 'Chord[SystemT]':
        self.assert_same_system(other)
        return self.system.chord(*(self.keys | other.keys))

    def combine(self, other: 'Chord[SystemT]') -> 'Chord[SystemT]':
        self.assert_no_overlapping_noncombining(other)
        return self.lax_combine(other)

    def lax_remove(self, other: 'Chord[SystemT]') -> 'Chord[SystemT]':
        self.assert_same_system(other)
        return self.system.chord(*(self.keys - other.keys))

    def remove(self, other: 'Chord[SystemT]') -> 'Chord[SystemT]':
        self.assert_is_superset(other)
        return self.lax_remove(other)

    @property
    def plover_str(self) -> str:
        return self._to_str(self.system.mandatory_replacements)

    def __repr__(self) -> str:
        return f"Chord({self.system!r}, {self})"

    def __str__(self) -> str:
        return self._to_str()

    def __contains__(self, item: Union['Chord[SystemT]', str]) -> bool:
        if isinstance(item, str):
            self.system.assert_key(item)
            return set(self.system.expand_key(item)) <= self.keys
        else:
            return item.keys <= self.keys

    def __len__(self) -> int:
        return len(self.keys)

    def __add__(self, other: Union['Chord[SystemT]', str]) -> 'Chord[SystemT]':
        if isinstance(other, str):
            return self + self.system.parse(other)
        elif isinstance(other, Chord):
            return self.combine(other)
        else:
            return NotImplemented

    def __radd__(self, other: Union['Chord[SystemT]', str]) -> 'Chord[SystemT]':
        return self.__add__(other)

    def __sub__(self, other: Union['Chord[SystemT]', str]) -> 'Chord[SystemT]':
        if isinstance(other, str):
            return self - self.system.parse(other)
        elif isinstance(other, Chord):
            return self.remove(other)
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash((id(self.system), self.keys))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Chord):
            return self.keys == other.keys
        else:
            return NotImplemented

    def __ne__(self, other: object) -> bool:
        return not (self == other)


def to_multi_chord(
    value: Union[Chord[SystemT], Tuple[Chord[SystemT], ...]]
) -> Tuple[Chord[SystemT], ...]:
    return value if isinstance(value, tuple) else (value,)


def to_plover_str(
    value: Union[Chord[SystemT], Tuple[Chord[SystemT], ...]]
) -> str:
    return "/".join(i.plover_str for i in to_multi_chord(value))


def add(
    chord: Union[Chord[SystemT], str]
) -> Callable[[Chord[SystemT]], Chord[SystemT]]:
    return lambda x: chord + x


def sub(
    chord: Union[Chord[SystemT], str]
) -> Callable[[Chord[SystemT]], Chord[SystemT]]:
    return lambda x: x - chord


@overload
def prefix(
    prefix: Chord[SystemT]
) -> Callable[[Chord[SystemT]], Chord[SystemT]]: ...
@overload
def prefix(prefix: str) -> Callable[[str], str]: ...
def prefix(prefix: Union[Chord[SystemT], str]) -> Callable[[Any], Any]:
    return lambda r: prefix + r


@overload
def suffix(
    suffix: Chord[SystemT]
) -> Callable[[Chord[SystemT]], Chord[SystemT]]: ...
@overload
def suffix(suffix: str) -> Callable[[str], str]: ...
def suffix(suffix: Union[Chord[SystemT], str]) -> Callable[[Any], Any]:
    return lambda l: l + suffix


@overload
def surround(
    prefix: Chord[SystemT],
    suffix: Chord[SystemT]
) -> Callable[[Chord[SystemT]], Chord[SystemT]]: ...
@overload
def surround(prefix: str, suffix: str) -> Callable[[str], str]: ...
def surround(
    prefix: Union[Chord[SystemT], str],
    suffix: Union[Chord[SystemT], str]
) -> Callable[[Any], Any]:
    return lambda x: prefix + x + suffix


@overload
def concat(
    left: Union[Chord[SystemT], Tuple[Chord[SystemT], ...]],
    right: Union[Chord[SystemT], Tuple[Chord[SystemT], ...]],
    *,
    middle: Optional[Union[Chord[SystemT], Tuple[Chord[SystemT], ...]]]=None,
) -> Tuple[Chord[SystemT], ...]: ...
@overload
def concat(left: str, right: str, *, middle: Optional[str]=None) -> str: ...
def concat(
    left: Union[Chord[SystemT], Tuple[Chord[SystemT], ...], str],
    right: Union[Chord[SystemT], Tuple[Chord[SystemT], ...], str],
    *,
    middle: Optional[
        Union[Chord[SystemT], Tuple[Chord[SystemT], ...], str]
    ]=None,
) -> Union[Tuple[Chord[SystemT], ...], str]:
    if isinstance(left, str):
        assert isinstance(right, str)
        assert middle is None or isinstance(middle, str)
        return left + (middle if middle is not None else "") + right
    else:
        assert isinstance(left, Chord) or isinstance(left, tuple)
        assert isinstance(right, Chord) or isinstance(right, tuple)
        assert middle is None or isinstance(middle, Chord) or isinstance(middle, tuple)
        if middle is not None:
            return (
                to_multi_chord(left) +
                to_multi_chord(middle) +
                to_multi_chord(right)
            )
        else:
            return to_multi_chord(left) + to_multi_chord(right)


def to_tuple(left: T, right: T) -> Tuple[T, T]:
    return (left, right)


@overload
def reverse_concat(
    right: Union[Chord[SystemT], Tuple[Chord[SystemT], ...]],
    left: Union[Chord[SystemT], Tuple[Chord[SystemT], ...]],
    *,
    middle: Optional[Union[Chord[SystemT], Tuple[Chord[SystemT], ...]]]=None,
) -> Tuple[Chord[SystemT], ...]: ...
@overload
def reverse_concat(right: str, left: str, *, middle: Optional[str]=None) -> str:
    ...
def reverse_concat(right: Any, left: Any, *, middle: Optional[Any]=None) -> Any:
    return concat(left, right, middle=middle)


def _is_chord_in_single_element_tuple(key: object) -> bool:
    return (
        isinstance(key, tuple) and len(key) == 1 and
        isinstance(key[0], Chord)
    )


K = TypeVar("K")
V = TypeVar("V")
K2 = TypeVar("K2")
V2 = TypeVar("V2")
K3 = TypeVar("K3")
V3 = TypeVar("V3")


class Dictionary(Generic[K, V]):
    def __init__(
        self,
        iterable_or_dict: Union[Iterable[Tuple[K, V]], Dict[K, V]]
    ) -> None:
        self.dict: Dict[K, V]

        if isinstance(iterable_or_dict, dict):
            self.dict = iterable_or_dict
        else:
            self.dict = {}
            for k, v in iterable_or_dict:
                if k in self.dict:
                    warn(
                        f"The key {k!r} is present more than once in " +
                        f"{self.dict!r}"
                    )

                self.dict[k] = v

    def copy(self) -> 'Dictionary[K, V]':
        return Dictionary(self.dict.items())

    def keys(self) -> Iterable[K]:
        return self.dict.keys()

    def values(self) -> Iterable[V]:
        return self.dict.values()

    def keys_for(self, value: V) -> List[K]:
        return [k for k, v in self.dict.items() if v == value]

    @overload
    def with_empty_chord(
        self: 'Dictionary[Chord[SystemT], V]',
        default: V,
        *,
        system: Optional[SystemT]=None,
    ) -> 'Dictionary[Chord[SystemT], V]': ...
    @overload
    def with_empty_chord(
        self: 'Dictionary[Chord[SystemT], str]',
        default: str="",
        *,
        system: Optional[SystemT]=None,
    ) -> 'Dictionary[Chord[SystemT], V]': ...
    def with_empty_chord(
        self: 'Dictionary[Chord[SystemT], V]',
        default: Any="",
        *,
        system: Optional[SystemT]=None,
    ) -> 'Dictionary[Chord[SystemT], V]':
        """
        Limitation: the dictionary cannot be empty, otherwise
        the system cannot be inferred
        """
        inferred_system: SystemT
        if system is not None:
            inferred_system = system
        else:
            try:
                inferred_system = next(
                    i.system
                    for i in self.keys()
                )
            except StopIteration:
                raise ValueError(
                    "Cannot infer the system of an empty " +
                    "dictionary"
                )
        return self + Dictionary({
            inferred_system.empty_chord: default
        })

    # Suggested key maps:
    # * `Chord.to_multi_chord` / `to_multi_chord`
    # * `chord.combine` / `add(chord)` / `add(key)`
    # * `sub(chord)` (removes `chord` from all entries) / `sub(key)`
    # * `prefix(chords)`
    # * `suffix(chords)`
    # * `surround(prefix_chords, suffix_chords)`
    # Suggested value maps:
    # * `prefix(s)`
    # * `suffix(s)`
    # * `surround(prefix_s, suffix_s)`
    @overload
    def map(self) -> 'Dictionary[K, V]': ...
    @overload
    def map(self, *, keys: Callable[[K], K2]) -> 'Dictionary[K2, V]': ...
    @overload
    def map(self, *, values: Callable[[V], V2]) -> 'Dictionary[K, V2]': ...
    @overload
    def map(
        self,
        *,
        keys: Callable[[K], K2],
        values: Callable[[V], V2]
    ) -> 'Dictionary[K2, V2]': ...
    def map(
        self,
        *,
        keys: Callable[[K], Any]=lambda x: x,
        values: Callable[[V], Any]=lambda x: x
    ) -> 'Dictionary[K2, V2]':
        typed_keys: Callable[[K], K2] = keys
        typed_values: Callable[[V], V2] = values
        return Dictionary((typed_keys(k), typed_values(v)) for k, v in self)

    def to_multi_chords(
        self: 'Dictionary[Chord[SystemT], V]'
    ) -> 'Dictionary[Tuple[Chord[SystemT], ...], V]':
        return self.map(keys=Chord.to_multi_chord)

    # Suggested key combiners:
    # * `Chord.combine` (default) for single chords
    # * `concat` for chord tuples
    #   (treats chords as chord tuples with one element)
    # * `to_tuple`
    # Suggested value combiners:
    # * `concat` (default)
    # * `to_tuple`
    @overload
    def combinations(
        self,
        other: 'Dictionary[K2, V2]',
        *,
        keys: Callable[[K, K2], K3],
        values: Callable[[V, V2], V3],
    ) -> 'Dictionary[K3, V3]': ...
    @overload
    def combinations(
        self: 'Dictionary[Chord[SystemT], V]',
        other: 'Dictionary[Chord[SystemT], V2]',
        *,
        # keys = Chord.combine
        values: Callable[[V, V2], V3],
    ) -> 'Dictionary[Chord[SystemT], V3]': ...
    # We *could* also allow chords and the like on the right side by default
    # here, but that is seldom used, and as such I think requiring the user to
    # explicitly use `keys=concat` is not a big deal, *especially* since this
    # would otherwise require 2 (any `K`, `Chord[...]` as `K`) * 3 (`Chord[...]`
    # as `V`, `Tuple[Chord[...], ...]` as `V`,
    # `Union[Chord[...], Tuple[Chord[...], ...]]` as `V`) = 6 overloads
    @overload
    def combinations(
        self: 'Dictionary[K, str]',
        other: 'Dictionary[K2, str]',
        *,
        keys: Callable[[K, K2], K3],
        # values = concat
    ) -> 'Dictionary[K3, str]': ...
    @overload
    def combinations(
        self: 'Dictionary[Chord[SystemT], str]',
        other: 'Dictionary[Chord[SystemT], str]',
    ) -> 'Dictionary[Chord[SystemT], str]': ...
    def combinations(
        self,
        other: 'Dictionary[K2, V2]',
        *,
        keys: Callable[[Any, Any], Any]=Chord.combine,
        values: Callable[[Any, Any], Any]=concat
    ) -> 'Dictionary[K3, V3]':
        typed_keys: Callable[[K, K2], K3] = keys
        typed_values: Callable[[V, V2], V3] = values
        return Dictionary(
            (typed_keys(kl, kr), typed_values(vl, vr))
            for kl, vl in self
            for kr, vr in other
        )

    def to_plover_dict(
        self: Union[
            'Dictionary[Chord[SystemT], str]',
            'Dictionary[Tuple[Chord[SystemT], ...], str]'
        ]
    ) -> Dict[str, str]:
        return {to_plover_str(k): v for k, v in self}

    def print_as_plover_json_dict(
        self: Union[
            'Dictionary[Chord[SystemT], str]',
            'Dictionary[Tuple[Chord[SystemT], ...], str]'
        ]
    ) -> None:
        import json
        print(json.dumps(self.to_plover_dict()))

    def longest_key(
        self: Union[
            'Dictionary[Chord[SystemT], str]',
            'Dictionary[Tuple[Chord[SystemT], ...], str]'
        ]
    ) -> int:
        return max(len(to_multi_chord(i)) for i in self.keys())

    def plover_lookup(
        self: Union[
            'Dictionary[Chord[SystemT], str]',
            'Dictionary[Tuple[Chord[SystemT], ...], str]'
        ],
        key: Tuple[str, ...],
        *,
        system: SystemT,
    ) -> str:
        """
        This ignores any and all `ValueError`s due to invalid
        keys!

        These should only occur if this is used by the Plover
        Python dictionary plugin when Plovary has a bug, but a
        bug in Plovary shouldn't pull Plover down with it.
        """

        try:
            return self[tuple(system.parse(i) for i in key)]
        except ValueError as e:
            print(e, file=sys.stderr)
            raise KeyError

    def plover_reverse_lookup(
        self: Union[
            'Dictionary[Chord[SystemT], str]',
            'Dictionary[Tuple[Chord[SystemT], ...], str]'
        ],
        output: str
    ) -> List[Tuple[str, ...]]:
        return [
            tuple(j.plover_str for j in to_multi_chord(i))
            for i in self.keys_for(output)
        ]

    def install_as_plover_python_dict(
        self: Union[
            'Dictionary[Chord[SystemT], str]',
            'Dictionary[Tuple[Chord[SystemT], ...], str]'
        ],
        mod_globals: Dict[str, Any]
    ) -> None:
        mod_globals["LONGEST_KEY"] = self.longest_key()
        # We have to use lambdas here, otherwise it doesn't work for some reason
        try:
            key = next(i for i in self.keys() if i != ())
            system = key.system if isinstance(key, Chord) else key[0].system
            mod_globals["lookup"] = (
                lambda x: self.plover_lookup(x, system=system)
            )
        except StopIteration:
            def only_throw(*args: Any, **kwargs: Any) -> Any:
                raise KeyError
            mod_globals["lookup"] = only_throw
        mod_globals["reverse_lookup"] = lambda x: self.plover_reverse_lookup(x)

    def plover_dict_main(
        self: Union[
            'Dictionary[Chord[SystemT], str]',
            'Dictionary[Tuple[Chord[SystemT], ...], str]'
        ],
        name: str,
        mod_globals: Dict[str, Any]
    ) -> None:
        if name == "__main__":
            import sys
            if "--debug" in sys.argv:
                print(self)
            else:
                self.print_as_plover_json_dict()
        else:
            self.install_as_plover_python_dict(mod_globals)

    def _add_impl(
        self,
        other: Union['Dictionary[K, V]', Chord[SystemT], str, Any],
        *,
        suffix_or_prefix: Callable[[str], Callable[[str], str]]
    ) -> Any:
        if isinstance(other, Dictionary):
            return Dictionary(chain(self, other))
        elif isinstance(other, Chord):
            self_chord_k = cast(Dictionary[Chord[Any], V], self)
            return self_chord_k.map(keys=add(other))
        elif isinstance(other, str):
            self_str_v = cast(Dictionary[K, str], self)
            return self_str_v.map(values=suffix_or_prefix(other))
        else:
            return NotImplemented

    @overload
    def __add__(self, other: 'Dictionary[K, V]') -> 'Dictionary[K, V]':  ...
    @overload
    def __add__(
        self: 'Dictionary[Chord[SystemT], V]',
        other: Chord[SystemT]
    ) -> 'Dictionary[Chord[SystemT], V]': ...
    @overload
    def __add__(self: 'Dictionary[K, str]', other: str) -> 'Dictionary[K, str]':
        ...
    # Using `Any` in the return position because `mypy` doesn't like just using
    # `Dictionary[K, V]` as a return type, even though it would be correct.
    # Using `Any` in the argument position because it could be anything else to
    # allow for `__radd__`
    def __add__(
        self,
        other: Union['Dictionary[K, V]', Chord[SystemT], str, Any]
    ) -> Any:
        """
        Note that strings are *always* assumed to be meant for the value side
        """
        return self._add_impl(other, suffix_or_prefix=suffix)

    @overload
    def __radd__(self, other: 'Dictionary[K, V]') -> 'Dictionary[K, V]': ...
    @overload
    def __radd__(
        self: 'Dictionary[Chord[SystemT], V]',
        other: Chord[SystemT]
    ) -> 'Dictionary[Chord[SystemT], V]': ...
    @overload
    def __radd__(
        self: 'Dictionary[K, str]',
        other: str
    ) -> 'Dictionary[K, str]': ...
    def __radd__(
        self,
        other: Union['Dictionary[K, V]', Chord[SystemT], str, Any]
    ) -> Any:
        return self._add_impl(other, suffix_or_prefix=prefix)

    def __sub__(self, other: Iterable[K]) -> 'Dictionary[K, V]':
        if hasattr(other, "__iter__"):
            other = list(other)
            if not all(k in self for k in other):
                warn(f"Not all keys of {other!r} are present in {self!r}")
            return Dictionary((k, v) for k, v in self if k not in other)
        else:
            return NotImplemented

    def __mul__(
        self: 'Dictionary[Chord[SystemT], str]',
        other: Union['Dictionary[Chord[SystemT], str]', Any]
    ) -> 'Dictionary[Chord[SystemT], str]':
        if isinstance(other, Dictionary):
            return self.combinations(other)
        else:
            return NotImplemented

    @overload
    def __contains__(self, key: K) -> bool: ...
    @overload
    def __contains__(
        self: 'Dictionary[Chord[SystemT], V]',
        key: Tuple[Chord[SystemT], ...]
    ) -> bool: ...
    @overload
    def __contains__(
        self: 'Dictionary[Tuple[Chord[SystemT], ...], V]',
        key: Chord[SystemT]
    ) -> bool: ...
    # Using `Any` because `mypy` doesn't like `Union`ing everything together as
    # of version 0.800
    def __contains__(self, key: Any) -> bool:
        if isinstance(key, Chord) and (key,) in self.dict:
            return True

        if _is_chord_in_single_element_tuple(key) and key[0] in self.dict:
            return True

        return key in self.dict

    @overload
    def __getitem__(self, key: K) -> V: ...
    @overload
    def __getitem__(
        self: 'Dictionary[Chord[SystemT], V]',
        key: Tuple[Chord[SystemT], ...]
    ) -> V: ...
    @overload
    def __getitem__(
        self: 'Dictionary[Tuple[Chord[SystemT], ...], V]',
        key: Chord[SystemT]
    ) -> V: ...
    def __getitem__(self, key: Any) -> V:
        if isinstance(key, Chord) and (key,) in self.dict:
            return self.dict[cast(Any, (key,))]

        if _is_chord_in_single_element_tuple(key) and key[0] in self.dict:
            return self.dict[key[0]]

        return self.dict[key]

    def __setitem__(self, key: K, value: V) -> None:
        self.dict[key] = value

    def __iter__(self) -> Iterator[Tuple[K, V]]:
        return iter(self.dict.items())

    def __repr__(self) -> str:
        return "Dictionary({{\n{}}})".format(
            "".join(
                "  {}: {!r},\n".format(
                    (
                        k.plover_str
                        if isinstance(k, Chord)
                        else (
                            "/".join(i.plover_str for i in k)
                            if isinstance(k, tuple) and
                                all(isinstance(i, Chord) for i in k)
                            else repr(k)
                        )
                    ),
                    v
                )
                for k, v in self
            )
        )


class EnglishSystem(System):
    sys_name = "English Stenotype"

    sys_key_order = [
        "#",
        "S-", "T-", "K-", "P-", "W-", "H-", "R-",
        "A", "O", "*", "-", "E", "U",
        "-F", "-R", "-P", "-B", "-L", "-G", "-T", "-S", "-D", "-Z",
    ]

    sys_unordered_keys = ["#"]

    sys_combining_keys = ["#", "*"]

    sys_optional_replacements = {
        # Alphabet
        "B-": ["P-", "W-"],
        "C-": ["K-", "R-"],
        "D-": ["T-", "K-"],
        "F-": ["T-", "P-"],
        "G-": ["T-", "K-", "P-", "W-"],
        "J-": ["S-", "K-", "W-", "R-"],
        "L-": ["H-", "R-"],
        "M-": ["P-", "H-"],
        "N-": ["T-", "P-", "H-"],
        "Q-": ["K-", "W-"],
        "V-": ["S-", "R-"],
        "X-": ["K-", "P-"],
        "Y-": ["K-", "W-", "R-"],
        "Z-": ["S-", "*"],

        "I": ["E", "U"],

        "-J": ["-P", "-B", "-L", "-G"],
        "-K": ["-B", "-G"],
        "-M": ["-P", "-L"],
        "-N": ["-P", "-B"],
        "-V": ["*", "-F"],
        "-X": ["-B", "-G", "-S"],
    }

    sys_mandatory_replacements = {
        "1-": ["#", "S-"],
        "2-": ["#", "T-"],
        "3-": ["#", "P-"],
        "4-": ["#", "H-"],
        "5": ["#", "A"],
        "0": ["#", "O"],
        "-6": ["#", "-F"],
        "-7": ["#", "-P"],
        "-8": ["#", "-L"],
        "-9": ["#", "-T"],
    }


EnglishChord = Chord[EnglishSystem]


# Keeping the name short since I expect it to be used a lot:
system = EnglishSystem()

digit_keys = [
    "0", "1-", "2-", "3-", "4-", "5", "-6", "-7", "-8", "-9"
]
digits = [system.chord(i) for i in digit_keys]

# A few default dictionaries:
single_digit_only = Dictionary(
    (digits[i], str(i))
    for i in range(10)
)
double_digit_only = Dictionary(
    (digits[i] + digits[j], str(i) + str(j))
    for i in range(10)
    for j in range(10)
    if i != j and system.keys_ordered(digit_keys[i], digit_keys[j])
) + Dictionary(
    (digits[i] + digits[j] + system.chord("E", "U"), str(i) + str(j))
    for i in range(10)
    for j in range(10)
    if i != j and system.keys_ordered(digit_keys[j], digit_keys[i])
) + Dictionary((digits[i] + "-D", str(i) * 2) for i in range(10))
hundred00 = system.parsed_single_dict({"0D": "100"})
double_digit_only_hundred00 = double_digit_only - hundred00.keys() + hundred00
hundred1z = system.parsed_single_dict({"1-Z": "100"})
double_digit_only_hundred1z = double_digit_only + hundred1z
single_and_double_digit = single_digit_only + double_digit_only
single_and_double_digit_hundred00 = (
    single_digit_only + double_digit_only_hundred00
)
single_and_double_digit_hundred1z = (
    single_digit_only + double_digit_only_hundred1z
)
hundreds = Dictionary(
    (digits[i] + "-Z", str(i) + "00")
    for i in range(10)
)
numbers = single_and_double_digit + hundreds

# Fingertyping
fingertyping_lowercase_no_asterisk = system.parsed_single_dict({
    "A": "a",
    "PW": "b",
    "KR": "c",
    "TK": "d",
    "E": "e",
    "TP": "f",
    "TKPW": "g",
    "H": "h",
    "EU": "i",
    "SKWR": "j",
    "K": "k",
    "HR": "l",
    "PH": "m",
    "TPH": "n",
    "O": "o",
    "P": "p",
    "KW": "q",
    "R": "r",
    "S": "s",
    "T": "t",
    "U": "u",
    "SR": "v",
    "W": "w",
    "KP": "x",
    "KWR": "y",
    "STKPW": "z",
})
fingertyping_uppercase_no_p_no_asterisk = (
    fingertyping_lowercase_no_asterisk.map(values=str.upper)
)
fingertyping_uppercase_p_no_asterisk = (
    fingertyping_uppercase_no_p_no_asterisk.map(keys=add("-P"))
)
fingertyping_no_asterisk = (
    fingertyping_lowercase_no_asterisk + fingertyping_uppercase_p_no_asterisk
)
fingertyping_lowercase = fingertyping_lowercase_no_asterisk.map(keys=add("*"))
fingertyping_uppercase_no_p = (
    fingertyping_uppercase_no_p_no_asterisk.map(keys=add("*"))
)
fingertyping_uppercase_p = (
    fingertyping_uppercase_p_no_asterisk.map(keys=add("*"))
)
fingertyping = fingertyping_no_asterisk.map(keys=add("*"))
