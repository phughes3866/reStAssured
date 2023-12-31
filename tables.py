# -*- coding: utf-8 -*-

"""
This is a SublimeText 2 adaptation of `Vincent Driessen's vim-rst-tables` [1]_ code
by Martín Gaitán <gaitan@gmail.com>

.. [1]: https://github.com/nvie/vim-rst-tables

Usage
-----

1. Set reStructuredText as syntax (or open a .rst)
2. Create some kind of table outline::

      This is paragraph text *before* the table.

      Column 1  Column 2
      Foo  Put two (or more) spaces as a field separator.
      Bar  Even very very long lines like these are fine, as long as you do not put in line endings here.
      Qux  This is the last line.

      This is paragraph text *after* the table.

2. Put your cursor somewhere in the content to convert as table.

3. Press ``ctrl+t`` (to create the table).  The output will look something like
   this::

      This is paragraph text *before* the table.

      +----------+---------------------------------------------------------+
      | Column 1 | Column 2                                                |
      +==========+=========================================================+
      | Foo      | Put two (or more) spaces as a field separator.          |
      +----------+---------------------------------------------------------+
      | Bar      | Even very very long lines like these are fine, as long  |
      |          | as you do not put in line endings here.                 |
      +----------+---------------------------------------------------------+
      | Qux      | This is the last line.                                  |
      +----------+---------------------------------------------------------+

      This is paragraph text *after* the table.

.. tip::

   Change something in the output table and run ``ctrl+t`` again: Magically,
   it will be fixed.

   And ``ctrl+r+t`` reflows the table fixing the current column width.
"""

import re
import textwrap
from .utils.textcommandUtils import BaseBlockCommand

# try:
#     from .helpers import BaseBlockCommand
# except ValueError:
#     from helpers import BaseBlockCommand    # NOQA

import os
import sys
# wcwidth_dir = os.path.join(os.path.dirname(__file__), 'wcwidth')
# sys.path.insert(0, wcwidth_dir)
# import wcwidth
from .wcwidth import wcwidth


class TableCommand(BaseBlockCommand):

    def get_withs(self, lines):
        return None

    def get_result(self, indent, table, widths):
        result = '\n'.join(draw_table(indent, table, widths))
        result += '\n'
        return result

    def run(self, edit):
        region, lines, indent = self.get_block_bounds()
        table = parse_table(lines)
        widths = self.get_withs(lines)
        result = self.get_result(indent, table, widths)
        self.view.replace(edit, region, result)


class FlowtableCommand(TableCommand):

    def get_withs(self, lines):
        return get_column_widths_from_border_spec(lines)


class BaseMergeCellsCommand(BaseBlockCommand):

    def get_column_index(self, raw_line, col_position):
        """given the raw line and the column col cursor position,
           return the table column index to merge"""
        return raw_line[:col_position].count('|')


class MergeCellsDownCommand(BaseMergeCellsCommand):
    offset = 1

    def run(self, edit):
        region, lines, indent= self.get_block_bounds()
        raw_table = self.view.substr(region).split('\n')
        begin = self.view.rowcol(region.begin())[0]
        # end = self.view.rowcol(region.end())[0]
        cursor = self.get_cursor_position()
        actual_line = raw_table[cursor[0] - begin]
        col = self.get_column_index(actual_line, cursor[1])
        sep_line = raw_table[cursor[0] + self.offset - begin]
        new_sep_line = self.update_sep_line(sep_line, col)
        raw_table[cursor[0] + self.offset - begin] = indent + new_sep_line
        result = '\n'.join(raw_table)
        self.view.replace(edit, region, result)


    def update_sep_line(self, original, col):
        segments = original.strip().split('+')
        segments[col] = ' ' * len(segments[col])
        new_sep_line = '+'.join(segments)
        # replace ghost ``+``
        new_sep_line = re.sub('(^\+ )|( \+ )|( \+)$',
                              lambda m: m.group().replace('+', '|'),
                              new_sep_line)
        return new_sep_line

class MergeCellsUpCommand(MergeCellsDownCommand):
    offset = -1


class MergeCellsRightCommand(BaseMergeCellsCommand):
    offset = 0

    def run(self, edit):
        region, lines, indent= self.get_block_bounds()
        raw_table = self.view.substr(region).split('\n')
        begin = self.view.rowcol(region.begin())[0]
        # end = self.view.rowcol(region.end())[0]
        cursor = self.get_cursor_position()
        actual_line = raw_table[cursor[0] - begin]
        col = self.get_column_index(actual_line, cursor[1])
        separator_indexes = [match.start() for match in
                             re.finditer(re.escape('|'), actual_line)]
        actual_line = list(actual_line)
        actual_line[separator_indexes[col + self.offset]] = ' '
        actual_line = ''.join(actual_line)
        raw_table[cursor[0] - begin] = actual_line
        result = '\n'.join(raw_table)
        self.view.replace(edit, region, result)


class MergeCellsLeftCommand(MergeCellsRightCommand):
    offset = -1




def join_rows(rows, sep='\n'):
    """Given a list of rows (a list of lists) this function returns a
    flattened list where each the individual columns of all rows are joined
    together using the line separator.

    """
    output = []
    for row in rows:
        # grow output array, if necessary
        if len(output) <= len(row):
            for i in range(len(row) - len(output)):
                output.extend([[]])

        for i, field in enumerate(row):
            field_text = field.strip()
            if field_text:
                output[i].append(field_text)
    return [sep.join(lines) for lines in output]


def line_is_separator(line):
    return re.match('^[\t +=-]+$', line)


def has_line_seps(raw_lines):
    for line in raw_lines:
        if line_is_separator(line):
            return True
    return False


def partition_raw_lines(raw_lines):
    """Partitions a list of raw input lines so that between each partition, a
    table row separator can be placed.

    """
    if not has_line_seps(raw_lines):
        return [[x] for x in raw_lines]

    curr_part = []
    parts = [curr_part]
    for line in raw_lines:
        if line_is_separator(line):
            curr_part = []
            parts.append(curr_part)
        else:
            curr_part.append(line)

    # remove any empty partitions (typically the first and last ones)
    return [x for x in parts if x]


def unify_table(table):
    """Given a list of rows (i.e. a table), this function returns a new table
    in which all rows have an equal amount of columns.  If all full column is
    empty (i.e. all rows have that field empty), the column is removed.

    """
    max_fields = max([len(row) for row in table])
    empty_cols = [True] * max_fields
    output = []
    for row in table:
        curr_len = len(row)
        if curr_len < max_fields:
            row += [''] * (max_fields - curr_len)
        output.append(row)

        # register empty columns (to be removed at the end)
        for i in range(len(row)):
            if row[i].strip():
                empty_cols[i] = False

    # remove empty columns from all rows
    table = output
    output = []
    for row in table:
        cols = []
        for i in range(len(row)):
            should_remove = empty_cols[i]
            if not should_remove:
                cols.append(row[i])
        output.append(cols)

    return output


def split_table_row(row_string):
    if row_string.find("|") >= 0:
        # first, strip off the outer table drawings
        row_string = re.sub(r'^\s*\||\|\s*$', '', row_string)
        return re.split(r'\s*\|\s*', row_string.strip())
    return re.split(r'\s\s+', row_string.rstrip())


def parse_table(raw_lines):
    row_partition = partition_raw_lines(raw_lines)
    lines = []
    for row_string in row_partition:
        lines.append(join_rows([split_table_row(cell) for cell in row_string]))
    return unify_table(lines)


def table_line(widths, header=False):
    if header:
        linechar = '='
    else:
        linechar = '-'
    sep = '+'
    parts = []
    for width in widths:
        parts.append(linechar * width)
    if parts:
        parts = [''] + parts + ['']
    return sep.join(parts)


def get_field_width(field_text):
    return max([wcwidth.wcswidth(s) for s in field_text.split('\n')])


def split_row_into_lines(row):
    row = [field.split('\n') for field in row]
    height = max([len(field_lines) for field_lines in row])
    turn_table = []
    for i in range(height):
        fields = []
        for field_lines in row:
            if i < len(field_lines):
                fields.append(field_lines[i])
            else:
                fields.append('')
        turn_table.append(fields)
    return turn_table


def get_column_widths(table):
    widths = []
    for row in table:
        num_fields = len(row)
        # dynamically grow
        if num_fields >= len(widths):
            widths.extend([0] * (num_fields - len(widths)))
        for i in range(num_fields):
            field_text = row[i]
            field_width = get_field_width(field_text)
            widths[i] = max(widths[i], field_width)
    return widths


def get_column_widths_from_border_spec(slice):
    border = None
    for row in slice:
        if line_is_separator(row):
            border = row.strip()
            break

    if border is None:
        raise RuntimeError('Cannot reflow this table. Top table border not found.')

    left = right = None
    if border[0] == '+':
        left = 1
    if border[-1] == '+':
        right = -1
    return [max(0, len(drawing) - 2) for drawing in border[left:right].split('+')]


def pad_fields(row, widths):
    """Pads fields of the given row, so each field lines up nicely with the
    others.

    """
    wgaps = [wcwidth.wcswidth(c) - len(c) for c in row]
    widths = [w-wgaps[i] for i, w in enumerate(widths)]
    widths = [(' %-' + str(w) + 's ') for w in widths]

    # Pad all fields using the calculated widths
    new_row = []
    for i in range(len(row)):
        col = row[i]
        col = widths[i] % col.strip()
        new_row.append(col)
    return new_row


def reflow_row_contents(row, widths):
    new_row = []
    for i, field in enumerate(row):
        wrapped_lines = textwrap.wrap(field.replace('\n', ' '), widths[i])
        new_row.append("\n".join(wrapped_lines))
    return new_row


def draw_table(indent, table, manual_widths=None):
    if table == []:
        return []

    if manual_widths is None:
        col_widths = get_column_widths(table)
    else:
        col_widths = manual_widths

    # Reserve room for the spaces
    sep_col_widths = [(col + 2) for col in col_widths]
    header_line = table_line(sep_col_widths, header=True)
    normal_line = table_line(sep_col_widths, header=False)

    output = [indent + normal_line]
    first = True
    for row in table:

        if manual_widths:
            row = reflow_row_contents(row, manual_widths)

        row_lines = split_row_into_lines(row)

        # draw the lines (num_lines) for this row
        for row_line in row_lines:
            row_line = pad_fields(row_line, col_widths)
            output.append(indent + "|".join([''] + row_line + ['']))

        # then, draw the separator
        if first:
            output.append(indent + header_line)
            first = False
        else:
            output.append(indent + normal_line)

    return output
