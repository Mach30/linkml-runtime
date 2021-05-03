from dataclasses import fields
from typing import Union, Optional

from linkml_runtime.utils.metamodelcore import Curie
from linkml_runtime.utils.yamlutils import YAMLRoot


class EnumDefinitionMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls._addvals()

    def __getitem__(cls, item):
        return cls.__dict__[item]

    def __setitem__(cls, key, value):
        if key in cls.__dict__:
            raise ValueError(f"{cls.__name__} - {key} already assigned")
        cls.__dict__[key] = value

    def __setattr__(self, key, value):
        value_is_pv = "PermissibleValue" in [c.__name__ for c in type(value).mro()]
        if self._defn.code_set and value_is_pv and value.meaning:
            print(f"Validating {value.meaning} against {self._defn.code_set}")
        super().__setattr__(key, value)

    def __contains__(cls, item) -> bool:
        return item in cls.__dict__


class EnumDefinitionImpl(YAMLRoot, metaclass=EnumDefinitionMeta):
    _defn: YAMLRoot = None         # Overridden by implementation - Must be EnumDefinition

    def __init__(self, code: Union[str, Curie, YAMLRoot]) -> None:
        """
        @param code: A permissible value or something that can be morphed into a PV
        """
        code_is_pv = "PermissibleValue" in [c.__name__ for c in type(code).mro()]
        # if isinstance(code, PermissibleValue):
        if code_is_pv:
            key = code.text
        elif isinstance(code, Curie):
            key = str(code)
        else:
            key = code

        if key not in self.__class__ and self._defn.code_set:
            code = self._lookup(key)
            if code:
                self.__class__[key] = code
                self._code = code
        elif key not in self.__class__:
            raise ValueError(f"Unknown {self.__class__.__name__} enumeration code: {key}")
        elif code_is_pv:
            if getattr(self, 'code', None):
                if self._code != code:
                    raise ValueError(f"Enumeration: {self.__class__.__name__} - "
                                     f"Cannot change an existing permissible value entry for {code}")
            else:
                self._code = code
        else:
            self._code = self.__class__[key]

    def _lookup(self, key: str) -> Optional[YAMLRoot]:
        """
        Hook to look up key in the appropriate code system
        @param key: URI or string in Curie form (TBD) or a PermissibleValue
        @return: Permissible value rendering if key is valid
        """
        return None

    # WARNING: any non "_" prefix pollutes the EnumDefinition namespace.  These CAN be overridden, but be aware that
    # the value "code", "meaning" "uri", or "curie" as actual codes will mean that one will need to use "_code" and
    # direct access to get at the real values
    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, val):
        self._code = val

    @property
    def meaning(self):
        return self._code.meaning

    @property
    def uri(self):
        return self._code.meaning

    @property
    def curie(self):
        return "Curie for: " + self._code.meaning

    @classmethod
    def _addvals(cls):
        """ Override this to add non-python compatible values """
        pass

    def __str__(self) -> str:
        return f'{self._code.text}: {self._code.description or ""}'

    def __repr__(self) -> str:
        rlist = [(f.name, getattr(self._code, f.name)) for f in fields(self._code)]
        return '(' + ', '.join([f"{f[0]}={repr(f[1])}" for f in rlist if f[1]]) + ')'
