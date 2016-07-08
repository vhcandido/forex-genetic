source('strategy.r')

# Read currency pairs from stdin
param <- commandArgs(trailingOnly = TRUE)
# Get all elements but the last
file.path <- head(param, -1)
# Last element
dates <- tail(param, 1)

#Load financial data
quotes <- read_data(file.path, dates)
prices <- quotes$prices

while(TRUE) {
	# Open socket connection
	con <- socketConnection(host="localhost", port = 6011, blocking=TRUE,
		    server=TRUE, open="r+")
	while(TRUE) {
		# Wait to receive the next rule
		print("\nListening...")
		input <- readLines(con, 1)
		if(length(input) == 0) {
			writeLines('Waiting for the next generation')
			break
		}

		# Separate rule parameters into different rules (buy/sell)
		params <- spl(input)
		buy <- params[1:9]
		sell <- params[10:18]
		print(params) # simple output to check in stdout

		# Evaluate the output of the rules
		rule <- join_rules(prices, buy, sell)
		if( all(is.na(rule)) ) {
			print('No trades')
			writeLines('0', con)
			next
		}

		# Run strategy and get its results
		models <- run_strategy(quotes, rule)

		# Compute Sharpe ratio and send the result back to the client
		sharpe <- compute.sharpe(models$stopped.rule$ret)
		print(sharpe)
		writeLines(toString(sharpe), con)
	}
	# Close current connection
	close(con)
}
