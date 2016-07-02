# Genetic Algorithm for optimization of trading rules
----------
This is a simple Genetic Algorithm developed to optimize parameters of trading rules based on Technical Analysis.

It's built using the R package Systematic Investor Tookit available here: [SIT][1]. Many thanks to Michael Kapler.

**Dependencies**

To run this program you should have some R packages installed:
* zoo
* xts
* TTR
* quantmod

Also some Python 2.7 libraries
* pandas
* matplotlib

**Running**

First, run the R server passing the currency pairs as parameters (the associated data file must be located in the data directory, see more details in `strategy.r:read_data`):
* `Rscript server.r 'GBPUSD'`

Then, run the Python GA client:
* `python client.py`

There will be an image with the evolution of the fitness function (Sharpe ratio, currently).

Using the generated rule string (separated by commas) run the strategy test to see the metrics computed over it.
* `Rscript test_strategy '<strategy_string>'`


----------

**Note to myself**: I need to learn how to use markdown tags.

[1]: https://github.com/systematicinvestor/SIT
