This is a simple Genetic Algorithm developed to optimize parameters of
trading rules based on Technical Analysis.


To run this program you should have some R packages installed:
* quantmod
* TTR
* zoo
* xts

Also some Python 2.7 libraries
* pandas
* matplotlib

And the name of the file holding the financial data must be put in the strategy.r file.


First, run the R server passing the currency pairs as parameters (the associated data file must be located in the data directory, see more details in strategy.r:read_data):
> Rscript server.r 'GBPUSD'

Then, run the Python GA client:
> python client.py

There will be an image with the evolution of the fitness function (Sharpe ratio, currently).

Using the generated rule string (separated by commas) run the strategy test to see the metrics computed over it.
> Rscript test_strategy '<strategy_string>'


#################################################
The tookit used for running strategies can be found here:
https://github.com/systematicinvestor/SIT
Many thanks to Michael Kapler.
