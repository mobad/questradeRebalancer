## Questrade Rebalancer
Script to buy and sell stocks/ETFs according to a predefined ratio.

# This script is not trading on your behalf.
# All trades must be manually confirmed by yourself.
# By using this script you assume full responsibility any trades made. 

### Features
- List your Questrade accounts
- Per account rebalancing
- Show the best orders to make to keep your account balanced using your remaining cash
- Detect whether orders have already been created for the ETFs you've configured and not place any orders
- Actually place those orders
- Three strategies for rebalancing

### Authenticating

You must create a personal app on Questrade and generate an API key.

### Usage:

```
$ ./questraderebalancer -h
usage: questraderebalancer [-h] {show,rebalance} ...

Rebalance your Questrade account according to a predefined ratio.

positional arguments:
  {show,rebalance}
    show            Show various information about your account(s).
    rebalance       Rebalance your portfolio with various strategies.

optional arguments:
  -h, --help        show this help message and exit

```

```
$ ./questraderebalancer show -h
usage: questraderebalancer show [-h] {accounts,orders}

positional arguments:
  {accounts,orders}  accounts will display account details, orders will
                     display all open orders for all accounts.

optional arguments:
  -h, --help         show this help message and exit
```

```
$ ./questraderebalancer rebalance -h
usage: questraderebalancer rebalance [-h] [--preview-only]
                                        [--strategy {1,2,3}]
                                        [--import-ratios IMPORT_RATIOS]
                                        account

positional arguments:
  account               The account to rebalance.

optional arguments:
  -h, --help            show this help message and exit
  --preview-only        Test run. Doesn't place orders.
  --strategy {1,2,3}    Set the strategy type when calculating which
                        ETFs/stocks to buy and sell.
  --import-ratios IMPORT_RATIOS
                        Path to the ratios file. Defaults to
                        target_ratios.json in the current working directory.

```

### Strategies

1. Buy the stock that will decrease the sum of r^2 between the account portfolio
ratios and the target ratios.
2. Buy the stock that will decrease the sum of r^2 just from the available cash.
3. (TODO) Buy and sell to achieve account balance.

### Other

You can find the original repo [Here](https://github.com/mobad/questradeRebalancer)

###### Disclaimer
No blame thanks.
