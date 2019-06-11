#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
This is the subset of the C language that this project is supposed to
recognize:
    √   While
    √   Do-While
    √   For
    √   For inside a For (For must create a "subscope" of variables)
    √   If
    √   One-line If
    √   Break and Continue
    √   Attribution as a command, not as an operator (=, *=, /=, %=, +=, -=,
        <<=, >>=, &=, ^=, |=)
    √   Expression:
        √   Logical Or (||)
        √   Logical And (&&)
        √   Equality (==, !=)
        √   Relational (<, <=, >, >=)
        √   Additive (+, -)
        √   Multiplicative (*, /, %)
        √   Unary (+, -)
    √   Command block, demarked by curly brackets
    √   Function declaration
    √   Function call

This project is supposed to generate C3E code of all the items stated in the
subset above, as well as to identify non-declared identifiers and multiple
declarations of an identifier.

Note: I chose to make a more "verbose" version of the syntactic and semantic
analyser instead of making a more "intelligent" coding for the purpose of
making it easier to understand for those who want to learn how to create the
same thing.
'''

import inspect
import sys
from support_classes import (Error, Production, SemanticWarning,
                             StandaloneCodeManager, SymbolsTable)


class SyntacticAndSemanticAnalyser():
    def __init__(self, tokens_list):
        self.tokens_list = tokens_list
        self.symbols_table = SymbolsTable()
        self.error = None
        self.warnings = []
        self.definitions_code = StandaloneCodeManager()
        self.token_index = 0
        self.token = None
        self.temporary_variable_index = 0
        self.label_index = 0
        self.log = False
        self.modifiers_list = [
            u'auto', u'extern', u'register', u'static'
        ]
        self.specifiers_list = [
            u'long', u'short', u'signed', u'unsigned'
        ]
        self.types_list = [
            u'boolean', u'char', u'double', u'float', u'int', u'word'
        ]
        self.return_types_list = [
            u'boolean', u'char', u'double', u'float', u'int', u'void', u'word'
        ]
        self.assignment_operator_list = [
            u'=', u'*=', u'/=', u'%=', u'+=', u'-=', u'<<=', u'>>=', u'&=',
            u'^=', u'|='
        ]
        self.equality_operator_list = [
            u'==', u'!='
        ]
        self.relational_operator_list = [
            u'<', u'>', u'<=', u'>='
        ]
        self.additive_operator_list = [
            u'+', u'-'
        ]
        self.multiplicative_operator_list = [
            u'*', u'/', u'%'
        ]
        self.unary_prefix_operator_list = [
            u'+', u'-'
        ]

    def get_specific_token(self, position):
        if position >= 0 and position < len(self.tokens_list):
            return self.tokens_list[position]
        return None

    def log_message(self, token):
        if self.log:
            print u'Reconheceu %s - %s ||| %s' % (token.token_type,
                                                  token.lexeme,
                                                  inspect.stack()[2][3])

    def get_present_token(self):
        return self.get_specific_token(self.token_index)

    def get_last_token(self):
        return self.get_specific_token(len(self.tokens_list) - 1)

    def set_eof_error(self, expected_token):
        self.error = Error(u'Expected a %s, got %s' %
                           (expected_token, u'EOF'), self.get_last_token())
        print self.error
        sys.exit()

    def set_syntactic_error(self, expected_token_type, received_token):
        self.error = Error(u'Expected a %s, got %s' %
                           (expected_token_type, received_token.token_type),
                           received_token)
        print self.error
        sys.exit()

    def set_multiple_declaration_error(self, identifier_token):
        self.error = Error(u'Previous declaration of "%s" was found' %
                           identifier_token.lexeme, identifier_token)
        print self.error
        sys.exit()

    def set_invalid_type_error(self, production_type):
        self.error = Error(u'"%s" is an invalid type for this operation' %
                           production_type, None)
        print self.error
        sys.exit()

    def set_undeclared_variable_error(self, identifier_token):
        self.error = Error(u'"%s" undeclared.' %
                           identifier_token.lexeme, identifier_token)
        print self.error
        sys.exit()

    def set_redeclared_variable_error(self, identifier_token):
        self.error = Error(u'"%s" redeclared as different kind of symbol' %
                           identifier_token.lexeme, identifier_token)
        print self.error
        sys.exit()

    def set_invalid_operands_error(self, production1_type, production2_type,
                                   token):
        self.error = Error(
            u'Invalid operands for remainder operation: "%s" and "%s"' %
            (production1_type, production2_type), token)
        print self.error
        sys.exit()

    def set_return_out_of_function_error(self):
        self.error = Error(u'Return out of function')
        print self.error
        sys.exit()

    def set_unexpected_parameter_error(self, function_identifier,
                                       parameters_ammount):
        self.error = None
        if parameters_ammount == 0:
            self.error = Error(u'%s %s %s' % (
                u'The function', function_identifier,
                u'didn\'t expect any parameters'))
        else:
            self.error = Error(
                u'%s %s %s %s %s' % (
                    u'The function', function_identifier, u'only expected',
                    parameters_ammount, u'parameters'))
        print self.error
        sys.exit()

    def set_implicit_conversion_warning(self, left_side_type, right_side_type,
                                        left_side_token):
        self.warnings.append(SemanticWarning(
            u'implicit conversion from "%s" to "%s"' %
            (right_side_type, left_side_type), left_side_token))

    def get_localized_identifier(self, identifier, scope):
        if '#' not in identifier:
            return self.symbols_table.get_localized_identifier(
                identifier, scope)
        return identifier

    def add_to_symbols_table(self, identifier_token, return_type, scope,
                             is_function=False, parameters_set=None,
                             symbols_table=None):
        if not self.symbols_table.add(identifier_token.lexeme, return_type,
                                      scope, is_function, parameters_set,
                                      symbols_table):
            self.set_multiple_declaration_error(identifier_token)

    def exists_in_symbols_table(self, identifier_token, scope):
        return self.symbols_table.exists(identifier_token.lexeme, scope,
                                         try_global=True)

    def add_parameter_to_symbol(self, symbol_identifier, parameter_token,
                                parameter_type):
        if not self.symbols_table[symbol_identifier].add_parameter(
                parameter_token.lexeme, parameter_type):
            self.set_multiple_declaration_error(parameter_token)

    def get_next_label(self):
        name = '#LB%s' % self.label_index
        self.label_index += 1
        return name

    def get_next_temporary_variable(self):
        name = '#T%s' % self.temporary_variable_index
        self.temporary_variable_index += 1
        return name

    def generate_code(self, parameter_1, parameter_2, parameter_3=None,
                      parameter_4=None, parameter_5=None, parameter_6=None,
                      code_type=None):
        if parameter_6:
            return '%s %s %s %s %s %s' % (parameter_1, parameter_2,
                                          parameter_3, parameter_4,
                                          parameter_5, parameter_6)
        elif parameter_5:
            if code_type == 'call':
                return '%s %s %s %s, %s' % (parameter_1, parameter_2,
                                            parameter_3, parameter_4,
                                            parameter_5)
            else:
                return '%s %s %s %s %s' % (parameter_1, parameter_2,
                                           parameter_3, parameter_4,
                                           parameter_5)
        elif parameter_4:
            return '%s %s %s %s' % (parameter_1, parameter_2, parameter_3,
                                    parameter_4)
        elif parameter_3:
            if code_type == 'return':
                return '%s %s, %s' % (parameter_1, parameter_2, parameter_3)
            else:
                return '%s %s %s' % (parameter_1, parameter_2, parameter_3)
        else:
            if code_type == 'label':
                return '%s%s' % (parameter_1, parameter_2)
            return '%s %s' % (parameter_1, parameter_2)

    def calculate_resulting_production_type(self, production1, production2):
        if self.is_valid_operation(production1, production2):
            return self.return_operation_type(production1, production2)
        else:
            self.set_invalid_type_error(production1)

    def is_valid_operation(self, production1, production2,
                           are_both_required=False):
        valid_types = ['float', 'int', 'double']
        is_production1_valid_type = production1.production_type in valid_types
        is_production2_valid_type = production2.production_type in valid_types
        if production1.place and production2.place and\
                is_production1_valid_type and is_production2_valid_type:
            return True
        elif are_both_required:
            return False
        elif production1.place and is_production1_valid_type:
            return True
        else:
            return False

    def return_operation_type(self, production1, production2):
        if production1.place and production2.place:
            if production2.production_type !=\
                    production1.production_type:
                if production1.production_type == 'double' or\
                        production2.production_type == 'double':
                    return 'double'
                return 'float'
            else:
                return production1.production_type
        else:
            return production1.production_type

    def process_tokens(self, print_all):
        program = self.check_program()
        if program and self.token_index == len(self.tokens_list):
            if print_all:
                self.print_symbols_table()
                self.print_intermediary_code(program)
                self.print_warnings()
            else:
                print 'OK.'
        else:
            print self.error

    def print_separator(self):
        print '-' * 40

    def print_symbols_table(self):
        print
        print 'Symbols\' Table'
        print '---------------'
        print
        self.symbols_table.print_all()
        print
        self.print_separator()

    def print_intermediary_code(self, program):
        print
        print 'Intermediary Code'
        print '-----------------'
        print
        self.definitions_code.print_all()
        print 'goto main'
        program.print_all()
        print
        self.print_separator()

    def print_warnings(self):
        print
        if self.warnings:
            print 'Warning(s)'
            print '----------'
            print
            for warning in self.warnings:
                print warning
            print
            self.print_separator()

    def check_program(self):
        return self.check_definitions_list(scope=u'_global_')

    def check_definitions_list(self, scope):
        definitions_list = Production()
        definition = self.check_definition(scope=scope)
        if definition:
            definitions_list1 = self.check_definitions_list(scope=scope)
            definitions_list.append_code(definition.code)
            definitions_list.append_code(definitions_list1.code)
            return definitions_list
        return definitions_list

    def check_definition(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            modifiers_return = self.check_modifiers_list()
            modifiers = None if type(modifiers_return) is bool\
                else modifiers_return
            return_type_return = self.check_return_type()
            return_type = u'%s %s' % (modifiers, return_type_return)\
                if modifiers else u'%s' % (return_type_return)
            index = self.token_index
            token = self.get_specific_token(index)
            if token:
                if token.token_type == u'T_ID' or\
                        token.token_type == u'T_RESERVED_WORD':
                    identifier_token = token
                    self.log_message(token)
                    index = self.token_index = index + 1
                    token = self.get_specific_token(index)
                    if token:
                        # Likely to be a function declaration
                        if token.token_type == u'T_PARENTHESES_OPEN':
                            self.add_to_symbols_table(identifier_token,
                                                      return_type, scope, True)
                            definition = Production()
                            definition_parentheses =\
                                self.check_definition_parentheses(
                                    token, index, identifier_token.lexeme)
                            new_production = self.generate_code(
                                identifier_token.lexeme, ':',
                                code_type='label')
                            definition.append_code(new_production)
                            definition.append_code(definition_parentheses.code)
                            # TODO: Verificar uma solução melhor
                            # Falha no caso if_elseif_else
                            if 'return' not in definition.code[-1]:
                                definition_place =\
                                    self.get_next_temporary_variable()
                                new_production = self.generate_code(
                                    definition_place, ':=', '0')
                                new_production2 = self.generate_code(
                                    'return', definition_place)
                                definition.append_code(new_production)
                                definition.append_code(new_production2)
                            return definition
                        # Likely to be a declaration with assignment
                        elif token.token_type == u'T_ASSIGN':
                            self.add_to_symbols_table(identifier_token,
                                                      return_type, scope)
                            definition_assign = self.check_definition_assign(
                                token, index, return_type, scope,
                                identifier_token)
                            self.definitions_code.append_code(
                                definition_assign.code)
                            return Production()
                        # Likely to be a declaration without assignment
                        elif token.token_type == u'T_SEMICOLON':
                            self.log_message(token)
                            self.add_to_symbols_table(identifier_token,
                                                      return_type, scope)
                            self.token_index = index + 1
                            return Production()
                        # Likely to be a multiple declaration with no
                        # assignment on its first element
                        elif token.token_type == u'T_COMMA':
                            self.add_to_symbols_table(identifier_token,
                                                      return_type, scope)
                            more_declarations =\
                                self.check_more_declarations(return_type,
                                                             scope)
                            token = self.get_specific_token(self.token_index)
                            if token.token_type == u'T_SEMICOLON':
                                self.log_message(token)
                                self.token_index += 1
                                return more_declarations
                            return more_declarations
                        self.set_syntactic_error(
                            u'%s %s %s' % ('T_PARENTHESES_OPEN',
                                           u'or T_ASSIGN', 'or T_SEMICOLON'),
                            token)
                    self.set_eof_error(u'%s %s %s' %
                                       ('T_PARENTHESES_OPEN', u'or T_ASSIGN',
                                        'or T_SEMICOLON'), token)
                self.set_syntactic_error(u'T_ID or T_RESERVED_WORD', token)
            self.set_eof_error(u'T_ID or T_RESERVED_WORD')
        # If no token is found, it's likely that there are no more declarations
        return False

    # Helper function, not in the grammar
    def check_definition_assign(self, token, index, return_type, scope,
                                identifier_token):
        if token:
            if token.token_type == u'T_ASSIGN':
                right_side_declaration = self.check_right_side_declaration(
                    return_type, scope, identifier_token)
                more_declarations =\
                    self.check_more_declarations(return_type, scope)
                token = self.get_specific_token(self.token_index)
                if token:
                    if token.token_type == u'T_SEMICOLON':
                        self.log_message(token)
                        self.token_index += 1
                        definition_assign = Production()
                        definition_assign.append_code(right_side_declaration.code)
                        definition_assign.append_code(more_declarations.code)
                        definition_assign.place = right_side_declaration.place
                        return definition_assign
                    self.set_syntactic_error(u'T_SEMICOLON', token)
                self.set_eof_error(u'T_SEMICOLON')
            self.set_syntactic_error(u'T_ASSIGN', token)
        self.set_eof_error(u'T_ASSIGN')

    # Helper function, not in the grammar
    def check_definition_parentheses(self, token, index, scope):
        if token:
            if token.token_type == u'T_PARENTHESES_OPEN':
                self.log_message(token)
                self.token_index = index + 1
                parameters_list = self.check_parameters_list(scope)
                index = self.token_index
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_PARENTHESES_CLOSE':
                        self.log_message(token)
                        index = self.token_index = index + 1
                        token = self.get_specific_token(index)
                        if token:
                            if token.token_type == u'T_CURLY_BRACKET_OPEN':
                                self.log_message(token)
                                index = self.token_index = index + 1
                                commands_list = self.check_commands_list(scope)
                                index = self.token_index
                                token = self.get_specific_token(index)
                                if token:
                                    if token.token_type ==\
                                            u'T_CURLY_BRACKET_CLOSE':
                                        self.log_message(token)
                                        self.token_index = index + 1
                                        definition_parentheses = Production()
                                        definition_parentheses.append_code(
                                            parameters_list.code)
                                        definition_parentheses.append_code(
                                            commands_list.code)
                                        return definition_parentheses
                                    self.set_syntactic_error(
                                        u'T_CURLY_BRACKET_CLOSE', token)
                                self.set_eof_error(u'T_CURLY_BRACKET_CLOSE')
                            self.set_syntactic_error(u'T_CURLY_BRACKET_OPEN',
                                                     token)
                        self.set_eof_error(u'T_CURLY_BRACKET_OPEN')
                    self.set_syntactic_error(u'T_PARENTHESES_CLOSE', token)
                self.set_eof_error(u'T_PARENTHESES_CLOSE')
            self.set_syntactic_error(u'T_PARENTHESES_OPEN', token)
        self.set_eof_error(u'T_PARENTHESES_OPEN')

    def check_parameters_list(self, scope):
        parameters_list = Production()
        parameter = self.check_parameter(scope, 0)
        if parameter:
            more_parameters = self.check_more_parameters(scope, 1)
            parameters_list.append_code(parameter.code)
            parameters_list.append_code(more_parameters.code)
            return parameters_list
        return parameters_list

    def check_more_parameters(self, scope, parameter_index):
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_COMMA':
                self.log_message(token)
                self.token_index += 1
                token = self.get_specific_token(self.token_index)
                more_parameters = Production()
                parameter = self.check_parameter(scope, parameter_index)
                if parameter:
                    more_parameters1 = self.check_more_parameters(
                        scope, parameter_index + 1)
                    more_parameters.append_code(parameter.code)
                    more_parameters.append_code(more_parameters1.code)
                    return more_parameters
                else:
                    # Expected a parameter after a comma
                    self.set_syntactic_error('parameter', token)
            # It is likely that there are no more parameters
            return Production()
        return True

    def check_parameter(self, scope, parameter_index):
        modifiers_return = self.check_modifiers_list()
        modifiers = None if type(modifiers_return) is bool\
            else modifiers_return
        type_return = self.check_type()
        if type_return:
            parameter_type = u'%s %s' % (modifiers, type_return)\
                if modifiers else u'%s' % (type_return)
            index = self.token_index
            token = self.get_specific_token(index)
            if token:
                if token.token_type == u'T_ID':
                    self.add_parameter_to_symbol(scope, token, parameter_type)
                    self.log_message(token)
                    self.token_index = index + 1
                    parameter = Production()
                    left_side_name = self.get_localized_identifier(
                        token.lexeme, scope)
                    new_production = self.generate_code(
                        left_side_name, ':=', 'param[%s]' % (parameter_index))
                    parameter.append_code(new_production)
                    return parameter
                self.set_syntactic_error(u'T_ID', token)
            self.set_eof_error(u'T_ID')
        # It is likely that there are no more parameters
        return False

    def check_modifiers_list(self):
        token = self.check_modifier()
        if token:
            rest_of_modifiers = self.check_modifiers_list()
            if rest_of_modifiers and type(rest_of_modifiers) is not bool:
                return u'%s %s' % (token.lexeme, rest_of_modifiers)
            return u'%s' % (token.lexeme)
        return True

    def check_modifier(self):
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme in self.modifiers_list:
                self.log_message(token)
                self.token_index += 1
                return token
            # It is likely that are no modifiers anymore
            return False
        self.set_eof_error(u'T_RESERVED_WORD')

    def check_specifiers_list(self):
        token = self.check_specifier()
        if token:
            rest_of_specifiers = self.check_modifiers_list()
            if rest_of_specifiers and type(rest_of_specifiers) is not bool:
                return u'%s %s' % (token.lexeme, rest_of_specifiers)
            return u'%s' % (token.lexeme)
        return True

    def check_specifier(self):
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme in self.specifiers_list:
                self.log_message(token)
                self.token_index += 1
                return token
            # It is likely that there are no more specifiers anymore
            return False
        self.set_eof_error(u'T_RESERVED_WORD')

    def check_type(self):
        specifiers_return = self.check_specifiers_list()
        specifiers = None if type(specifiers_return) is bool\
            else specifiers_return
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme in self.types_list:
                self.log_message(token)
                self.token_index = index + 1
                if specifiers:
                    return u'%s %s' % (specifiers, token.lexeme)
                return u'%s' % (token.lexeme)
            return False
        self.set_eof_error(u'T_RESERVED_WORD')

    def check_return_type(self):
        specifiers_return = self.check_specifiers_list()
        specifiers = None if type(specifiers_return) is bool\
            else specifiers_return
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme in self.return_types_list:
                self.log_message(token)
                self.token_index = index + 1
                if specifiers:
                    return u'%s %s' % (specifiers, token.lexeme)
                return u'%s' % (token.lexeme)
            self.set_syntactic_error(u'T_RESERVED_WORD', token)
        self.set_eof_error(u'T_RESERVED_WORD')

    def check_standalone_declaration(self, return_type, scope):
        """
        $modifiers_list $type #identifier
        $right_side_declaration $more_declarations
        """
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_ID' or\
                    token.token_type == u'T_RESERVED_WORD':
                self.log_message(token)
                identifier_token = token
                index = self.token_index = index + 1
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_ASSIGN':
                        self.add_to_symbols_table(identifier_token,
                                                  return_type, scope)
                        right_side_declaration =\
                            self.check_right_side_declaration(
                                return_type, scope, identifier_token)
                        if right_side_declaration.place:
                            more_declarations =\
                                self.check_more_declarations(return_type,
                                                             scope)
                            token = self.get_specific_token(self.token_index)
                            if token:
                                if token.token_type == u'T_SEMICOLON':
                                    self.log_message(token)
                                    self.token_index += 1
                                    standalone_declaration = Production()
                                    standalone_declaration.append_code(
                                        right_side_declaration.code)
                                    return standalone_declaration
                                self.set_syntactic_error(u'T_SEMICOLON', token)
                            self.set_eof_error(u'T_SEMICOLON')
                        standalone_declaration = Production()
                        return standalone_declaration
                    elif token.token_type == u'T_COMMA':
                        self.add_to_symbols_table(identifier_token,
                                                  return_type, scope)
                        self.check_more_declarations(return_type, scope)
                        token = self.get_specific_token(self.token_index)
                        if token.token_type == u'T_SEMICOLON':
                            self.log_message(token)
                            self.token_index += 1
                            standalone_declaration = Production()
                            return standalone_declaration
                        # Commented, check if there are any consequences
                        # return True
                        self.set_syntactic_error(u'T_SEMICOLON', token)
                    elif token.token_type == u'T_SEMICOLON':
                        self.add_to_symbols_table(identifier_token,
                                                  return_type, scope)
                        self.log_message(token)
                        self.token_index += 1
                        standalone_declaration = Production()
                        return standalone_declaration
                    self.set_syntactic_error(u'T_ASSIGN or T_COMMA', token)
                self.set_eof_error(u'T_ASSIGN or T_COMMA')
            self.set_syntactic_error(u'T_ID or T_RESERVED_WORD', token)
        # If no token is found, it's likely that there are no more declarations
        return False

    def check_more_declarations(self, return_type, scope):
        """
        {{
            , $declaration $more_declarations
            Ø
        }}
        """
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_COMMA':
                self.log_message(token)
                self.token_index = index + 1
                declaration = self.check_declaration(return_type, scope)
                if declaration:
                    more_declarations1 =\
                        self.check_more_declarations(return_type, scope)
                    more_declarations = Production()
                    more_declarations.append_code(declaration.code)
                    more_declarations.append_code(more_declarations1.code)
                    return more_declarations
                # TODO: Verify if the line below is valid in any way
                token = self.get_specific_token(self.token_index)
            more_declarations = Production()
            return more_declarations
        more_declarations = Production()
        return more_declarations

    def check_declaration(self, return_type, scope):
        """
        #identifier $right_side_declaration
        """
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_ID':
                self.log_message(token)
                self.add_to_symbols_table(token, return_type, scope)
                self.token_index = index + 1
                right_side_declaration = self.check_right_side_declaration(
                    return_type, scope, token)
                return right_side_declaration
            return False
        self.set_eof_error(u'T_ID')

    def check_right_side_declaration(self, return_type, scope,
                                     identifier_token):
        """
        {{
            = $right_side_expression
            Ø
        }}
        """
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_ASSIGN':
                self.log_message(token)
                index = self.token_index = index + 1
                right_side_expression = self.check_right_side_expression(
                    scope)
                right_side_declaration = Production()
                right_side_declaration.place = right_side_expression.place
                right_side_declaration.append_code(right_side_expression.code)
                if right_side_expression.place:
                    if return_type != right_side_expression.production_type:
                        self.set_implicit_conversion_warning(
                            return_type, right_side_expression.production_type,
                            identifier_token)
                    left_side_name = self.get_localized_identifier(
                        identifier_token.lexeme, scope)
                    new_production = self.generate_code(
                        left_side_name, ':=',
                        right_side_expression.place)
                    right_side_declaration.append_code(new_production)
                return right_side_declaration
            right_side_declaration = Production()
            return right_side_declaration
        self.set_eof_error(u'T_ASSIGN')

    def check_commands_list(self, scope):
        """
        $command $more_commands
        Ø
        """
        commands_list = Production()
        command = self.check_command(scope)
        if command:
            commands_list1 = self.check_commands_list(scope)
            commands_list.append_code(command.code)
            commands_list.append_code(commands_list1.code)
            return commands_list
        return commands_list

    def check_command(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_ID':
                expression = self.check_expression(scope)
                return expression
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'while':
                command = self.check_while(scope)
                return command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'do':
                command = self.check_do_while(scope)
                return command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'for':
                _for = self.check_for(scope)
                return _for
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'if':
                _if = self.check_if(scope)
                return _if
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'return':
                command = self.check_return(scope)
                return command
            elif token.token_type != u'T_CURLY_BRACKET_CLOSE':
                modifiers_return = self.check_modifiers_list()
                modifiers = None if type(modifiers_return) is bool\
                    else modifiers_return
                return_type_return = self.check_return_type()
                return_type = u'%s %s' % (modifiers, return_type_return)\
                    if modifiers else u'%s' % (return_type_return)
                standalone_declaration =\
                    self.check_standalone_declaration(return_type, scope)
                return standalone_declaration
            return False

    def check_block_commands_list(self, scope, break_label, continue_label):
        """
        $command $more_commands
        Ø
        """
        block_commands_list = Production()
        block_command = self.check_block_command(
            scope, break_label, continue_label)
        if block_command:
            block_commands_list1 = self.check_block_commands_list(
                scope, break_label, continue_label)
            block_commands_list.append_code(block_command.code)
            block_commands_list.append_code(block_commands_list1.code)
            return block_commands_list
        return block_commands_list

    def check_block_command(self, scope, break_label, continue_label):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_ID':
                block_command = self.check_expression(scope)
                return block_command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'while':
                block_command = self.check_while(scope)
                return block_command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'do':
                block_command = self.check_do_while(scope)
                return block_command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'for':
                block_command = self.check_for(scope)
                return block_command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'if':
                block_command = self.check_if(
                    scope, break_label, continue_label)
                return block_command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    (token.lexeme == u'break' or token.lexeme == u'continue'):
                block_command = self.check_single_word_command(
                    scope, break_label, continue_label)
                return block_command
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'return':
                block_command = self.check_return(scope)
                return block_command
            return False

    def check_single_word_command(self, scope, break_label, continue_label):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    (token.lexeme == u'break' or token.lexeme == u'continue'):
                self.log_message(token)
                single_word_lexeme = token.lexeme
                index = self.token_index = index + 1
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_SEMICOLON':
                        self.log_message(token)
                        self.token_index += 1
                        if single_word_lexeme == u'break':
                            single_word_command = Production()
                            new_production = self.generate_code(
                                'goto', break_label)
                            single_word_command.append_code(new_production)
                            return single_word_command
                        else:
                            single_word_command = Production()
                            new_production = self.generate_code(
                                'goto', continue_label)
                            single_word_command.append_code(new_production)
                            return single_word_command
                    self.set_syntactic_error(u'T_SEMICOLON', token)
                self.set_eof_error(u'T_SEMICOLON')
            self.set_syntactic_error(u'T_RESERVED_WORD', token)
        self.set_eof_error(u'T_RESERVED_WORD')

    def check_return(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'return':
                if scope != '_global_':
                    self.log_message(token)
                    self.token_index = index + 1
                    right_side_expression = self.check_right_side_expression(
                        scope)
                    token = self.get_specific_token(self.token_index)
                    if token:
                        if token.token_type == u'T_SEMICOLON':
                            self.log_message(token)
                            self.token_index += 1
                            return_ = Production()
                            function_token = self.symbols_table[scope]
                            right_side_expression_name =\
                                self.get_localized_identifier(
                                    right_side_expression.place, scope)
                            new_production = self.generate_code(
                                'return', right_side_expression_name,
                                function_token.get_parameters_length(),
                                code_type='return')
                            return_.append_code(right_side_expression.code)
                            return_.append_code(new_production)
                            return return_
                        self.set_syntactic_error(u'T_SEMICOLON', token)
                    self.set_eof_error(u'T_SEMICOLON')
                self.set_return_out_of_function_error()
            self.set_syntactic_error(u'T_RESERVED_WORD', token)
        self.set_eof_error(u'T_RESERVED_WORD')

    def check_expression(self, scope):
        left_side_expression = self.check_left_side_expression(scope)
        right_side_expression = self.check_right_side_expression(scope)
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_SEMICOLON':
                self.log_message(token)
                self.token_index += 1
                if left_side_expression.place:
                    expression = Production()
                    left_side_expression_name = self.get_localized_identifier(
                        left_side_expression.place, scope)
                    right_side_expression_name = self.get_localized_identifier(
                        right_side_expression.place, scope)
                    new_production = self.generate_code(
                        left_side_expression_name,
                        left_side_expression.operator,
                        right_side_expression_name)
                    expression.append_code(right_side_expression.code)
                    expression.append_code(new_production)
                    return expression
                else:
                    expression = Production()
                    if any('call' in string for string
                           in right_side_expression.code):
                        expression.append_code(right_side_expression.code)
                    return expression
            self.set_syntactic_error(u'T_SEMICOLON', token)
        self.set_eof_error(u'T_SEMICOLON')

    def check_left_side_expression(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_ID':
                if self.exists_in_symbols_table(token, scope):
                    self.token_index += 1
                    assignment_operator = self.check_assignment_operator()
                    if assignment_operator:
                        left_side_expression = Production()
                        left_side_expression.place = token.lexeme
                        left_side_expression.operator = assignment_operator
                        return left_side_expression
                    else:
                        # There is no left side in this expression
                        self.token_index -= 1
                        left_side_expression = Production()
                        return left_side_expression
                else:
                    self.set_undeclared_variable_error(token)
            # There is no left side in this expression
            left_side_expression = Production()
            return left_side_expression
        self.set_eof_error(u'T_ID')

    def check_assignment_operator(self):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.lexeme in self.assignment_operator_list:
                self.log_message(token)
                index = self.token_index = index + 1
                return token.lexeme
            return None
        self.set_eof_error(u'assignment operator')

    def check_right_side_expression(self, scope):
        right_side_expression = self.check_logical_or(scope)
        return right_side_expression

    def check_logical_or(self, scope):
        logical_and = self.check_logical_and(scope)
        logical_or_helper = self.check_logical_or_helper(
            scope, logical_and.place, logical_and.code,
            logical_and.production_type)
        logical_or = Production()
        logical_or.place = logical_or_helper.place
        logical_or.code = logical_or_helper.code
        logical_or.production_type = logical_or_helper.production_type
        return logical_or

    def check_logical_or_helper(self, scope, inherited_place, inherited_code,
                                inherited_production_type):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_OR':
                self.log_message(token)
                index = self.token_index = index + 1
                logical_and = self.check_logical_and(scope)
                logical_or_helper1_place = self.get_next_temporary_variable()
                logical_or_helper1_code = StandaloneCodeManager()
                logical_or_helper1_code.append_code(inherited_code)
                logical_or_helper1_code.append_code(logical_and.code)
                logical_or_helper1_name = self.get_localized_identifier(
                    logical_or_helper1_place, scope)
                inherited_place_name = self.get_localized_identifier(
                    inherited_place, scope)
                logical_and_place_name = self.get_localized_identifier(
                    logical_and.place, scope)
                new_production =\
                    self.generate_code(logical_or_helper1_name, ':=',
                                       inherited_place_name, token.lexeme,
                                       logical_and_place_name)
                logical_or_helper1_code.append_code(new_production)
                '''
                Logical operators do not perform the usual arithmetic
                conversions. Instead, they evaluate each operand in terms of
                its equivalence to 0. The result of a logical operation is
                either 0 or 1. The result's type is int.
                '''
                logical_or_helper1_production_type = 'int'
                logical_or_helper1 = self.check_logical_or_helper(
                    scope, logical_or_helper1_place,
                    logical_or_helper1_code.code,
                    logical_or_helper1_production_type)
                logical_or_helper = Production()
                logical_or_helper.place = logical_or_helper1.place
                logical_or_helper.code = logical_or_helper1.code
                logical_or_helper.production_type =\
                    logical_or_helper1.production_type
                return logical_or_helper
            logical_or_helper = Production()
            logical_or_helper.place = inherited_place
            logical_or_helper.code = inherited_code
            logical_or_helper.production_type = inherited_production_type
            return logical_or_helper
        self.set_eof_error(u'T_OR operator')

    def check_logical_and(self, scope):
        equality = self.check_equality(scope)
        logical_and_helper = self.check_logical_and_helper(
            scope, equality.place, equality.code,
            equality.production_type)
        logical_and = Production()
        logical_and.place = logical_and_helper.place
        logical_and.code = logical_and_helper.code
        logical_and.production_type = logical_and_helper.production_type
        return logical_and

    def check_logical_and_helper(self, scope, inherited_place, inherited_code,
                                 inherited_production_type):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_AND':
                self.log_message(token)
                index = self.token_index = index + 1
                equality = self.check_equality(scope)
                logical_and_helper1_place = self.get_next_temporary_variable()
                logical_and_helper1_code = StandaloneCodeManager()
                logical_and_helper1_code.append_code(inherited_code)
                logical_and_helper1_code.append_code(equality.code)
                logical_and_helper1_name = self.get_localized_identifier(
                    logical_and_helper1_place, scope)
                inherited_place_name = self.get_localized_identifier(
                    inherited_place, scope)
                equality_place_name = self.get_localized_identifier(
                    equality.place, scope)
                new_production =\
                    self.generate_code(logical_and_helper1_name, ':=',
                                       inherited_place_name, token.lexeme,
                                       equality_place_name)
                logical_and_helper1_code.append_code(new_production)
                '''
                Logical operators do not perform the usual arithmetic
                conversions. Instead, they evaluate each operand in terms of
                its equivalence to 0. The result of a logical operation is
                either 0 or 1. The result's type is int.
                '''
                logical_and_helper1_production_type = 'int'
                logical_and_helper1 = self.check_logical_and_helper(
                    scope, logical_and_helper1_place,
                    logical_and_helper1_code.code,
                    logical_and_helper1_production_type)
                logical_and_helper = Production()
                logical_and_helper.place = logical_and_helper1.place
                logical_and_helper.code = logical_and_helper1.code
                logical_and_helper.production_type =\
                    logical_and_helper1.production_type
                return logical_and_helper
            logical_and_helper = Production()
            logical_and_helper.place = inherited_place
            logical_and_helper.code = inherited_code
            logical_and_helper.production_type = inherited_production_type
            return logical_and_helper
        self.set_eof_error(u'logical_and operator')

    def check_equality(self, scope):
        relational = self.check_relational(scope)
        equality_helper = self.check_equality_helper(
            scope, relational.place, relational.code,
            relational.production_type)
        equality = Production()
        equality.place = equality_helper.place
        equality.code = equality_helper.code
        equality.production_type = equality_helper.production_type
        return equality

    def check_equality_helper(self, scope, inherited_place, inherited_code,
                              inherited_production_type):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.lexeme in self.equality_operator_list:
                self.log_message(token)
                index = self.token_index = index + 1
                relational = self.check_relational(scope)
                equality_helper1_place = self.get_next_temporary_variable()
                equality_helper1_code = StandaloneCodeManager()
                equality_helper1_code.append_code(inherited_code)
                equality_helper1_code.append_code(relational.code)
                equality_helper1_name = self.get_localized_identifier(
                    equality_helper1_place, scope)
                inherited_place_name = self.get_localized_identifier(
                    inherited_place, scope)
                relational_place_name = self.get_localized_identifier(
                    relational.place, scope)
                new_production =\
                    self.generate_code(equality_helper1_name, ':=',
                                       inherited_place_name, token.lexeme,
                                       relational_place_name)
                equality_helper1_code.append_code(new_production)
                mock_production = Production()
                mock_production.place = inherited_place
                mock_production.code = inherited_code
                mock_production.production_type = inherited_production_type
                equality_helper1_production_type =\
                    self.calculate_resulting_production_type(mock_production,
                                                             relational)
                equality_helper1 = self.check_equality_helper(
                    scope, equality_helper1_place, equality_helper1_code.code,
                    equality_helper1_production_type)
                equality_helper = Production()
                equality_helper.place = equality_helper1.place
                equality_helper.code = equality_helper1.code
                equality_helper.production_type =\
                    equality_helper1.production_type
                return equality_helper
            equality_helper = Production()
            equality_helper.place = inherited_place
            equality_helper.code = inherited_code
            equality_helper.production_type = inherited_production_type
            return equality_helper
        self.set_eof_error(u'equality operator')

    def check_relational(self, scope):
        additive = self.check_additive(scope)
        relational_helper = self.check_relational_helper(
            scope, additive.place, additive.code,
            additive.production_type)
        relational = Production()
        relational.place = relational_helper.place
        relational.code = relational_helper.code
        relational.production_type = relational_helper.production_type
        return relational

    def check_relational_helper(self, scope, inherited_place, inherited_code,
                                inherited_production_type):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.lexeme in self.relational_operator_list:
                self.log_message(token)
                index = self.token_index = index + 1
                additive = self.check_additive(scope)
                relational_helper1_place = self.get_next_temporary_variable()
                relational_helper1_code = StandaloneCodeManager()
                relational_helper1_code.append_code(inherited_code)
                relational_helper1_code.append_code(additive.code)
                relational_helper1_name = self.get_localized_identifier(
                    relational_helper1_place, scope)
                inherited_place_name = self.get_localized_identifier(
                    inherited_place, scope)
                additive_place_name = self.get_localized_identifier(
                    additive.place, scope)
                new_production =\
                    self.generate_code(relational_helper1_name, ':=',
                                       inherited_place_name, token.lexeme,
                                       additive_place_name)
                relational_helper1_code.append_code(new_production)
                # Type checking
                mock_production = Production()
                mock_production.place = inherited_place
                mock_production.code = inherited_code
                mock_production.production_type = inherited_production_type

                relational_helper1_production_type =\
                    self.calculate_resulting_production_type(mock_production,
                                                             additive)

                relational_helper1 = self.check_relational_helper(
                    scope, relational_helper1_place,
                    relational_helper1_code.code,
                    relational_helper1_production_type)
                relational_helper = Production()
                relational_helper.place = relational_helper1.place
                relational_helper.code = relational_helper1.code
                relational_helper.production_type =\
                    relational_helper1.production_type
                return relational_helper
            relational_helper = Production()
            relational_helper.place = inherited_place
            relational_helper.code = inherited_code
            relational_helper.production_type = inherited_production_type
            return relational_helper
        self.set_eof_error(u'relational operator')

    def check_additive(self, scope):
        multiplicative = self.check_multiplicative(scope)
        additive_helper = self.check_additive_helper(
            scope, multiplicative.place, multiplicative.code,
            multiplicative.production_type)
        additive = Production()
        additive.place = additive_helper.place
        additive.code = additive_helper.code
        additive.production_type = additive_helper.production_type
        return additive

    def check_additive_helper(self, scope, inherited_place, inherited_code,
                              inherited_production_type):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.lexeme in self.additive_operator_list:
                self.log_message(token)
                index = self.token_index = index + 1
                multiplicative = self.check_multiplicative(scope)
                additive_helper1_place = self.get_next_temporary_variable()
                additive_helper1_code = StandaloneCodeManager()
                additive_helper1_code.append_code(inherited_code)
                additive_helper1_code.append_code(multiplicative.code)
                additive_helper1_name = self.get_localized_identifier(
                    additive_helper1_place, scope)
                inherited_place_name = self.get_localized_identifier(
                    inherited_place, scope)
                multiplicative_place_name = self.get_localized_identifier(
                    multiplicative.place, scope)
                new_production =\
                    self.generate_code(additive_helper1_name, ':=',
                                       inherited_place_name, token.lexeme,
                                       multiplicative_place_name)
                additive_helper1_code.append_code(new_production)
                mock_production = Production()
                mock_production.place = inherited_place
                mock_production.code = inherited_code
                mock_production.production_type = inherited_production_type
                additive_helper1_production_type =\
                    self.calculate_resulting_production_type(mock_production,
                                                             multiplicative)
                additive_helper1 = self.check_additive_helper(
                    scope, additive_helper1_place, additive_helper1_code.code,
                    additive_helper1_production_type)
                additive_helper = Production()
                additive_helper.place = additive_helper1.place
                additive_helper.code = additive_helper1.code
                additive_helper.production_type =\
                    additive_helper1.production_type
                return additive_helper
            additive_helper = Production()
            additive_helper.place = inherited_place
            additive_helper.code = inherited_code
            additive_helper.production_type = inherited_production_type
            return additive_helper
        self.set_eof_error(u'additive operator')

    def check_multiplicative(self, scope):
        unary_prefix = self.check_unary_prefix(scope)
        multiplicative_helper = self.check_multiplicative_helper(
            scope, unary_prefix.place, unary_prefix.code,
            unary_prefix.production_type)
        multiplicative = Production()
        multiplicative.place = multiplicative_helper.place
        multiplicative.code = multiplicative_helper.code
        multiplicative.production_type = multiplicative_helper.production_type
        return multiplicative

    def check_multiplicative_helper(self, scope, inherited_place,
                                    inherited_code, inherited_production_type):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.lexeme in self.multiplicative_operator_list:
                self.log_message(token)
                index = self.token_index = index + 1
                unary_prefix = self.check_unary_prefix(scope)
                multiplicative_helper1_place =\
                    self.get_next_temporary_variable()
                multiplicative_helper1_code = StandaloneCodeManager()
                multiplicative_helper1_code.append_code(inherited_code)
                multiplicative_helper1_code.append_code(unary_prefix.code)
                multiplicative_helper1_name = self.get_localized_identifier(
                    multiplicative_helper1_place, scope)
                inherited_place_name = self.get_localized_identifier(
                    inherited_place, scope)
                unary_prefix_name = self.get_localized_identifier(
                    unary_prefix.place, scope)
                new_production =\
                    self.generate_code(multiplicative_helper1_name, ':=',
                                       inherited_place_name, token.lexeme,
                                       unary_prefix_name)
                multiplicative_helper1_code.append_code(new_production)
                # The operands of the remainder operator (%) must be integral
                if token.lexeme == '%' and\
                        (inherited_production_type != 'int' or
                         unary_prefix.production_type != 'int'):
                    self.set_invalid_operands_error(
                        inherited_production_type,
                        unary_prefix.production_type, token)
                mock_production = Production()
                mock_production.place = inherited_place
                mock_production.code = inherited_code
                mock_production.production_type = inherited_production_type
                multiplicative_helper1_production_type =\
                    self.calculate_resulting_production_type(
                        mock_production, unary_prefix)
                multiplicative_helper1 = self.check_multiplicative_helper(
                    scope, multiplicative_helper1_place,
                    multiplicative_helper1_code.code,
                    multiplicative_helper1_production_type)
                multiplicative_helper = Production()
                multiplicative_helper.place = multiplicative_helper1.place
                multiplicative_helper.code = multiplicative_helper1.code
                multiplicative_helper.production_type =\
                    multiplicative_helper1.production_type
                return multiplicative_helper
            multiplicative_helper = Production()
            multiplicative_helper.place = inherited_place
            multiplicative_helper.code = inherited_code
            multiplicative_helper.production_type = inherited_production_type
            return multiplicative_helper
        self.set_eof_error(u'multiplicative operator')

    def check_unary_prefix(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.lexeme in self.unary_prefix_operator_list:
                self.log_message(token)
                unary_prefix_operator = token
                index = self.token_index = index + 1
                token = self.get_specific_token(index)
                if token:
                    expression_element = self.check_expression_element(scope)
                    if expression_element:
                        unary_prefix = Production()
                        unary_prefix.place = self.get_next_temporary_variable()
                        unary_prefix.append_code(expression_element.code)
                        new_production =\
                            self.generate_code(unary_prefix.place, ':=',
                                               unary_prefix_operator.lexeme,
                                               expression_element.place)
                        unary_prefix.append_code(new_production)
                        unary_prefix.production_type =\
                            expression_element.production_type
                        return unary_prefix
                    else:
                        self.set_syntactic_error(u'%s %s' % (
                            'T_ID or T_PARENTHESES_OPEN',
                            'or T_INTEGER or T_FLOAT'), token)
                else:
                    self.set_eof_error(u'%s %s' % (
                        'T_ID or T_PARENTHESES_OPEN',
                        'or T_INTEGER or T_FLOAT'))
            else:
                expression_element = self.check_expression_element(scope)
                return expression_element
        self.set_eof_error('+ ou -')

    def check_expression_element(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_PARENTHESES_OPEN':
                self.log_message(token)
                self.token_index = index = index + 1
                right_side_expression = self.check_right_side_expression(scope)
                index = self.token_index
                token = self.get_specific_token(self.token_index)
                if token:
                    if token.token_type == u'T_PARENTHESES_CLOSE':
                        self.log_message(token)
                        self.token_index = index + 1
                        return right_side_expression
                    self.set_syntactic_error(u'T_PARENTHESES_CLOSE', token)
                self.set_eof_error(u'T_PARENTHESES_CLOSE')
            elif token.token_type == u'T_ID':
                self.log_message(token)
                self.token_index = index + 1
                function_call = self.check_function_call(scope, token.lexeme)
                expression_element = Production()
                expression_element.code = function_call.code
                if function_call.place:
                    expression_element.place = function_call.place
                else:
                    expression_element.place = token.lexeme
                if self.symbols_table.exists(token.lexeme, scope, True):
                    identifier = self.symbols_table.get(token.lexeme, scope)
                    if 'int' in identifier.defined_type:
                        expression_element.production_type = 'int'
                    elif 'float' in identifier.defined_type:
                        expression_element.production_type = 'float'
                    elif 'double' in identifier.defined_type:
                        expression_element.production_type = 'double'
                    else:
                        expression_element.production_type =\
                            identifier.defined_type
                else:
                    self.set_undeclared_variable_error(token)
                return expression_element
            elif token.token_type == u'T_RESERVED_WORD' and\
                    (token.lexeme == u'true' or token.lexeme == u'false'):
                self.log_message(token)
                self.token_index = index + 1
                expression_element = Production()
                expression_element.place = '1'\
                    if token.lexeme == u'true' else '0'
                expression_element.production_type = 'int'
                return expression_element
            elif token.token_type == u'T_INTEGER' or\
                    token.token_type == u'T_FLOAT':
                self.log_message(token)
                self.token_index = index + 1
                expression_element = Production()
                expression_element.place = self.get_next_temporary_variable()
                if token.token_type == u'T_INTEGER':
                    expression_element.production_type = 'int'
                else:
                    expression_element.production_type = 'float'
                new_production = self.generate_code(
                    expression_element.place, ':=', token.lexeme)
                expression_element.append_code(new_production)
                return expression_element
            self.set_syntactic_error(u'%s %s' % ('T_ID or T_PARENTHESES_OPEN',
                                                 'or T_INTEGER or T_FLOAT'),
                                     token)
        self.set_eof_error(u'%s %s' % ('T_ID or T_PARENTHESES_OPEN',
                                       'or T_INTEGER or T_FLOAT'))

    def check_function_call(self, scope, function_identifier):
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_PARENTHESES_OPEN':
                self.log_message(token)
                self.token_index += 1
                function_argument = self.check_function_argument(
                    scope, function_identifier, 0)
                token = self.get_specific_token(self.token_index)
                if token:
                    if token.token_type == u'T_PARENTHESES_CLOSE':
                        self.log_message(token)
                        self.token_index += 1
                        function_call = Production()
                        function_call.place =\
                            self.get_next_temporary_variable()
                        function_token = self.symbols_table[
                            function_identifier]
                        new_production = self.generate_code(
                            function_call.place, ':=',
                            'call', function_identifier,
                            function_token.get_parameters_length(),
                            code_type='call')
                        function_call.append_code(function_argument.code)
                        function_call.append_code(new_production)
                        return function_call
                    self.set_syntactic_error(u'T_PARENTHESES_CLOSE', token)
                self.set_eof_error(u'T_PARENTHESES_CLOSE')
            return Production()
        self.set_eof_error(u'T_PARENTHESES_OPEN')

    def check_more_function_arguments(self, scope, function_identifier,
                                      argument_index):
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_COMMA':
                self.log_message(token)
                self.token_index += 1
                function_argument = self.check_function_argument(
                    scope, function_identifier, argument_index)
                if function_argument.place:
                    more_function_arguments1 =\
                        self.check_more_function_arguments(
                            scope, function_identifier, argument_index + 1)
                    more_function_arguments = Production()
                    more_function_arguments.append_code(function_argument.code)
                    more_function_arguments.append_code(
                        more_function_arguments1.code)
                    return more_function_arguments
                else:
                    # Expected an expression after a comma
                    token = self.get_specific_token(self.token_index)
                    self.set_syntactic_error('expression', token)
            # It is likely that there are no more expressions
            return Production()
        self.set_eof_error(u'T_COMMA')

    def check_function_argument(self, scope, function_identifier,
                                argument_index):
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_PARENTHESES_CLOSE':
                return Production()
        if len(self.symbols_table[function_identifier].
               parameters_set.elements) == argument_index:
            self.set_unexpected_parameter_error(
                function_identifier, argument_index)
        left_side_expression = self.check_left_side_expression(scope)
        right_side_expression = self.check_right_side_expression(scope)
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_COMMA':
                function_argument = Production()
                function_argument.append_code(
                    right_side_expression.code)
                function_argument.place = right_side_expression.place
                if left_side_expression.place:
                    new_production = self.generate_code(
                        left_side_expression.place, ':=',
                        right_side_expression.place)
                    function_argument.append_code(new_production)
                    function_argument.place = left_side_expression.place
                param_name = self.get_localized_identifier(
                    function_argument.place, scope)
                new_production = self.generate_code(
                    'param', param_name)
                function_argument.append_code(new_production)
                present_argument = self.symbols_table[function_identifier].\
                    parameters_set.get_element_by_index(argument_index)
                if present_argument and present_argument.defined_type !=\
                        right_side_expression.production_type:
                    self.set_implicit_conversion_warning(
                        present_argument.defined_type,
                        right_side_expression.production_type,
                        self.get_specific_token(self.token_index))
                more_function_arguments = self.check_more_function_arguments(
                    scope, function_identifier, argument_index + 1)
                function_argument.append_code(more_function_arguments.code)
                return function_argument
            else:
                function_argument = Production()
                function_argument.append_code(
                    right_side_expression.code)
                function_argument.place = right_side_expression.place
                if left_side_expression.place:
                    new_production = self.generate_code(
                        left_side_expression.place, ':=',
                        right_side_expression.place)
                    function_argument.append_code(new_production)
                    function_argument.place = left_side_expression.place
                param_name = self.get_localized_identifier(
                    function_argument.place, scope)
                new_production = self.generate_code(
                    'param', param_name)
                function_argument.append_code(new_production)
                return function_argument
        self.set_eof_error(u'T_COMMA')

    def check_block_argument(self, scope):
        left_side_expression = self.check_left_side_expression(scope)
        right_side_expression = self.check_right_side_expression(scope)
        if left_side_expression.place:
            block_argument = Production()
            left_side_expression_name = self.get_localized_identifier(
                left_side_expression.place, scope)
            right_side_expression_name = self.get_localized_identifier(
                right_side_expression.place, scope)
            new_production = self.generate_code(
                left_side_expression_name,
                left_side_expression.operator,
                right_side_expression_name)
            block_argument.append_code(right_side_expression.code)
            block_argument.append_code(new_production)
            return block_argument
        else:
            return right_side_expression

    def check_do_while(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'do':
                self.log_message(token)
                start_label = self.get_next_label()
                end_label = self.get_next_label()
                index = self.token_index = index + 1
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_CURLY_BRACKET_OPEN':
                        self.log_message(token)
                        index = self.token_index = index + 1
                        block_commands_list = self.check_block_commands_list(
                            scope, end_label, start_label)
                        index = self.token_index
                        token = self.get_specific_token(index)
                        if token:
                            if token.token_type == u'T_CURLY_BRACKET_CLOSE':
                                self.log_message(token)
                                self.token_index = index = index + 1
                                token = self.get_specific_token(index)
                                if token:
                                    if token.token_type == u'T_RESERVED_WORD'\
                                            and token.lexeme == u'while':
                                        self.log_message(token)
                                        index = self.token_index = index + 1
                                        token = self.get_specific_token(index)
                                        if token:
                                            if token.token_type ==\
                                                    u'T_PARENTHESES_OPEN':
                                                self.log_message(token)
                                                self.token_index = index + 1
                                                block_argument =\
                                                    self.check_block_argument(
                                                    scope)
                                                index = self.token_index
                                                token =\
                                                    self.get_specific_token(
                                                        index)
                                                if token:
                                                    if token.token_type ==\
                                                            u'T_PARENTHESES_CLOSE':
                                                        self.log_message(token)
                                                        index =\
                                                            self.token_index =\
                                                            index + 1
                                                        token = self.get_specific_token(index)
                                                        if token:
                                                            if token.token_type ==\
                                                                    u'T_SEMICOLON':
                                                                self.log_message(token)
                                                                index =\
                                                                    self.token_index =\
                                                                    index + 1
                                                                do_while = Production()
                                                                new_production1 =\
                                                                    self.generate_code(
                                                                        start_label, ':')
                                                                do_while.append_code(
                                                                    new_production1)
                                                                do_while.append_code(
                                                                    block_commands_list.code)
                                                                do_while.append_code(
                                                                    block_argument.code)
                                                                new_production2 =\
                                                                    self.generate_code(
                                                                        'if',
                                                                        block_argument.place,
                                                                        '=', '0',
                                                                        'goto', end_label)
                                                                do_while.append_code(
                                                                    new_production2)
                                                                new_production3 =\
                                                                    self.generate_code(
                                                                        'goto', start_label)
                                                                do_while.append_code(
                                                                    new_production3)
                                                                new_production4 =\
                                                                    self.generate_code(
                                                                        end_label, ':')
                                                                do_while.append_code(
                                                                    new_production4)
                                                                return do_while
                                                            self.set_syntactic_error(
                                                                u'T_SEMICOLON',
                                                                token)
                                                        self.set_eof_error(
                                                            u'T_SEMICOLON')
                                                    self.set_syntactic_error(
                                                        u'T_PARENTHESES_CLOSE',
                                                        token)
                                                self.set_eof_error(
                                                    u'T_PARENTHESES_CLOSE')
                                            self.set_syntactic_error(
                                                u'T_PARENTHESES_OPEN', token)
                                        self.set_eof_error(
                                            u'T_PARENTHESES_OPEN')
                                    self.set_syntactic_error(u'while', token)
                                self.set_eof_error(u'while')
                            self.set_syntactic_error(u'T_CURLY_BRACKET_CLOSE',
                                                     token)
                        self.set_eof_error(u'T_CURLY_BRACKET_CLOSE')
                    self.set_syntactic_error(u'T_CURLY_BRACKET_OPEN', token)
                self.set_eof_error(u'T_CURLY_BRACKET_OPEN')
            self.set_syntactic_error(u'do', token)
        self.set_eof_error(u'do')

    def check_while(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'while':
                self.log_message(token)
                index = self.token_index = index + 1
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_PARENTHESES_OPEN':
                        self.log_message(token)
                        self.token_index = index + 1
                        block_argument = self.check_block_argument(scope)
                        start_label = self.get_next_label()
                        end_label = self.get_next_label()
                        index = self.token_index
                        token = self.get_specific_token(index)
                        if token:
                            if token.token_type == u'T_PARENTHESES_CLOSE':
                                self.log_message(token)
                                index = self.token_index = index + 1
                                token = self.get_specific_token(index)
                                if token:
                                    if token.token_type ==\
                                            u'T_CURLY_BRACKET_OPEN':
                                        self.log_message(token)
                                        index = self.token_index = index + 1
                                        block_commands_list =\
                                            self.check_block_commands_list(
                                                scope, end_label, start_label)
                                        index = self.token_index
                                        token = self.get_specific_token(index)
                                        if token:
                                            if token.token_type ==\
                                                    u'T_CURLY_BRACKET_CLOSE':
                                                self.log_message(token)
                                                self.token_index = index =\
                                                    index + 1
                                                _while = Production()
                                                new_production1 =\
                                                    self.generate_code(
                                                        start_label, ':')
                                                _while.append_code(
                                                    new_production1)
                                                _while.append_code(
                                                    block_argument.code)
                                                new_production2 =\
                                                    self.generate_code(
                                                        'if',
                                                        block_argument.place,
                                                        '=', '0',
                                                        'goto', end_label)
                                                _while.append_code(
                                                    new_production2)
                                                _while.append_code(
                                                    block_commands_list.code)
                                                new_production3 =\
                                                    self.generate_code(
                                                        'goto', start_label)
                                                _while.append_code(
                                                    new_production3)
                                                new_production4 =\
                                                    self.generate_code(
                                                        end_label, ':')
                                                _while.append_code(
                                                    new_production4)
                                                return _while
                                            self.set_syntactic_error(
                                                u'T_CURLY_BRACKET_CLOSE',
                                                token)
                                        self.set_eof_error(
                                            u'T_CURLY_BRACKET_CLOSE')
                                    self.set_syntactic_error(
                                        u'T_CURLY_BRACKET_OPEN', token)
                                self.set_eof_error(u'T_CURLY_BRACKET_OPEN')
                            self.set_syntactic_error(u'T_PARENTHESES_CLOSE',
                                                     token)
                        self.set_eof_error(u'T_PARENTHESES_CLOSE')
                    self.set_syntactic_error(u'T_PARENTHESES_OPEN', token)
                self.set_eof_error(u'T_PARENTHESES_OPEN')
            self.set_syntactic_error(u'while', token)
        self.set_eof_error(u'while')

    def check_if(self, scope, break_label=None, continue_label=None):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'if':
                self.token_index += 1
                self.log_message(token)
                if_parentheses = self.check_if_parentheses(
                    scope, inherited_end_label=None,
                    break_label=break_label,
                    continue_label=continue_label)
                return if_parentheses
            self.set_syntactic_error(u'if', token)
        self.set_eof_error(u'if')

    # Helper function, not in the grammar
    def check_if_parentheses(self, scope, inherited_end_label,
                             break_label=None, continue_label=None):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_PARENTHESES_OPEN':
                self.log_message(token)
                self.token_index = index + 1
                block_argument = self.check_block_argument(scope)
                index = self.token_index
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_PARENTHESES_CLOSE':
                        self.log_message(token)
                        self.token_index = index + 1
                        token = self.get_specific_token(self.token_index)
                        if token:
                            if token.token_type == u'T_CURLY_BRACKET_OPEN':
                                block_curly_brackets =\
                                    self.check_block_curly_brackets(
                                        scope, break_label, continue_label)
                                if not inherited_end_label:
                                    end_label = self.get_next_label()
                                else:
                                    end_label = inherited_end_label
                                _else = self.check_else(
                                    scope, end_label, break_label, continue_label)
                                if_parentheses = Production()
                                else_label = None
                                if _else.code:
                                    else_label = self.get_next_label()
                                if_parentheses.append_code(block_argument.code)
                                if _else.code:
                                    new_production = self.generate_code(
                                        'if', block_argument.place, '=', '0',
                                        'goto', else_label)
                                    if_parentheses.append_code(new_production)
                                    if_parentheses.append_code(
                                        block_curly_brackets.code)
                                    new_production2 = self.generate_code(
                                        'goto', end_label)
                                    if_parentheses.append_code(new_production2)
                                    new_production3 = self.generate_code(
                                        else_label, ':')
                                    if_parentheses.append_code(new_production3)
                                    if_parentheses.append_code(_else.code)
                                    if not inherited_end_label:
                                        new_production4 = self.generate_code(
                                            end_label, ':')
                                        if_parentheses.append_code(new_production4)
                                else:
                                    new_production = self.generate_code(
                                        'if', block_argument.place, '=', '0',
                                        'goto', end_label)
                                    if_parentheses.append_code(new_production)
                                    if_parentheses.append_code(
                                        block_curly_brackets.code)
                                    new_production2 = self.generate_code(
                                        end_label, ':')
                                    if_parentheses.append_code(new_production2)
                                return if_parentheses
                            else:
                                one_line_if_block = self.check_one_line_if_block(
                                    scope, break_label, continue_label)
                                if not inherited_end_label:
                                    end_label = self.get_next_label()
                                else:
                                    end_label = inherited_end_label
                                _else = self.check_else(
                                    scope, end_label, break_label, continue_label)
                                if_parentheses = Production()
                                else_label = None
                                if _else.code:
                                    else_label = self.get_next_label()
                                if_parentheses.append_code(block_argument.code)
                                if _else.code:
                                    new_production = self.generate_code(
                                        'if', block_argument.place, '=', '0',
                                        'goto', else_label)
                                    if_parentheses.append_code(new_production)
                                    if_parentheses.append_code(
                                        one_line_if_block.code)
                                    new_production2 = self.generate_code(
                                        'goto', end_label)
                                    if_parentheses.append_code(new_production2)
                                    new_production3 = self.generate_code(
                                        else_label, ':')
                                    if_parentheses.append_code(new_production3)
                                    if_parentheses.append_code(_else.code)
                                    if not inherited_end_label:
                                        new_production4 = self.generate_code(
                                            end_label, ':')
                                        if_parentheses.append_code(new_production4)
                                else:
                                    new_production = self.generate_code(
                                        'if', block_argument.place, '=', '0',
                                        'goto', end_label)
                                    if_parentheses.append_code(new_production)
                                    if_parentheses.append_code(
                                        one_line_if_block.code)
                                    new_production2 = self.generate_code(
                                        end_label, ':')
                                    if_parentheses.append_code(new_production2)
                                return if_parentheses
                            self.set_syntactic_error(u'T_CURLY_BRACKETS_OPEN or an one line block', token)
                        self.set_eof_error(u'T_CURLY_BRACKETS_OPEN or an one line block')
                    self.set_syntactic_error(u'T_PARENTHESES_CLOSE', token)
                self.set_eof_error(u'T_PARENTHESES_CLOSE')
            self.set_syntactic_error(u'T_PARENTHESES_OPEN', token)
        self.set_eof_error(u'T_PARENTHESES_OPEN')

    def check_one_line_if_block(self, scope, break_label=None,
                                continue_label=None):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_ID':
                one_line_if_block = self.check_expression(scope)
                return one_line_if_block
            elif token.token_type == u'T_RESERVED_WORD' and\
                    (token.lexeme == u'break' or
                     token.lexeme == u'continue'):
                one_line_if_block = self.check_single_word_command(
                    scope, break_label, continue_label)
                return one_line_if_block
            elif token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'return':
                one_line_if_block = self.check_return(scope)
                return one_line_if_block
            self.set_syntactic_error(u'T_ID or T_RESERVED_WORD', token)
        self.set_eof_error(u'T_ID or T_RESERVED_WORD')

    # Helper function, not in the grammar
    def check_block_curly_brackets(self, scope, break_label=None,
                                   continue_label=None):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_CURLY_BRACKET_OPEN':
                self.log_message(token)
                self.token_index = index + 1
                block_curly_brackets = self.check_block_commands_list(
                    scope, break_label, continue_label)
                index = self.token_index
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_CURLY_BRACKET_CLOSE':
                        self.log_message(token)
                        self.token_index = index + 1
                        return block_curly_brackets
                    self.set_syntactic_error(u'T_CURLY_BRACKET_CLOSE', token)
                self.set_eof_error(u'T_CURLY_BRACKET_CLOSE')
            self.set_syntactic_error(u'T_CURLY_BRACKET_OPEN', token)
        self.set_eof_error(u'T_CURLY_BRACKET_OPEN')

    def check_else(self, scope, inherited_end_label, break_label=None,
                   continue_label=None):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'else':
                self.log_message(token)
                index = self.token_index = index + 1
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_RESERVED_WORD' and\
                            token.lexeme == u'if':
                        self.log_message(token)
                        index = self.token_index = index + 1
                        if_parentheses = self.check_if_parentheses(
                            scope, inherited_end_label, break_label,
                            continue_label)
                        return if_parentheses
                    elif token.token_type == u'T_CURLY_BRACKET_OPEN':
                        block_curly_brackets =\
                            self.check_block_curly_brackets(
                                scope, break_label, continue_label)
                        return block_curly_brackets
                    else:
                        one_line_if_block = self.check_one_line_if_block(
                            scope, break_label, continue_label)
                        return one_line_if_block
                    self.set_syntactic_error(u'if', token)
                self.set_eof_error(u'if')
            return Production()
            self.set_syntactic_error(u'else', token)
        self.set_eof_error(u'else')

    def check_for(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_RESERVED_WORD' and\
                    token.lexeme == u'for':
                self.log_message(token)
                index = self.token_index = index + 1
                check_for_parentheses = self.check_for_parentheses(scope)
                return check_for_parentheses
            self.set_syntactic_error(u'for', token)
        self.set_eof_error(u'for')

    # Helper function, not in the grammar
    def check_for_parentheses(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        start_label = self.get_next_label()
        end_label = self.get_next_label()
        if token:
            if token.token_type == u'T_PARENTHESES_OPEN':
                self.log_message(token)
                self.token_index = index + 1
                for_parameters = self.check_for_parameters(scope)
                index = self.token_index
                token = self.get_specific_token(index)
                if token:
                    if token.token_type == u'T_PARENTHESES_CLOSE':
                        self.log_message(token)
                        self.token_index = index + 1
                        block_curly_brackets = self.check_block_curly_brackets(
                            scope, end_label, start_label)
                        for_parentheses = Production()
                        for_parentheses.append_code(for_parameters.code)
                        new_production1 = self.generate_code(start_label, ':')
                        for_parentheses.append_code(new_production1)
                        for_parentheses.append_code(
                            for_parameters.condition_code)
                        new_production2 = self.generate_code(
                            'if', for_parameters.place, '=', '0',
                            'goto', end_label)
                        for_parentheses.append_code(new_production2)
                        for_parentheses.append_code(block_curly_brackets.code)
                        for_parentheses.append_code(
                            for_parameters.increment_code)
                        new_production3 = self.generate_code(
                            'goto', start_label)
                        for_parentheses.append_code(new_production3)
                        new_production4 = self.generate_code(end_label, ':')
                        for_parentheses.append_code(new_production4)
                        return for_parentheses
                    self.set_syntactic_error(u'T_PARENTHESES_CLOSE', token)
                self.set_eof_error(u'T_PARENTHESES_CLOSE')
            self.set_syntactic_error(u'T_PARENTHESES_OPEN', token)
        self.set_eof_error(u'T_PARENTHESES_OPEN')

    # Helper function, not in the grammar
    def check_for_parameters(self, scope):
        for_first_parameter = self.check_for_first_parameter(scope)
        token = self.get_specific_token(self.token_index)
        if token:
            if token.token_type == u'T_SEMICOLON':
                self.log_message(token)
                self.token_index += 1
                for_parameter_expression1 =\
                    self.check_for_parameter_expression(scope)
                token = self.get_specific_token(self.token_index)
                if token:
                    if token.token_type == u'T_SEMICOLON':
                        self.log_message(token)
                        self.token_index += 1
                        for_parameter_expression2 =\
                            self.check_for_parameter_expression(scope)
                        for_parameters = Production()
                        for_parameters.append_code(for_first_parameter.code)
                        for_parameters.place =\
                            for_parameter_expression1.place
                        for_parameters.condition_code =\
                            for_parameter_expression1.code
                        for_parameters.increment_code =\
                            for_parameter_expression2.code
                        return for_parameters
                    self.set_syntactic_error(u'T_SEMICOLON', token)
                self.set_eof_error(u'T_SEMICOLON')
            self.set_syntactic_error(u'T_SEMICOLON', token)
        self.set_eof_error(u'T_SEMICOLON')

    def check_for_first_parameter(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_SEMICOLON':
                return Production()
            else:
                expression = self.check_for_expression(scope)
                more_for_expressions = self.check_more_for_expressions(scope)
                for_first_parameter = Production()
                for_first_parameter.append_code(expression.code)
                for_first_parameter.append_code(more_for_expressions.code)
                return for_first_parameter

    def check_for_expression(self, scope):
        left_side_expression = self.check_left_side_expression(scope)
        right_side_expression = self.check_right_side_expression(scope)
        if left_side_expression.place:
            if right_side_expression.place:
                for_expression = Production()
                left_side_expression_name = self.get_localized_identifier(
                    left_side_expression.place, scope)
                right_side_expression_name = self.get_localized_identifier(
                    right_side_expression.place, scope)
                new_production = self.generate_code(
                    left_side_expression_name,
                    left_side_expression.operator,
                    right_side_expression_name)
                for_expression.append_code(right_side_expression.code)
                for_expression.append_code(new_production)
                for_expression.place = left_side_expression.place
                return for_expression
            else:
                for_expression = Production()
                for_expression.place = left_side_expression.place
                return for_expression
        else:
            if right_side_expression.place:
                expression = Production()
                if any('call' in string for string
                        in right_side_expression.code):
                    expression.append_code(right_side_expression.code)
                return expression
            else:
                return Production()

    def check_more_for_expressions(self, scope):
        index = self.token_index
        token = self.get_specific_token(index)
        if token:
            if token.token_type == u'T_COMMA':
                self.log_message(token)
                self.token_index = index + 1
                for_expression = self.check_for_expression(scope)
                more_for_expressions1 =\
                    self.check_more_for_expressions(scope)
                more_for_expressions = Production()
                more_for_expressions.append_code(for_expression.code)
                more_for_expressions.append_code(more_for_expressions1.code)
                return more_for_expressions
            more_for_expressions = Production()
            return more_for_expressions
        more_for_expressions = Production()
        return more_for_expressions

    def check_for_parameter_expression(self, scope):
        token = self.get_specific_token(self.token_index)
        if token:
            # Empty Expression
            if token.token_type == u'T_PARENTHESES_CLOSE' or\
                    token.token_type == u'T_SEMICOLON':
                # Empty condition expression
                if token.token_type == u'T_SEMICOLON':
                    for_expression = Production()
                    for_expression.place =\
                        self.get_next_temporary_variable()
                    new_production = self.generate_code(
                        for_expression.place, ':=', '1')
                    for_expression.append_code(new_production)
                    return for_expression
                # Empty loop expression
                else:
                    for_expression = Production()
                    return for_expression
            else:
                left_side_expression =\
                    self.check_left_side_expression(scope)
                right_side_expression =\
                    self.check_right_side_expression(scope)
                if left_side_expression.place:
                    for_parameter_expression = Production()
                    left_side_expression_name = self.get_localized_identifier(
                        left_side_expression.place, scope)
                    right_side_expression_name = self.get_localized_identifier(
                        right_side_expression.place, scope)
                    new_production = self.generate_code(
                        left_side_expression_name,
                        left_side_expression.operator,
                        right_side_expression_name)
                    for_parameter_expression.append_code(
                        right_side_expression.code)
                    for_parameter_expression.place =\
                        left_side_expression_name
                    for_parameter_expression.append_code(new_production)
                    return for_parameter_expression
                elif right_side_expression.place:
                    return right_side_expression
                else:
                    for_expression = Production()
                    for_expression.place =\
                        self.get_next_temporary_variable()
                    new_production = self.generate_code(
                        for_expression.place, ':=', '1')
                    for_expression.append_code(new_production)
                    return for_expression
            self.set_syntactic_error(
                u'T_PARENTHESES_CLOSE or T_SEMICOLON', token)
        self.set_eof_error(u'T_PARENTHESES_CLOSE or T_SEMICOLON')
