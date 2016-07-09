#required libraries
library(zoo)
library(xts)
library(TTR)
library(chron)
library(quantmod)

source('SIT.r')

#parsing dates helper function
fun <- function(d) as.chron(strptime(d, "%d.%m.%Y %H:%M:%S"))#parsing dates helper function

read_data <- function(file.path, dates='') {
	quotes <- new.env()
	for(file in file.path) { 
		n <- pair_name_from_path(file)
		quotes[[n]] =   as.xts(read.zoo(
			#file=paste(file.path, n, '.csv', sep=''),
			file=file,
			header=F, FUN=fun,sep=',',
			col.names=c("GMT time", "Open","High","Low","Close","Volume")))
		if(dates != '') {
			quotes[[n]] = quotes[[n]][dates]
		}
		# fill missing values
		quotes[[n]] = na.locf(quotes[[n]], fromLast=TRUE) 
		quotes[[n]] <- quotes[[n]][quotes[[n]]$Volume != 0]
	}
	# remove missing values
	bt.prep(quotes, align='remove.na')

	return(quotes)
}

pair_name_from_path <- function(filepath) {
	fp <- strsplit(filepath, '/')[[1]]
	return(strsplit(tail(fp,1), '.csv')[[1]])
}

evaluate_rule <- function(prices, rule) {
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

join_rules <- function(prices, buy, sell) {
	buy <- evaluate_rule(prices, buy)
	sell <- evaluate_rule(prices, sell)
	rule <- iif(buy==1 & sell==1, NA, iif(buy==1, 1, iif(sell==1, -1, NA)))
	return(rule)
}

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

run_strategy <- function(quotes, rule) {
	# TP and SL levels its R:R is 2:10!
	Takeprofit = 3/100
	Stoploss = 1/100

	models <- list()

	quotes$weight[] = NA
	quotes$weight[] = custom.stop.fn(coredata(rule), coredata(prices), stop.loss.take.profit, pstop = Stoploss, pprofit = Takeprofit)
	models$stopped.rule = bt.run.share(quotes, clean.signal=T, trade.summary = FALSE) 

	return(models)
}

