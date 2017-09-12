# questradeRebalancer
Script to buy ETFs using available cash and rebalance according to configured ratios.

# This is a WIP, use at your own risk!
# This will spend all the money in an account to buy ETFs!!!

This uses my fork of QuestradeAPI_PythonWrapper https://github.com/mobad/QuestradeAPI_PythonWrapper

## Configuration:
You need to create a Personal Api key on Questrade and make sure to enable all three permissions if you want it to make trades.

If you never want the script to place any orders then I recommened not enabling the trading permission.

Put this api key in a file called ~/.questrade_token.json in the format of:

>{"access_token":"","api_server":"https:\\/\\/api01.iq.questrade.com\\/","expires_in":1800,"refresh_token":"YOUR_TOKEN_HERE","token_type":"Bearer"}

To configure which ETFs and the ratios then modify getSymbolTargetRatiosForAccount and make sure they add to 100.

## Usage:

> questradeRebalancer.py listAccounts to list accounts

Then, to list what it would buy:

> questradeRebalancer.py showOrders accountType accountNumber

> eg. questradeRebalancer.py showOrders Margin 12345678

And to actually buy:

> questradeRebalancer.py placeOrders accountType accountNumber

Then type CONFIRM at the prompt to place the orders.

You can use the --noConfirm option to skip the confirmation.

## Limitations:

There is some error handling but not much:
- If it can't get a quote of an ETF, it'll stop. (Likely exchange is just closed.)
- If for some reason the total order cost exceeds what is in your cash account it will stop.
- If it detects an open order for any ETF it's configured to buy, it'll stop.
- If it any orders fail, it'll stop.

It uses a pretty simple algorithm for rebalancing:
- Go through each of the ETFs it's been configured to buy and calculate the sum of the differences of target ratio to the ratio if that ETF was bought. (sum((target-actual)^2))
- Choose the ETF with the lowest sum of differences.
- If you can't afford to buy that ETF then stop, else repeat.
- Buy all ETFs that have been chosen.

It's not an efficient algorithm but it handles many edge cases nicely and is simple and easy to understand.

It will place a Day Limit order for the current ask price.

It can also do a kind of dollar cost averaging by modifying DOLLAR_COST_AVERAGE.

It will just use currentCash / DOLLAR_COST_AVERAGE every time you run the script.

It only handles CAD cash and won't touch other currencies.
