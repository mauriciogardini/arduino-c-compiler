#!/usr/bin/python
# -*- coding: utf-8 -*-

class Token():
    def __str__(self):
        return u'%s - "%s" (%i, %i)' % (self.token_type, self.lexeme,
            self.line, self.column)

    def __init__(self, token_type, lexeme, line, column):
        self.token_type = token_type
        self.lexeme = lexeme
        self.line = line
        self.column = column

class FileManager():
    def __init__(self, file_path):
        self.content = self.read_file_content(file_path)
        self.line = 0
        self.column = 0

    def print_all(self):
        for i in self.content:
            print i

    def read_file_content(self, file_path):
        with open(file_path, u'r') as input_file:
            return input_file.readlines()

    def get_next_char(self):
        if self.line < len(self.content) and\
            self.column >= len(self.content[self.line]):
            self.column = 0
            self.line += 1
        if self.line >= len(self.content):
            return None
        next_char = self.content[self.line][self.column]
        self.column += 1
        if self.line < len(self.content) and\
            self.column >= len(self.content[self.line]):
            self.column = 0
            self.line += 1
        return next_char

    def get_specific_char(self, line, column):
        if self.line < len(self.content) and\
            self.column < len(self.content[self.line]):
            return self.content[line][column]
        return None

    def get_current_position(self):
        return (self.line, self.column)

    def set_current_position(self, line, column):
        self.line = line
        self.column = column

class LexicalAnalyser():
    def __init__(self, input_file):
        self.content = None
        self.current_position = 0
        self.generated_tokens = []
        self.file_manager = FileManager(input_file)
        self.possible_tokens = self.get_list_of_tokens()
        self.reserved_words = self.get_list_of_reserved_words()

    def get_list_of_reserved_words(self):
        constants = [
            u'HIGH', u'LOW', u'INPUT', u'OUTPUT', u'INPUT_PULLUP'
        ]
        keywords = [
            u'auto', u'boolean', u'break', u'case', u'char', u'const',
            u'continue', u'default', u'do', u'double', u'else', u'enum',
            u'extern', u'false', u'float', u'for', u'goto', u'if', u'int',
            u'long', u'register', u'return', u'short', u'signed', u'sizeof',
            u'static', u'struct', u'switch', u'true', u'typedef', u'union',
            u'unsigned', u'void', u'volatile', u'word', u'while'
        ]
        operators = [
            u'and', u'and_eq', u'bitand', u'bitor', u'compl', u'not', u'or',
            u'or_eq', u'sizeof', u'type', u'typeid', u'xor', u'xor_eq'
        ]

        reserved_words = [
            u'loop', u'setup'
        ]

        return constants + keywords + operators + reserved_words

    def get_list_of_tokens(self):
        tokens = {
            u'(': self.process_parentheses_open,
            u')': self.process_parentheses_close,
            u'[': self.process_square_brackets_open,
            u']': self.process_square_brackets_close,
            u'{': self.process_curly_brackets_open,
            u'}': self.process_curly_brackets_close,
            u'=': self.process_assignment,
            u'!': self.process_not,
            u'~': self.process_bitwise_not,
            u'^': self.process_bitwise_xor,
            u'&': self.process_bitwise_and,
            u'|': self.process_bitwise_or,
            u'>': self.process_greater_than,
            u'<': self.process_lower_than,
            u'.': self.process_dot,
            u',': self.process_comma,
            u':': self.process_colon,
            u';': self.process_semicolon,
            u'+': self.process_plus,
            u'-': self.process_minus,
            u'*': self.process_times,
            u'/': self.process_divide,
            u'%': self.process_modulo,
            u'?': self.process_question_mark
        }

        # Generate the token dictionary keys for the blank characters.
        blank_keys = [u' ', u'\r', u'\n', u'\t']
        blank_tokens = {key: self.process_blank for key in blank_keys}

        # Generate the token dictionary keys for the alphabet letters.
        lowercase_letters = map(unichr, range(ord(u'a'), ord(u'z') + 1))
        uppercase_letters = map(unichr, range(ord(u'A'), ord(u'Z') + 1))
        symbols = ['_']
        id_keys = symbols + lowercase_letters + uppercase_letters
        id_tokens = {key: self.process_id for key in id_keys}

        # Generate the token dictionary for the numbers.
        number_keys = map(unichr, range(ord(u'0'), ord(u'9') + 1))
        number_tokens = {key: self.process_integer for key in number_keys}

        tokens = dict(tokens.items() + id_tokens.items() +\
            number_tokens.items() + blank_tokens.items())
        return tokens

    def write_token_file(self):
        with open(u'output.lex', u'a') as output_file:
            for token in self.generated_tokens:
                output_file.write(token.__str__() + u'\n')

    def generate_token(self, token_type, lexeme, line, column):
        self.generated_tokens.append(Token(token_type, lexeme, line, column))

    def get_tokens(self):
        line, column = self.file_manager.get_current_position()
        current_character = self.file_manager.get_next_char()
        while current_character:
            self.possible_tokens[current_character](line, column)
            line, column = self.file_manager.get_current_position()
            current_character = self.file_manager.get_next_char()
        #self.write_token_file()
        return self.generated_tokens

    def is_id(self, character):
        return (character >= 'a' and character <= 'z') or\
            (character >= 'A' and character <= 'Z') or character == '_'

    def is_integer(self, character):
        return character >= '0' and character <= '9'

    def process_parentheses_open(self, line, column):
        self.generate_token(u'T_PARENTHESES_OPEN', u'(', line, column)

    def process_parentheses_close(self, line, column):
        self.generate_token(u'T_PARENTHESES_CLOSE', u')', line, column)

    def process_square_brackets_open(self, line, column):
        self.generate_token(u'T_SQUARE_BRACKET_OPEN', u'[', line, column)

    def process_square_brackets_close(self, line, column):
        self.generate_token(u'T_SQUARE_BRACKET_CLOSE', u']', line, column)

    def process_curly_brackets_open(self, line, column):
        self.generate_token(u'T_CURLY_BRACKET_OPEN', u'{', line, column)

    def process_curly_brackets_close(self, line, column):
        self.generate_token(u'T_CURLY_BRACKET_CLOSE', u'}', line, column)

    def process_assignment(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_EQUAL_TO', u'==', line, column)
            return
        self.generate_token(u'T_ASSIGN', u'=', line, column)

    def process_not(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_DIFFERENT', u'!=', line, column)
            return
        self.generate_token(u'T_NOT', u'!', line, column)

    def process_bitwise_not(self, line, column):
        self.generate_token(u'T_BITWISE_NOT', u'~', line, column)

    def process_bitwise_xor(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_BITWISE_XOR_ASSIGNMENT',
                u'^=', line, column)
            return
        self.generate_token(u'T_BITWISE_XOR', u'^', line, column)

    def process_bitwise_and(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'&':
            self.file_manager.get_next_char()
            self.generate_token(u'T_AND', u'&&', line, column)
            return
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_BITWISE_AND_ASSIGNMENT',
                u'&=', line, column)
            return
        self.generate_token(u'T_BITWISE_AND', u'&', line, column)

    def process_bitwise_or(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'|':
            self.file_manager.get_next_char()
            self.generate_token(u'T_OR', u'||', line, column)
            return
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_BITWISE_OR_ASSIGNMENT',
                u'|=', line, column)
            return
        self.generate_token(u'T_BITWISE_OR', u'|', line, column)

    def process_greater_than(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_GREATER_THAN_OR_EQUAL_TO',
                u'>=', line, column)
            return
        if next_character == u'>':
            next_character = self.file_manager.get_specific_char(
                self.file_manager.line, self.file_manager.column + 1)
            if next_character == u'=':
                self.file_manager.get_next_char()
                self.file_manager.get_next_char()
                self.generate_token(u'T_BITWISE_RIGHT_ASSIGNMENT',
                    u'>>=', line, column)
                return
            self.file_manager.get_next_char()
            self.generate_token(u'T_BITWISE_RIGHT_SHIFT', u'>>', line, column)
            return
        self.generate_token(u'T_GREATER_THAN', u'>', line, column)

    def process_lower_than(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_LOWER_THAN_OR_EQUAL_TO',
                u'<=', line, column)
            return
        if next_character == u'<':
            next_character = self.file_manager.get_specific_char(
                self.file_manager.line, self.file_manager.column + 1)
            if next_character == u'=':
                self.file_manager.get_next_char()
                self.file_manager.get_next_char()
                self.generate_token(u'T_BITWISE_LEFT_ASSIGNMENT',
                    u'<<=', line, column)
                return
            self.file_manager.get_next_char()
            self.generate_token(u'T_BITWISE_LEFT_SHIFT', u'<<', line, column)
            return
        self.generate_token(u'T_LOWER_THAN', u'<', line, column)

    def process_dot(self, line, column):
        current_position = self.file_manager.get_current_position()
        lexeme = self.file_manager.get_specific_char(line, column)
        internal_character_position = current_position[1]
        character = self.file_manager.get_specific_char(current_position[0],
            current_position[1])
        while self.is_integer(character):
            lexeme += character
            internal_character_position += 1
            character = self.file_manager.get_specific_char(\
                self.file_manager.line, internal_character_position)
        self.file_manager.set_current_position(self.file_manager.line,
            internal_character_position)
        if lexeme != u'.':
            self.generate_token(u'T_FLOAT', lexeme, line, column)
        else:
            self.generate_token(u'T_DOT', u'.', line, column)

    def process_comma(self, line, column):
        self.generate_token(u'T_COMMA', u',', line, column)

    def process_colon(self, line, column):
        self.generate_token(u'T_COLON', u':', line, column)

    def process_semicolon(self, line, column):
        self.generate_token(u'T_SEMICOLON', u';', line, column)

    def process_plus(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'+':
            self.file_manager.get_next_char()
            self.generate_token(u'T_INCREMENT', u'++', line, column)
            return
        elif next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_COMPOUND_ADDITION', u'+=', line, column)
            return
        self.generate_token(u'T_ADDITION', u'+', line, column)

    def process_minus(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'-':
            self.file_manager.get_next_char()
            self.generate_token(u'T_DECREMENT', u'--', line, column)
            return
        if next_character == u'>':
            self.file_manager.get_next_char()
            self.generate_token(u'T_ARROW', u'->', line, column)
            return
        elif next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_COMPOUND_SUBTRACTION', u'-=', line, column)
            return
        self.generate_token(u'T_SUBTRACTION', u'-', line, column)

    def process_times(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'/':
            self.file_manager.get_next_char()
            self.generate_token(u'T_MULTI_LINE_COMMENT_END',
                u'*/', line, column)
            return
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_COMPOUND_MULTIPLICATION',
                u'*=', line, column)
            return
        self.generate_token(u'T_MULTIPLICATION', u'*', line, column)

    def process_divide(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'/':
            self.file_manager.get_next_char()
            self.generate_token(u'T_SINGLE_LINE_COMMENT', u'//', line, column)
            return
        if next_character == u'*':
            self.file_manager.get_next_char()
            self.generate_token(u'T_MULTI_LINE_COMMENT_START',
                u'/*', line, column)
            return
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_COMPOUND_DIVISION', u'/=', line, column)
            return
        self.generate_token(u'T_DIVISION', u'/', line, column)

    def process_modulo(self, line, column):
        next_character = self.file_manager.get_specific_char(
            self.file_manager.line, self.file_manager.column)
        if next_character == u'=':
            self.file_manager.get_next_char()
            self.generate_token(u'T_COMPOUND_MODULO', u'%=', line, column)
            return
        self.generate_token(u'T_MODULO', u'%', line, column)

    def process_question_mark(self, line, column):
        self.generate_token(u'T_QUESTION_MARK', u'?', line, column)

    def process_id(self, line, column):
        current_position = self.file_manager.get_current_position()
        lexeme = self.file_manager.get_specific_char(line, column)
        internal_character_position = current_position[1]
        character = self.file_manager.get_specific_char(current_position[0],
            current_position[1])
        while self.is_id(character) or self.is_integer(character):
            lexeme += character
            internal_character_position += 1
            character = self.file_manager.get_specific_char(\
                self.file_manager.line, internal_character_position)
        self.file_manager.set_current_position(current_position[0],
            internal_character_position)
        if lexeme in self.reserved_words:
            self.generate_token(u'T_RESERVED_WORD', lexeme, line, column)
        else:
            self.generate_token(u'T_ID', lexeme, line, column)

    def process_integer(self, line, column):
        current_position = self.file_manager.get_current_position()
        lexeme = self.file_manager.get_specific_char(line, column)
        internal_character_position = current_position[1]
        character = self.file_manager.get_specific_char(current_position[0],
            current_position[1])
        while self.is_integer(character):
            lexeme += character
            internal_character_position += 1
            character = self.file_manager.get_specific_char(\
                self.file_manager.line, internal_character_position)
        if character == u'.':
            lexeme += u'.'
            internal_character_position += 1
            character = self.file_manager.get_specific_char(current_position[0],
                internal_character_position)
            while self.is_integer(character):
                lexeme += character
                internal_character_position += 1
                character = self.file_manager.get_specific_char(\
                    self.file_manager.line, internal_character_position)
        self.file_manager.set_current_position(self.file_manager.line,
            internal_character_position)
        if lexeme.find(u'.') > 0:
            self.generate_token(u'T_FLOAT', lexeme, line, column)
        else:
            self.generate_token(u'T_INTEGER', lexeme, line, column)

    def process_blank(self, line, column):
        return
