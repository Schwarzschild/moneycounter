# Money Counter
*Portfolio analytics utilities*



This is the beginning of a work in progress.
I expect it will be in pretty good shape early in
2023 and then evolve from there.

This is a supporting package for a larger project I am working on and should be useful to others as is.

### Installation

[PyPI Page](https://pypi.org/search/?q=moneycounter)

```shell
$ pip install moneycounter 
```

### Prerequisite Trades Data Frame

A trades dataframe has these columns:

`columns = Index(['dt', 'q', 'p', 'cs', 't', 'a'], dtype='object')`

It must be ordered by dt.

Where:

| Column |                   Description                   |
|:------:|:-----------------------------------------------:|
|  `dt`  |       execution time as datetime.datetime       |
|  `q`   | quantity traded, signed with negative as a sale |
| `p`    |                 execution price                 |
|  `cs`  |          contract size, typically 1.0           |
|  `t`   |                     ticker                      |
|  `a`   |                     account                     |


### Example Calculations

```python
from datetime import date
from moneycounter import pnl, realized_gains, wap_calc

# Calculate realized, unrealized and total pnl from trades dataframe.
realized, unrealized, total = pnl(df, price=price)

# Calculate weighted average price of open positions from trades data frame.
wap = wap_calc(df)

# Calculate realized gains from trades data frame.
realized = realized_gains(df)

$` \phi = c * Q * (p - p_wap) `$
