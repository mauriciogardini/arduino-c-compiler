#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict


class Error():
    def __str__(self):
        if self.token:
            return u'Error - %s [%iL - %iC]' % (self.message,
                                                self.token.line + 1,
                                                self.token.column + 1)
        return u'Error - %s' % (self.message)

    def __init__(self, message, token=None):
        self.message = message
        self.token = token


class SemanticWarning():
    def __str__(self):
        if self.token:
            return u'Warning - %s [%iL - %iC]' % (self.message,
                                                  self.token.line + 1,
                                                  self.token.column + 1)
        return u'Warning - %s' % (self.message)

    def __init__(self, message, token=None):
        self.message = message
        self.token = token


class StandaloneCodeManager():
    def __init__(self, place=None, code=None, operator=None,
                 production_type=None):
        if code and code != '':
            self.code.append(code)
        else:
            self.code = []

    def prepend_code(self, code):
        if code:
            if code != '' and type(code) in [str, unicode]:
                self.code = code.append(self.code)
            elif type(code) == list:
                self.code = code + self.code

    def append_code(self, code):
        if code:
            if code != '' and type(code) in [str, unicode]:
                self.code.append(code)
            elif type(code) == list:
                self.code = self.code + code

    def print_all(self):
        for line in self.code:
            print line


class Production():
    def __init__(self, place=None, code=None, operator=None,
                 production_type=None):
        self.place = place
        if code and code != '':
            self.code.append(code)
        else:
            self.code = []
        self.operator = operator
        self.production_type = production_type

    def prepend_code(self, code):
        if code:
            if code != '' and type(code) in [str, unicode]:
                self.code = code.append(self.code)
            elif type(code) == list:
                self.code = code + self.code

    def append_code(self, code):
        if code:
            if code != '' and type(code) in [str, unicode]:
                self.code.append(code)
            elif type(code) == list:
                self.code = self.code + code

    def __str__(self):
        return u'Place: %s | Operator: %s | Production Type: %s' %\
            (self.place, self.operator, self.production_type)

    def print_all(self):
        for line in self.code:
            print line


class ParametersSet:
    def __init__(self):
        self.elements = OrderedDict()

    def __getitem__(self, key):
        return self.elements[key]

    def get_element_by_index(self, index):
        elements_list = list(self.elements)
        if index < len(elements_list):
            return self.elements[elements_list[index]]
        return None

    def exists(self, identifier):
        if identifier in self.elements.keys():
            return True
        return False

    def add(self, identifier, defined_type):
        if not self.exists(identifier):
            self.elements[identifier] = Parameter(identifier, defined_type)
            return True
        return False

    def __str__(self):
        return ', '.join(['%s %s' % (element.defined_type, element.identifier)
                          for element in self.elements.values()])

    def length(self):
        return len(self.elements)


class Parameter:
    def __init__(self, identifier, defined_type):
        self.identifier = identifier
        self.defined_type = defined_type

    def __str__(self):
        return '%s %s' % (self.defined_type, self.identifier)


class SymbolsTable:
    def __init__(self):
        self.elements = {}

    def __getitem__(self, key):
        return self.elements[key]

    def exists(self, identifier, scope='_global_', try_global=True):
        if scope != '_global_':
            symbols_identifiers = self.elements[scope].symbols_table.\
                elements.keys()
            if identifier in symbols_identifiers or identifier in\
                    self.elements[scope].parameters_set.elements.keys():
                return True
        if (try_global and scope != '_global_') or scope == '_global_':
            if identifier in self.elements.keys():
                return True
        return False

    def add(self, identifier, symbol_type, scope='_global_',
            is_function=False, parameters_set=None, symbols_table=None):
        if not self.exists(identifier, scope, try_global=False):
            if scope != '_global_':
                parent_symbol = self.elements[scope]
                parent_symbol.symbols_table.elements[identifier] =\
                    Symbol(identifier, symbol_type, is_function,
                           parameters_set, symbols_table)
            else:
                self.elements[identifier] =\
                    Symbol(identifier, symbol_type, is_function,
                           parameters_set, symbols_table)
            return True
        return False

    def get(self, identifier, scope):
        if scope != '_global_':
            symbols_identifiers = self.elements[scope].symbols_table.\
                elements.keys()
            if identifier in symbols_identifiers:
                return self.elements[scope].symbols_table[identifier]
            parameters_identifiers = self.elements[scope].parameters_set.\
                elements.keys()
            if identifier in parameters_identifiers:
                return self.elements[scope].parameters_set[identifier]
        if identifier in self.elements.keys():
            return self.elements[identifier]
        return None

    def get_localized_identifier(self, identifier, scope):
        if scope != '_global_':
            symbols_identifiers = self.elements[scope].symbols_table.\
                elements.keys()
            if identifier in symbols_identifiers:
                selected_identifier = self.elements[scope].\
                    symbols_table[identifier].identifier
                return '%s_%s' % (scope, selected_identifier.split(' ')[-1])
            parameters_identifiers = self.elements[scope].parameters_set.\
                elements.keys()
            if identifier in parameters_identifiers:
                selected_identifier = self.elements[scope].\
                    parameters_set[identifier].identifier
                return '%s_%s' % (scope, selected_identifier.split(' ')[-1])
        if identifier in self.elements.keys():
            return self.elements[identifier].identifier.split(' ')[-1]
        return None

    def print_all(self):
        for symbol in self.elements.items():
            if symbol[1].is_function:
                print symbol[1]
        for symbol in self.elements.items():
            if not symbol[1].is_function:
                print symbol[1]


class Symbol:
    def __init__(self, identifier, defined_type, is_function=False,
                 parameters_set=None, symbols_table=None):
        self.identifier = identifier
        self.defined_type = defined_type
        self.is_function = is_function
        self.parameters_set = parameters_set if parameters_set is not None\
            else ParametersSet()
        self.symbols_table = symbols_table if symbols_table is not None\
            else SymbolsTable()

    def __str__(self):
        if self.is_function:
            symbols_table = ['%s %s' % (
                self.symbols_table.elements[key].defined_type,
                self.symbols_table.elements[key].identifier)
                for key in self.symbols_table.elements]
            symbols_table_string = ', '.join(map(str, symbols_table))
            return '%s %s (%s) {%s}' %\
                (self.defined_type, self.identifier,
                 self.parameters_set, symbols_table_string)
        else:
            return '%s %s' %\
                (self.defined_type, self.identifier)

    def add_parameter(self, lexeme, parameter_type):
        return self.parameters_set.add(lexeme, parameter_type)

    def get_parameters_length(self):
        return self.parameters_set.length()
