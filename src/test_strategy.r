source('strategy.r')

# Read rule parameters from stdin
args <- commandArgs(trailingOnly = TRUE)

# Separate rule parameters into different rules (buy/sell)
input <- args[1]
params <- spl(input)
buy <- params[1:9]
sell <- params[10:18]

# Load financial data
tickers <- c('GBPUSD')
file.path<- '../data/'
quotes <- read_data(tickers, file.path)
prices <- quotes$prices

# Evaluate the output of the rules
rule <- join_rules(prices, buy, sell)

# Run strategy and get its results
models <- run_strategy(quotes, rule)

# Simple output - may be removed later
sharpe <- compute.sharpe(models$stopped.rule$ret)
print(sharpe)

effective_dates = '2015-01-01::2015-09-30'
# Get graphic information of the strategy
bt.stop.strategy.plot(quotes, models$stop.loss.take.profit, dates = effective_dates, layout=F, main = 'Strategy', plotX = T)
strategy.performance.snapshoot(models, T) 
