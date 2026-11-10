# Performance

## Measure before claiming

"Too slow" or "too much memory" needs a number. Write a targeted experiment, memoized by its parameters
with the knobs as CLI flags, run it where the real work runs (e.g. a pod), and tune with it. Decide from
the measurement, then build. When the code under test changes, make sure old memoized results do not come
back.

## Size a worker pool from the runner, never from a magic number

Take the core count from what the runner guarantees (on k8s, the pod's CPU request), not a constant like
32. When workers use memory-heavy engines like DuckDB, give each worker its share of the cores and of the
memory budget. If memory use is a concern, run one process per task
(`ProcessPoolExecutor(n, max_tasks_per_child=1)`) so the memory of a task is given back when it ends.

Always bound the parallelism with an explicit executor. When order matters, key each task by its position
and restore the order after; completion order is not input order.

## For pyarrow and DuckDB, use one single-threaded process per core

One single-threaded process per core does better than threads: in each worker, set
`pa.set_cpu_count(threads_per_worker)` and use `use_threads=False` on parquet reads. Measured on a
62-core pod: 62 such processes averaged 47 cores, 62 threads averaged 27, and 31 two-threaded processes 32.

## Submit the biggest tasks first

Sort tasks by size, descending, so the tail of the pool is comprised of small tasks.
