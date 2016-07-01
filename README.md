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


First, run the R server:
> Rscript strategy.r

Then, the Python GA:
> python main.py

There will be an image with the evolution of the fitness function (Sharpe ratio, currently).
