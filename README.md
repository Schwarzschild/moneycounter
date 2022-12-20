# Money Counter
Portfolio analytics utilities

This is the beginning of a work in progress.
I expect it will be in pretty good shape early in
2023 and then evolve from there.

This is a supporting package for a larger project I am working on and should be useful to others as is.


```shell
$ pip install moneycounter 
```

```python
from datetime import date
from moneycounter import fifo, realized_gains

# Given pandas df of trades calculate realized gains from sells after d
realized = fifo(df, d=date(2022, 1, 1))

# Given a pandas df of trades calculate realized gains.
realized = realized_gains(df)
```