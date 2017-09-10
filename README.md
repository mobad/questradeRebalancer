# questradeRebalancer
Script to buy ETFs using available cash and rebalance according to configured ratios.

This is a WIP, use at your own risk!

This will use all your money in that account to buy ETFs!!!

This uses my fork of QuestradeAPI_PythonWrapper.

To configure which ETFs and the ratios then modify getSymbolTargetRatiosForAccount and make sure they add to 100.

Usage:

questradeRebalancer.py listAccounts to list accounts

Then, to list what it would buy:

questradeRebalancer.py showOrders accountType accountNumber

eg. questradeRebalancer.py showOrders Margin 12345678

And to actually buy:

questradeRebalancer.py spendAllMyMoney accountType accountNumber

There is some error handling but not much:
- If it can't get a quote of an ETF, it'll stop. (Likely exchange is just closed.)
- If it detects an open order for any ETF it's configured to buy, it'll stop.
- If it any orders fail, it'll stop.

It has a pretty simple algorithm for rebalancing:
- Go though each of the ETFs it's been configured to buy and calculate the sum of the differences of target ratio to the ratio if that ETF was bought.
- Choose the ETF with the lowest sum of differences.
- If you can't afford to buy that ETF then stop, else repeat.
- Buy all ETFs that have been chosen.

It's not efficient but it handles many edge cases nicely and is pretty simple.

It will place a Day Limit order for the current ask price.

It can also kind of do dollar cost averaging by modifying DOLLAR_COST_AVERAGE.

It will just use currentCash / DOLLAR_COST_AVERAGE every time you run the script.
