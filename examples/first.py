from typing import Dict

from bigqueryorm import declare_row, Count, Client
from google.cloud import bigquery

client = Client(bigquery.Client())
table_name: str = "..."


@declare_row
class ExampleRow:
    name: str
    age: int
    some_float: float
    meta: Dict
    test: bool


query = ExampleRow.table(table_name).filter(
    age__gte=26,
    name="john",
).filter(
    some_float=3.33
).limit(10)

print("with two filters and limit(10):")
print(query.sql())

for result in client.query(ExampleRow, query):
    print(result)


@declare_row
class AggResult:
    test: bool
    ct: int


query = AggResult.table(table_name).values(
    AggResult.test,
    Count("*", name="ct"),
).group_by(AggResult.test).limit(100)

print("count(*) group by test column:")
print(query.sql())

for result in client.query(AggResult, query):
    print(result)
