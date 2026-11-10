# pyarrow and parquet

## Read one parquet file with `ParquetFile`, not `read_table`

Read one file with `pq.ParquetFile(path).read()` or `.read_row_group(i)`, not `pq.read_table(path)`.
`read_table` infers hive partition columns from `key=value` segments of the path and adds them as
dictionary columns, so a file under `region=south/batch=000/` comes back with two columns it does not
hold. `partitioning=None` is the equivalent on `read_table`.

## Choose input and output row group sizes separately

Plan on small input row groups (the unit of chunking) and write the output through
`ParquetWriter.write_table(table, row_group_size=N)`, which re-chunks whatever it is handed, so the output
carries only its own metadata. For a wide nested schema the metadata is most of a small file: 133 shards
of one partition were 80 MiB, their data 0.8 MiB.
