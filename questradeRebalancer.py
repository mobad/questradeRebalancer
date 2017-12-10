#!/bin/env python3

import argparse
from sys import float_info
from QuestradeApi import QuestradeApi

AUTH_TOKEN = ""

QUESTRADE_ECN = 0.0035
DOLLAR_COST_AVERAGE = 1.0

questrade_api = QuestradeApi(AUTH_TOKEN)
questrade_api.setup()


def get_symbol_target_rations_for_account(account_type):
    # Please make sure each account adds to 100 or this script will not work correctly!
    ratios = {
        'Margin': {'VCN.TO': 40, 'XUU.TO': 40, 'XEF.TO': 20},
        'TFSA': {'VCN.TO': 40, 'XUU.TO': 40, 'XEF.TO': 20},
        'RRSP': {'VCN.TO': 40, 'XUU.TO': 40, 'XEF.TO': 20}
    }
    return ratios[account_type]


def get_available_cash(account_id):
    balances = questrade_api.get_balances(account_id)
    cash_balances = balances['perCurrencyBalances']
    for currency in cash_balances:
        if currency['currency'] == 'CAD':
            return currency['cash']
    return None


def get_positions_value(account_id, symbols):
    position_values = {}
    for symbol in symbols:
        position_values[symbol] = 0

    positions_total = 0
    positions = questrade_api.get_positions(account_id)
    for position in positions['positions']:
        symbol = position['symbol']
        if symbol in position_values:
            value = position['currentMarketValue']
            position_values[symbol] = value
            positions_total += value

    return positions_total, position_values


def get_internal_symbols(symbols):
    symbol_id_dicts = {}
    for symbol in symbols:
        symbol_id = questrade_api.get_id_from_symbol_name(symbol)
        symbol_id_dicts[symbol] = symbol_id

    return symbol_id_dicts


def get_symbol_quotes(symbol_ids):
    symbol_quotes = {}
    quotes = questrade_api.get_market_quotes(symbol_ids)
    for quote in quotes['quotes']:
        symbol_quotes[quote['symbol']] = quote['askPrice']

    return symbol_quotes


def get_symbol_of_smallest_target_ratio_differences(positions_total,
                                                    symbol_target_ratios,
                                                    symbol_quotes,
                                                    position_values):
    min_mag_diff = float_info.max
    min_symbol = None

    for selected_symbol in symbol_target_ratios.keys():
        total = positions_total + symbol_quotes[selected_symbol]

        sum_of_mag_diff = 0
        for symbol, position_value in position_values.items():
            value = position_value
            if selected_symbol == symbol:
                value += symbol_quotes[selected_symbol]
            diff = (symbol_target_ratios[symbol] / 100.0) - (value / total)
            sum_of_mag_diff += diff * diff

        if sum_of_mag_diff < min_mag_diff:
            min_mag_diff = sum_of_mag_diff
            min_symbol = selected_symbol

    return min_symbol


def get_buy_orders(cash_total, positions_total, symbol_target_ratios,
                   symbol_quotes, position_values):
    buy_orders = {}
    remaining = cash_total
    new_positions_total = positions_total

    while remaining > QUESTRADE_ECN:
        # Buy the stock which will produce the smallest difference in ratios
        symbol = get_symbol_of_smallest_target_ratio_differences(
            new_positions_total, symbol_target_ratios,
            symbol_quotes, position_values)
        # If we can't afford the optimum stock then stop
        if not symbol or (symbol_quotes[symbol] + QUESTRADE_ECN) > remaining:
            break

        buy_orders[symbol] = buy_orders.get(symbol, 0) + 1
        remaining -= symbol_quotes[symbol] + QUESTRADE_ECN
        new_positions_total += symbol_quotes[symbol]
        position_values[symbol] += symbol_quotes[symbol]

    return buy_orders


def place_buy_orders(account_id, symbol_id_dict, buy_orders, symbol_quotes):
    open_orders = questrade_api.get_orders(account_id, stateFilter="Open")
    for open_order in open_orders['orders']:
        if open_order['symbol'] in buy_orders:
            msg = "There is an open order for {} on account {}. stopping."
            msg.format(open_order['symbol'], account_id)
            print(msg)
            return False

    for symbol, to_buy in buy_orders.items():
        symbol_id = symbol_id_dict[symbol]
        symbol_quote = symbol_quotes[symbol]
        order = questrade_api.place_order(
            account_id, symbol_id, to_buy, symbol_quote)['orders'][0]
        if order['rejectionReason'] != '':
            reject_reason = order['rejectionReason']
            msg = "Order for {} x {} @ {} on account {} was rejected for " + \
                  "reason {}, stopping."
            msg = msg.format(
                to_buy, symbol, symbol_quote, account_id, reject_reason)
            print(msg)
            return False
        msg = "Order for {} x {} @ {} on account {} was placed successfully."
        msg = msg.format(to_buy, symbol, symbol_quote, account_id)
        print(msg)

    return True


def rebalance(account_id, symbol_target_ratios,
              should_place_orders, should_confirm_orders):
    symbols = symbol_target_ratios.keys()

    cash_total = get_available_cash(account_id) / DOLLAR_COST_AVERAGE

    symbol_id_dict = get_internal_symbols(symbols)
    positions_total, position_values = get_positions_value(account_id, symbols)

    symbol_quotes = get_symbol_quotes(list(symbol_id_dict.values()))
    for symbol, quote in symbol_quotes.items():
        if not quote:
            msg = "Something went wrong getting the quote of {}, stopping."
            msg = msg.format(symbol)
            print(msg)
            print("Most likely the exchange is just closed.")
            return False 

    buy_orders = get_buy_orders(cash_total, positions_total,
                                symbol_target_ratios, symbol_quotes,
                                position_values)

    if len(buy_orders) == 0:
        print("Not enough money to make any orders, stopping")
        return True

    order_price_sum = 0.0
    fee_sum = 0.0
    for symbol, to_buy in buy_orders.items():
        order_price = to_buy * symbol_quotes[symbol]
        order_price_sum += order_price
        fee = to_buy * QUESTRADE_ECN
        fee_sum += fee

        msg = "Will place a Day Limit order for {} x {} @ {} on account " + \
              "{} costing ${} CAD and ${} CAD in ECN fees"
        msg = msg.format(to_buy, symbol, symbol_quotes[symbol],
                         account_id, order_price, fee)
        print(msg)

    # Should never happen but just in case...
    total_cost = order_price_sum + fee_sum
    if total_cost > cash_total:
        msg = "Order total cost of ${} CAD is higher than total cash of " + \
              "${} CAD, stopping"
        msg = msg.format(total_cost, cash_total)
        print(msg)
        return False

    msg = "Total cost is ${} CAD and ${} CAD in fees, leaving you with ${} " + \
          "CAD in cash"
    msg = msg.format(order_price_sum, fee_sum, cash_total - total_cost)
    print(msg)

    if should_place_orders:
        if should_confirm_orders:
            msg = "Please type CONFIRM in all CAPS to place orders: "
            confirmation_text = input(msg)
            if confirmation_text.strip() != 'CONFIRM':
                print("Confirmation was not equal to CONFIRM, stopping.")
                return False

        return place_buy_orders(account_id, symbol_id_dict,
                                buy_orders, symbol_quotes)

    return True


parser = argparse.ArgumentParser(description='Buys ETFs according to the configured ratios')
subparsers = parser.add_subparsers(dest='command')
listAccounts = subparsers.add_parser('listAccounts', help='Lists your Questrade accounts')
showOrders = subparsers.add_parser('showOrders', help='Shows the orders that would be made')
showOrders.add_argument('accountType', help='The type of the account')
showOrders.add_argument('accountNumber', help='The number of the account')
placeOrders = subparsers.add_parser('placeOrders', help='Places orders to rebalance your account')
placeOrders.add_argument('--noConfirm', action='store_true', help='This will skip the place order confirmation and immediately place the orders')
placeOrders.add_argument('accountType', help='The type of the account')
placeOrders.add_argument('accountNumber', help='The number of the account')
args = parser.parse_args()

if args.command == 'listAccounts':
    accounts = questrade_api.get_accounts()
    for acc in accounts['accounts']:
        print(acc['type'], acc['number'])
        exit(0)
else:
    shouldPlaceOrders = args.command == 'placeOrders'
    shouldConfirmOrders = True
    if shouldPlaceOrders:
        shouldConfirmOrders = not args.noConfirm
    accountType = args.accountType
    accountNumber = args.accountNumber

    success = rebalance(
        accountNumber,
        get_symbol_target_rations_for_account(accountType),
        shouldPlaceOrders,
        shouldConfirmOrders)

    exit(not success)
