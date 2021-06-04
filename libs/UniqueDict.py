#!/usr/bin/env python3
# -*- coding: utf-8 -*

# Author: Tomáš Volf, ivolf(at)fit.vutbr.cz


class UniqueDict(dict):
    KEY_CONFLICTED = "!!!"

    def __setitem__(self, key, value):
        if key not in self:
            dict.__setitem__(self, key, value if value != "" else None)
        elif self[key] == None:
            dict.__setitem__(self, key, value)
        elif (
            not value in [None, ""] and self[key] != value
        ):  # if value not empty and dict[key] is not empty also => CONFLICT of values
            dict.__setitem__(self, key, self.KEY_CONFLICTED)
        # else (value is empty and dict[key] is not empty => OK, may be ignored
