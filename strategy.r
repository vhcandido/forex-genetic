#required libraries
library(zoo)
library(xts)
library(TTR)
library(chron)
library(quantmod)

source('SIT.r')

quotes <- new.env()

tickers<-c('GBPJPY')
file.path<- "/home/vhcandido/Downloads/historical_data/dukascopy/"

#parsing dates helper function
fun <- function(d) as.chron(strptime(d, "%d.%m.%Y %H:%M:%S"))#parsing dates helper function
for(n in tickers) { 
  quotes[[n]] =   as.xts(read.zoo(
    file=paste(file.path, n, '_Candlestick_1_h_BID_01.05.2008-31.10.2015.csv', sep=''),
    header=F, FUN=fun,sep=',',
    col.names=c("GMT time", "Open","High","Low","Close","Volume")))
  # fill missing values
  quotes[[n]] = na.locf(quotes[[n]], fromLast=TRUE) 
  quotes[[n]] <- quotes[[n]][quotes[[n]]$Volume != 0]
}

# remove missing values
bt.prep(quotes, align='remove.na')

while(TRUE) {
	con <- socketConnection(host="localhost", port = 6011, blocking=TRUE,
		    server=TRUE, open="r+")
	while(TRUE) {
		writeLines('Listening...')
		input <- readLines(con, 1)
		if(length(input) == 0) {
			writeLines('Waiting for the next generation')
			break
		}
		print(spl(input))

		params <- spl(input)
		buy <- params[1:9]
		sell <- params[10:18]

		prices <- quotes$prices
		models <- list()

		eval <- function(rule) {
			r1_str <- rule[c(1, 4)]
			r1_num <- as.numeric(rule[2:3])

			r2_str <- rule[c(5, 8)]
			r2_num <- as.numeric(rule[6:7])

			rop <- rule[9]

			ema1 <- EMA(prices, r1_num[1])
			ema2 <- EMA(prices, r1_num[2])

			if(r1_str[2] == '>') {
				rule1 <- iif(cross.up(ema1, ema2), 1, NA)
			}
			else {
				rule1 <- iif(cross.dn(ema1, ema2), 1, NA)
			}

			if(r2_str[1] == 'rsi') {
				tech = RSI(prices, n = r2_num[1])
				param <- r2_num[2]*100
			}
			else if(r2_str[1] == 'roc') {
				tech = ROC(prices, n = r2_num[1]-2)
				param <- r2_num[2]
			}
			else if(r2_str[1] == 'macd') {
				ma = MACD(prices, nSig = r2_num[1])
				tech <- ma$macd - ma$signal
				param <- r2_num[2]*10-5
			}

			if(r2_str[2] == '>') {
				rule2 <- iif(tech > param, 1, NA)
			}
			else if(r2_str[2] == '<') {
				rule2 <- iif(tech < param, 1, NA)
			}

			if(rop == 'and') {
				rule <- iif(rule1==1 & rule2==1, 1, NA)
			}
			else {
				rule <- iif(rule1==1 | rule2==1, 1, NA)
			}

			return(rule)
		}
		buy <- eval(buy)
		sell <- eval(sell)

		rule <- iif(buy==1 & sell==1, NA, iif(buy==1, 1, iif(sell==1, -1, NA)))
		if( all(is.na(rule)) ) {
			print('No trades')
			writeLines('0', con)
			next
		}

		#helper variable holding list of dates we will use later for plotting
		effective_dates = '2015-01-01::2015-09-30'

		#quotes$weight[] = NA
		#quotes$weight[] = rule
		#models$applied.rule = bt.run.share(quotes, clean.signal=T, trade.summary = TRUE)

		# TP and SL levels its R:R is 2:10!
		Takeprofit = 10/100
		Stoploss = 2/100

		stop.loss.take.profit <- function(weight, price, tstart, tend, pstop, pprofit) {
			index = tstart : tend
			if(weight > 0) {
			  temp = price[ index ] < (1 - pstop) * cummax(price[ index ])
			  temp = temp | price[ index ] > (1 + pprofit) * price[ tstart ]
			} else {
			  temp = price[ index ] > (1 + pstop) * cummin(price[ index ])
			  temp = temp | price[ index ] < (1 - pprofit) * price[ tstart ]       
			}
			return( temp )  
		}

		quotes$weight[] = NA
		quotes$weight[] = custom.stop.fn(coredata(rule), coredata(prices), stop.loss.take.profit, pstop = Stoploss, pprofit = Takeprofit)
		models$stopped.rule = bt.run.share(quotes, clean.signal=T, trade.summary = FALSE) 

		#bt.stop.strategy.plot(quotes, models$stop.loss.take.profit, dates = effective_dates, layout=F, main = 'Filtered', plotX = T)
		#strategy.performance.snapshoot(models, T) 

		#compute.sharpe(models$stop.loss.take.profit$equity)
		sharpe = compute.sharpe(models$stopped.rule$ret)
		print(sharpe)
		writeLines(toString(sharpe), con)
	}
	close(con)
}
