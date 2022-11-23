import json
from enum import Enum
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass


class CompOp(Enum):
    EQ = "="
    NE = "!="
    GTE = ">="
    LTE = "<="
    GT = ">"
    LT = "<"
    IN = "IN"
    NIN = "NOT IN"
    LIKE = "LIKE"
    NLIKE = "NOT LIKE"
    IS = "IS"
    NIS = "IS NOT"


def _split_op(key: str) -> Tuple[str, CompOp]:
    *column_names, op = key.split("__")
    if not column_names:
        # like foo="bar", assume EQ
        return [op], CompOp.EQ
    try:
        op = CompOp[op.upper()]
    except KeyError:
        raise ValueError(f"{op} does not appear to be a valid comparison operator")
    return column_names, op


class _Value:
    def __init__(self, value: Any):
        self.value = value

    def sql(self):
        if isinstance(self.value, (int, float)):
            return str(self.value)
        elif isinstance(self.value, str):
            return json.dumps(self.value)
        elif self.value is None:
            return "NULL"
        elif isinstance(self.value, Enum):
            return json.dumps(self.value.value)
        elif isinstance(self.value, (tuple, list, set)):
            json_dump = json.dumps(self.value)[1, -1]
            return f"({json_dump})"
        else:
            return json.dumps(self.value)


class _Comparison:
    def __init__(self, lhs: str, op: CompOp, rhs: Any):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    @classmethod
    def _parse(cls, key: str, val: Any):
        column_names, op = _split_op(key)
        return cls(column_names, op, _Value(val))

    def sql(self) -> str:
        col_names = ".".join(self.lhs)
        rhs = self.rhs.sql()
        return f"({col_names} {self.op.value} {rhs})"


class Count:
    def __init__(self, selected, *, name):
        self.selected = selected
        self.name = name

    def sql(self):
        return f"COUNT({self.selected}) AS {self.name}"


class _Selection:
    def __init__(self, selection: List[str]):
        self.selection = selection

    def sql(self):
        query = ""
        for sel in self.selection:
            if isinstance(sel, str):
                query = f"{query}{sel}"
            else:
                query = f"{query}{sel.sql()}"
            if sel is not self.selection[-1]:
                query = f"{query}, "
        return query


class _Query:
    def __init__(
        self,
        limit_=None,
        *,
        table,
        selection,
        grouping,
        filters: List[List[_Comparison]],
    ):
        self.table = table
        self.selection = selection
        self.filters = filters
        self.grouping = grouping
        self.limit_ = limit_

    def copy(self):
        return {
            "table": self.table,
            "selection": self.selection,
            "grouping": self.grouping,
            "filters": self.filters,
            "limit_": self.limit_,
        }

    def filter(self, **kwargs):
        comparisons = [_Comparison._parse(key, val) for key, val in kwargs.items()]
        copy = self.copy()
        copy["filters"] = self.filters + [comparisons]
        return _Query(**copy)

    def group_by(self, *args):
        copy = self.copy()
        copy["grouping"] = _Selection(args)
        return _Query(**copy)

    def limit(self, value: int):
        if value < 0:
            raise ValueError(f"limit cannot be negative: {value!r}")
        self.limit_ = value
        return self

    def sql(self):
        query = f"SELECT {self.selection.sql()}\n"
        query = f"{query}FROM {self.table.name}\n"
        if self.filters:
            query = f"{query}WHERE ("
        for filter_set in self.filters:
            query = f"{query}("
            for comp in filter_set:
                query = f"{query}{comp.sql()}"
                if comp is not filter_set[-1]:
                    query = f"{query} AND "
            query = f"{query})"
            if filter_set is not self.filters[-1]:
                query = f"{query} AND "
        if self.filters:
            query = f"{query})\n"
        if self.grouping:
            query = f"{query}GROUP BY {self.grouping.sql()}\n"
        if self.limit:
            query = f"{query}LIMIT {self.limit_}"
        return query


class _Table:
    def __init__(self, name: str, *, row_cls):
        split = name.split(".")
        if len(split) == 2:
            self.project, self.dataset, self.table = None, *split
        elif len(split) == 3:
            self.project, self.dataset, self.table = split
        else:
            raise ValueError(f"name {name!r} did not describe project.dataset.table")

    def filter(self, **kwargs):
        comparisons = [_Comparison._parse(key, val) for key, val in kwargs.items()]
        return _Query(
            table=self,
            selection=_Selection(["*"]),
            filters=[comparisons],
            grouping=None,
        )

    def values(self, *args):
        return _Query(
            table=self,
            selection=_Selection(args),
            filters=[],
            grouping=None,
        )

    @property
    def name(self):
        return f"{self.project}.{self.dataset}.{self.table}"


class Client:
    def __init__(self, bq_client: Any):
        self._client = bq_client

    def query(self, result_class: type, query: _Query) -> Any:
        sql = query.sql()
        for row in self._client.query(sql):
            yield result_class.parse(row)


def declare_row(klass) -> type:
    @classmethod
    def _columns(cls) -> Dict[str, Any]:
        return cls.__annotations__

    @classmethod
    def table(cls, name: str) -> _Table:
        return _Table(name, row_cls=cls)

    @classmethod
    def parse(cls, row: Any) -> Any:
        kwargs = {}
        for column, type_ in cls._columns().items():
            if type_ is Dict:
                kwargs[column] = json.loads(getattr(row, column))
            else:
                kwargs[column] = getattr(row, column)
        return cls(**kwargs)

    klass._columns = _columns
    klass.table = table
    klass.parse = parse

    klass = dataclass(klass)

    # To reference columns like ExampleRow.test
    for column in klass._columns():
        setattr(klass, column, column)

    return klass
