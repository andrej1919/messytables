from collections import defaultdict

import six

from messytables.core import Cell


def column_count_modal(rows):
    """ Return the modal value of columns in the row_set's
    sample. This can be assumed to be the number of columns
    of the table. """
    counts = defaultdict(int)
    for row in rows:
        length = len([c for c in row if not c.empty])
        if length > 1:
            counts[length] += 1
    if not len(counts):
        return 0
    return max(list(counts.items()), key=lambda k_v: k_v[1])[0]


def headers_guess(rows, tolerance=1):
    """ Guess the offset and names of the headers of the row set.
    This will attempt to locate the first row within ``tolerance``
    of the mode of the number of rows in the row set sample.

    The return value is a tuple of the offset of the header row
    and the names of the columns.
    """
    rows = list(rows)
    modal = column_count_modal(rows)
    for i, row in enumerate(rows):
        length = len([c for c in row if not c.empty])
        if length >= modal - tolerance:
            # TODO: use type guessing to check that this row has
            # strings and does not conform to the type schema of
            # the table.
            return i, [c.value for c in row]
    return 0, []


def headers_processor(headers):
    """ Add column names to the cells in a row_set. If no header is
    defined, use an autogenerated name. """

    def apply_headers(row_set, row):
        _row = []
        pairs = six.itertools.izip_longest(row, headers)
        for i, (cell, header) in enumerate(pairs):
            if cell is None:
                cell = Cell(None)
            cell.column = header
            if not cell.column:
                cell.column = "column_%d" % i
                cell.column_autogenerated = True
            _row.append(cell)
        return _row
    return apply_headers


def headers_make_unique(headers, max_length=None):
    """Make sure the header names are unique. For non-unique
    columns, append 1, 2, 3, ... after the name. If max_length
    is set, truncate the original string so that the headers are
    unique up to that length."""

    headers = [h.strip() for h in headers]

    new_digits_length = 0
    while not max_length or new_digits_length <= max_length:
        # If maxlength is 63 and we expect 1 digit for appending
        # numerals to make the headers unique, then truncate the
        # column names to 62 characters.
        _headers = headers
        if max_length:
            _headers = [h[0:max_length - new_digits_length].strip()
                        for h in headers]

        # For headers that are not unique, add a number to the end.
        header_counter = {}
        new_headers = list(_headers)  # clone before using
        for i, h in enumerate(new_headers):
            if _headers.count(h) > 1:
                header_counter[h] = header_counter.get(h, 0) + 1
                new_headers[i] += "_%d" % header_counter[h]

        # If there is a max_length but adding a counter made a header longer
        # than max_length, we have to truncate more up front (which may
        # change which headers are nonunique) and try again.
        if max_length and (True in [len(h) > max_length for h in new_headers]):
            # Adding this counter made the new header longer than max_length.
            # We have to truncate the original headers more.
            new_digits_length += 1
            continue

        # Otherwise, the new headers are unique.
        return new_headers

    raise ValueError('''max_length is so small that the column names cannot
        be made unique.''')
