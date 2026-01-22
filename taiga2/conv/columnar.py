import struct
import zlib
import array
from taiga2.conv import sniff
import csv
from collections import namedtuple
from io import StringIO
from io import BytesIO
import logging
import subprocess
import sys
from taiga2.conv.util import r_escape_str, shortened_list, ImportResult, get_file_hashes
from taiga2.conv import BYTES_PER_STR_OBJECT, MAX_MB_PER_CHUNK

log = logging.getLogger(__name__)

ColumnDef = namedtuple("ColumnDef", ["name", "index", "persister"])


class Predicate(object):
    def create_evaluator(self, cursorMap):
        raise Exception("unimp")

    def get_columns(self):
        raise Exception("unimp")


class ComparisonPred(object):
    def __init__(self, name, value, fn, value_is_set=False):
        self.value = value
        self.name = name
        self.comparison_fn = fn
        self.value_is_set = value_is_set

    def create_evaluator(self, cursorMap):
        cursor = cursorMap[self.name]
        assert cursor != None, "No cursor for %s in %s" % (
            repr(self.name),
            repr(cursorMap),
        )
        value = self.value
        if self.value_is_set:
            value = set([cursor.col_type(v) for v in value])
        else:
            value = cursor.col_type(value)
        fn = self.comparison_fn

        def is_satified():
            return fn(cursor.get_value(), value)

        return is_satified

    def get_columns(self):
        return [self.name]


InPred = lambda name, value: ComparisonPred(
    name, value, lambda value, ref: value in ref, True
)
NinPred = lambda name, value: ComparisonPred(
    name, value, lambda value, ref: not (value in ref), True
)

GtePred = lambda name, value: ComparisonPred(
    name, value, lambda value, ref: value >= ref
)
GtPred = lambda name, value: ComparisonPred(name, value, lambda value, ref: value > ref)
LtPred = lambda name, value: ComparisonPred(name, value, lambda value, ref: value < ref)
LtePred = lambda name, value: ComparisonPred(
    name, value, lambda value, ref: value <= ref
)
NePred = lambda name, value: ComparisonPred(
    name, value, lambda value, ref: value != ref
)
EqPred = lambda name, value: ComparisonPred(
    name, value, lambda value, ref: value == ref
)


class AndPred(object):
    def __init__(self, preds):
        self.preds = preds

    def create_evaluator(self, cursorMap):
        and_list = [p.create_evaluator(cursorMap) for p in self.preds]

        def all_true():
            for p in and_list:
                if not p():
                    return False
            return True

        return all_true

    def get_columns(self):
        all = [p.get_columns() for p in self.preds]
        return set().union(*all)


class AlwaysSatisfied(object):
    def create_evaluator(self, cursorMap):
        return lambda: True

    def get_columns(self):
        return []


class ColumnCursor(object):
    def __init__(self, values, col_type):
        self.index = 0
        self.col_type = col_type
        self.values = values

    def next(self):
        self.index += 1

    def get_value(self):
        return self.values[self.index]


def write_int(output, n):
    output.write(struct.pack("I", n))


def read_int(fd):
    buffer = fd.read(4)
    if len(buffer) == 0:
        return None
    return struct.unpack("I", buffer)[0]


def write_str(output, s):
    bytes = s.encode("utf8")
    write_int(output, len(bytes))
    output.write(bytes)


def read_str(fd, max_len=None):
    length = read_int(fd)
    if length == None:
        return None

    if max_len is not None and length > max_len:
        raise Exception(
            "In columnar read_str, attempted to read string with max length {}, but read a length of {}".format(
                max_len, length
            )
        )

    # HACK: The version of boto3 we use has a bug where reading 0 bytes from a
    # StreamingBody raises IncompleteReadError
    # See https://github.com/boto/botocore/issues/1309
    if length == 0:
        return ""

    bytes = fd.read(length)
    try:
        s = str(bytes, "utf8")
    except UnicodeDecodeError:
        s = str(bytes, "iso-8859-1")
    return s


class StringSerializer(object):
    type_name = "str"

    def to_buffer(self, values):
        output = BytesIO()
        for s in values:
            write_str(output, s)
        return output.getvalue()

    def from_buffer(self, array):
        fd = BytesIO(array)
        values = []
        while True:
            v = read_str(fd)
            if v == None:
                break
            values.append(v)
        return ColumnCursor(values, str)


class DoubleSerializer(object):
    type_name = "float"

    def to_buffer(self, values):
        v_array = array.array("d", [float(v) for v in values])
        return v_array.tobytes()

    def from_buffer(self, buffer):
        values = array.array("d")
        values.frombytes(buffer)
        return ColumnCursor(values, float)


class IntSerializer(object):
    type_name = "int"

    def to_buffer(self, values):
        v_array = array.array("i", [int(v) for v in values])
        return v_array.tobytes()

    def from_buffer(self, buffer):
        values = array.array("i")
        values.frombytes(buffer)
        return ColumnCursor(values, int)


# Block length (4b)
# Column lengths (4b * column_count)
# Column 1...
# Column 2...
# Column 3...


def write_block_header(fd, row_count, column_lengths):
    write_int(fd, row_count)
    write_int(fd, len(column_lengths))
    for length in column_lengths:
        write_int(fd, length)
        # print "column_lengths %s" % repr(column_lengths)
        # print "after write header", fd.tell()


def read_block_header(fd):
    row_count = read_int(fd)
    if row_count == None:
        return None
    # print "row count %d" % row_count
    column_count = read_int(fd)
    # if we have more than 100k columns, something isn't right.  The file is most likely corrupt or we have a bug in parsing.
    # Or we should re-think storing this in a column store...
    assert column_count < 100000
    # print "reading %d columns" % column_count
    column_lengths = []
    for i in range(column_count):
        column_lengths.append(read_int(fd))
    # print "after read header", fd.tell()
    return row_count, column_lengths


def persist_block(fd, column_persisters, values):
    column_lengths = []
    length_table_offset = fd.tell()
    write_block_header(fd, len(values), [0] * len(column_persisters))

    column_offsets = []
    #  print "persisting row: %s, %s" % (repr(values), column_persisters)
    for i, cp in enumerate(column_persisters):
        column_offsets.append(fd.tell())
        column_values = [row[i] for row in values]
        column_buffer = cp.to_buffer(column_values)
        column_compressed = zlib.compress(column_buffer)
        column_lengths.append(len(column_compressed))
        fd.write(column_compressed)
    # print "wrote col offsets", column_offsets

    next_block = fd.tell()
    fd.seek(length_table_offset)
    write_block_header(fd, len(values), column_lengths)
    fd.seek(next_block)
    # print "persist_block size = %s" % (next_block - length_table_offset)


def compute_column_offsets(base_offset, column_lengths):
    column_offsets = []
    cur_offset = base_offset
    for i, length in enumerate(column_lengths):
        column_offsets.append(cur_offset)
        cur_offset += length
    return column_offsets


def read_block(fd, column_count, columns):
    "columns: list of (column_index, persister) tuples"
    cursors = []
    pair = read_block_header(fd)
    if pair == None:
        return None
    row_count, column_lengths = pair
    base_offset = fd.tell()

    column_offsets = compute_column_offsets(base_offset, column_lengths)

    # print "column_lengths", column_lengths
    # print "column_offsets", column_offsets

    for column_index, column_persister in columns:
        fd.seek(column_offsets[column_index])
        column_compressed = fd.read(column_lengths[column_index])
        column_buffer = zlib.decompress(column_compressed)
        column_cursor = column_persister.from_buffer(column_buffer)
        cursors.append(column_cursor)

    # seek past the end of all data
    fd.seek(column_offsets[-1] + column_lengths[-1])

    return row_count, cursors


def select_from_cursors(all_columns, projection, predicate, row_count):
    for i in range(row_count):
        # print "evaluating for row %d, %s" % (i, [c.get_value() for c in projection])
        if predicate():
            yield [c.get_value() for c in projection]

        for c in all_columns:
            c.next()


def select(fd, column_count, columns, projection_indices, bind_predicate):
    "columns is list of (index, persister)"
    while True:
        next_block = read_block(fd, column_count, columns)
        if next_block == None:
            break

        row_count, cursors = next_block
        predicate = bind_predicate(cursors)
        projection = [cursors[index] for index in projection_indices]
        for row in select_from_cursors(cursors, projection, predicate, row_count):
            yield row


def execute_query(fd, select_names, predicate):
    column_definitions = read_column_definitions(fd)
    columns_to_extract = []

    needed_columns = list(set(predicate.get_columns()).union(select_names))
    name_to_index = dict([(name, i) for i, name in enumerate(needed_columns)])
    columns_to_extract = []
    for name in needed_columns:
        definition = column_definitions[name]
        columns_to_extract.append((definition.index, definition.persister))

    def bind_predicate(cursors):
        # go from indexed list of cursors to named map of cursors to perform binding
        cursor_map = {}
        # print "name to index", name_to_index
        # print "cursors", cursors
        for name in needed_columns:
            # print "name=%s" % name
            cursor_map[name] = cursors[name_to_index[name]]
        return predicate.create_evaluator(cursor_map)

    projection_indices = [name_to_index[name] for name in select_names]
    for row in select(
        fd,
        len(column_definitions),
        columns_to_extract,
        projection_indices,
        bind_predicate,
    ):
        yield row


def write_column_definitions(fd, name_type_pairs):
    fd.write(struct.pack("I", len(name_type_pairs)))
    for name, col_type in name_type_pairs:
        write_str(fd, name)
        write_str(fd, col_type.type_name)


class TableInfo:
    def __init__(self, columns):
        self.columns = columns
        self.by_name = dict([(c.name, c) for c in columns])

    def __iter__(self):
        return iter(self.columns)

    def __getitem__(self, key):
        if not (key in self.by_name):
            raise Exception(
                "No column named %s (columns: %s)" % (repr(key), self.by_name.keys())
            )
        return self.by_name[key]

    def __len__(self):
        return len(self.columns)


def read_column_definitions(fd):
    col_count_buffer = fd.read(4)  # type: bytes
    col_count = struct.unpack("I", col_count_buffer)[0]
    columns = []
    for i in range(col_count):
        name = read_str(fd)
        type_name = read_str(fd, max_len=10)
        if type_name == "str":
            columns.append(ColumnDef(name, i, StringSerializer()))
        elif type_name == "float":
            columns.append(ColumnDef(name, i, DoubleSerializer()))
        elif type_name == "int":
            columns.append(ColumnDef(name, i, IntSerializer()))
        else:
            raise Exception("unknown type: %s" % repr(type_name))
    return TableInfo(columns)


class DatasetWriter(object):
    def __init__(self, filename, columns, rows_per_block=100000):
        self.filename = filename
        self.output = open(filename, "wb")
        self.columns = columns

        persisters = []
        for c in columns:
            if c.type == str:
                persisters.append(StringSerializer())
            elif c.type == float:
                persisters.append(DoubleSerializer())
            elif c.type == int:
                persisters.append(IntSerializer())
            else:
                raise Exception("unknown type: %s" % repr(c))

        self.persisters = persisters
        #    print "a.persist:", self.persisters, columns
        self.row_block = []
        self.rows_per_block = rows_per_block

        write_column_definitions(
            self.output, [(columns[i].name, persisters[i]) for i in range(len(columns))]
        )

    def append(self, row):
        self.row_block.append(row)
        if len(self.row_block) >= self.rows_per_block:
            self.flush_block()

    def flush_block(self):
        #    print "persist:", self.persisters
        persist_block(self.output, self.persisters, self.row_block)
        self.row_block = []

    def close(self):
        self.flush_block()
        self.output.close()


def get_short_summary(input_file):
    with open(input_file) as fd:
        predicate = AlwaysSatisfied()

        column_definitions = read_column_definitions(fd)
        column_names = [x.name for x in column_definitions.columns]
        fd.seek(0)

        row_count = 0
        for row in execute_query(fd, [], predicate):
            row_count += 1

        return "Table with {} rows, {} columns".format(len(column_names), row_count)


def get_long_summary(input_file):
    with open(input_file) as fd:
        predicate = AlwaysSatisfied()

        column_definitions = read_column_definitions(fd)
        column_names = [x.name for x in column_definitions.columns]
        fd.seek(0)

        row_count = 0
        for row in execute_query(fd, [], predicate):
            row_count += 1

        b = StringIO()
        b.write("Table with {} rows, {} columns\n".format(len(column_names), row_count))
        b.write("Column names:\n")
        for c in column_definitions:
            b.write('\t"{}" {}\n'.format(c.name, c.persister.type_name))
        return b.getvalue()


def convert_csv_to_tabular(
    input_file, output_file, delimiter, encoding, rows_per_block=None
):
    sha256, md5 = get_file_hashes(input_file)
    hasRowNames, datafile_columns = sniff.sniff(
        input_file, encoding, delimiter=delimiter
    )

    if not rows_per_block:
        rows_per_block = MAX_MB_PER_CHUNK / (
            (BYTES_PER_STR_OBJECT * len(datafile_columns)) / 1024**2
        )

    # print("Before conversion")
    # tr.print_diff()
    with open(input_file, "r", encoding=encoding) as fd:
        reader = csv.reader(fd, delimiter=delimiter)

        w = DatasetWriter(output_file, datafile_columns, rows_per_block=rows_per_block)

        # throw out the header row
        next(reader)
        line_number = 1

        for row in reader:
            line_number += 1

            if len(datafile_columns) != len(row):
                raise Exception(
                    "line %d column count mismatches: cols (%r) mismatches (%r)"
                    % (line_number, datafile_columns, row)
                )
            w.append(row)

        w.close()

    long_summary = "Column names: {}\n".format(
        shortened_list([c.name for c in datafile_columns])
    )

    return ImportResult(
        sha256=sha256,
        md5=md5,
        short_summary="{} rows, {} columns".format(line_number, len(datafile_columns)),
        long_summary=long_summary,
    )


def convert_tabular_to_csv(
    input_file, output_file, delimiter, encoding, select_names=None, predicate=None
):
    log.info("convert_tabular_to_csv %s -> %s", input_file, output_file)
    _convert_tabular_to_csv(
        input_file,
        lambda: output_file,
        lambda row_count, file_len: False,
        delimiter,
        encoding,
        select_names,
        predicate,
    )


def convert_tabular_to_multiple_csvs(
    input_file,
    temp_file_generator,
    delimiter,
    encoding,
    select_names=None,
    predicate=None,
    max_bytes=None,
    max_rows=None,
):
    filenames = []

    def output_file_callback():
        filename = temp_file_generator()
        filenames.append(filename)
        return filename

    def flush_callback(row_count, length):
        if max_rows is not None and row_count >= max_rows:
            return True
        if max_bytes is not None and length >= max_bytes:
            return True
        return False

    _convert_tabular_to_csv(
        input_file,
        output_file_callback,
        flush_callback,
        delimiter,
        encoding,
        select_names,
        predicate,
    )
    return filenames


def _convert_tabular_to_csv(
    input_file,
    output_file_callback,
    flush_callback,
    delimiter,
    encoding,
    select_names=None,
    predicate=None,
):
    assert isinstance(input_file, str)
    assert callable(output_file_callback)
    assert callable(flush_callback)
    assert isinstance(delimiter, str)

    with open(input_file, "rb") as fd:

        if predicate == None:
            predicate = AlwaysSatisfied()

        if select_names == None:
            column_definitions = read_column_definitions(fd)
            select_names = [x.name for x in column_definitions.columns]
            fd.seek(0)

        row_generator = execute_query(fd, select_names, predicate)

        output_file = None

        for row in row_generator:
            if output_file is None:
                output_file = output_file_callback()
                output = open(output_file, "wt", encoding=encoding)
                w = csv.writer(output, delimiter=delimiter)
                w.writerow(select_names)
                row_count = 0
            w.writerow(row)
            row_count += 1

            # check if we need to move onto the next output file
            if flush_callback(row_count, output.tell()):
                output.close()
                output_file = None

        if output_file is not None:
            output.close()
