#!/usr/bin/python

"""
Short term capital gain/loss calculator for use with
OptionsHouse .csv export of trade history
FIFO (First-In-First-Out) method for cost basis
"""

import csv
from datetime import datetime, timedelta


#2014 tax return, all sales in 2014
start_date = datetime(2014, 01, 01)
end_date = datetime(2015, 01, 01)
print start_date, end_date

""" Uncomment for custom range
start_date = None
end_date = None

while start_date == None:
  start_date = raw_input('start date, e.g. 18-Feb-2014 \n')
  try:
    start_date = datetime.strptime(start_date, "%d-%b-%Y")
  except ValueError:
    start_date = None
    print ' incorect format for date. try day-month-year'

while end_date == None:
  end_date = raw_input('end date, e.g. 18-Feb-2014 \n')
  try:
    end_date = datetime.strptime(end_date, "%d-%b-%Y")
  except ValueError:
    end_date = None
    print ' incorrect format for date. try day-month-year'
"""
def create_dt_obj(row):
  """create python datetime object from date
  and time columns (type:(string)) in .csv file
  Args:
      row from csvreader instance
  Returns
      Python Datetime.Datetime object
  """
  date_and_time = row[1] + ";" + row[2]
  dt_obj = datetime.strptime(
                                date_and_time,
                                "%d-%b-%Y;%H:%M:%S"
                            )
  return (dt_obj)

buy_side = {}
sell_side = []
dividends = []

with open('AccountHistoryReportFull.csv') as trades:
  reader = csv.reader(trades)
  for ndx, row in enumerate(reader):
    if ndx > 2:
      #create buy side dictionary
      if row[7] == 'BUY' and row[3] == 'Trade':
        dt_obj = create_dt_obj(row)
        row.append(dt_obj)
        #fees + commission per share
        fee_per_share = (float(row[12]) + float(row[13]))/float(row[8])
        row.append(fee_per_share)
        #row[9] = ticker symbol - keys of dictionary
        if row[9] not in buy_side.keys():
          buy_side[row[9]] = [row]
        else:
          buy_side[row[9]].append(row)
      #create sell side list...
      elif row[7] == 'SELL' and row[3] == 'Trade':
        dt_obj = create_dt_obj(row)
        row.append(dt_obj)
        sell_side.append(row)
      # Cash and money market dividend payouts
      elif row[3] == 'Deposit' and row[4].startswith(('Cash','Money')):
        dt_obj = create_dt_obj(row)
        row.append(dt_obj)
        dividends.append(row)
          
trades.close()

#chronological order - 
sell_side = sorted(sell_side, key = lambda trade: trade[-1])
total_proceeds = 0
total_cost_basis = 0
total_gain_loss = 0
short_term = []
long_term = []
#compare short vs. long term gain/loss
year = timedelta(days = 365)
with open('2014_tax_return_8949.csv', 'wb') as csvfile:
  spamwriter = csv.writer(csvfile)
  for trade in sell_side:
    gain_loss = 0
    sold_tikr = trade[9]
    sold_shares = float(trade[8])
    shares_sold = sold_shares
    sold_pps = float(trade[10])
    sold_fee = float(trade[12])
    sold_comm = float(trade[13])
    sell_side_fee_per_share = (sold_fee + sold_comm)/sold_shares
    sold_date = trade[-1]
    buy_lots = {}
    while sold_shares > 0:
      buy_blocks = buy_side[sold_tikr]
      buy_blocks = sorted(buy_blocks, key = lambda trade: trade[-2])
      #grab earliest block of bought shares of the ticker of interest
      bought_shares = float(buy_blocks[0][8])
      bought_pps = float(buy_blocks[0][10])
      buy_side_fee_per_share = float(buy_blocks[0][-1])
      bought_id = buy_blocks[0][0]
      bought_date = buy_blocks[0][-2]
      #compare to shares just sold
      if sold_shares >= bought_shares:
        cost_basis = (bought_shares * bought_pps) + (bought_shares * buy_side_fee_per_share)
        sale_price = bought_shares * sold_pps
        proceeds = (bought_shares * sold_pps) - (bought_shares * sell_side_fee_per_share)
        sold_shares -= bought_shares
        gain_loss += sale_price - cost_basis
        #clear block of bought shares
        for ndx,item in enumerate(buy_side[sold_tikr]):
          if item[0] == bought_id:
            buy_side[sold_tikr].pop(ndx)
        buy_lots[bought_id] = bought_date, bought_shares, cost_basis, proceeds
      else:
        cost_basis = (sold_shares * bought_pps) + (sold_shares * buy_side_fee_per_share)
        sale_price = sold_shares * sold_pps
        proceeds = (sold_shares * sold_pps) - (sold_shares * sell_side_fee_per_share)
        gain_loss += sale_price - cost_basis
        #subtract sold shares
        for ndx, item in enumerate(buy_side[sold_tikr]):
          if item[0] == bought_id:
            item[8] = float(item[8]) - sold_shares
        buy_lots[bought_id] = bought_date, sold_shares, cost_basis, proceeds
        sold_shares = 0
    #sold_shares empty
    #finalize cap gain/loss less any sell side fees or commission
    gain_loss -= (sold_fee + sold_comm)

    #print out for form IRS 8949 - attachment to schedule D
    #only print out if sale occurs within custom date range
    if trade[-1] > start_date and trade[-1] < end_date:
      #print '\n'
      for key, value in buy_lots.iteritems():
        holding_period = sold_date - value[0]
        total_proceeds += value[3]
        total_cost_basis += value[2]
        if holding_period < year:
          #print 'short term'
          pass
        else:
          #print 'long term'
          pass
        spamwriter.writerow(
                               [(str(value[1]) + ' sh. ' + sold_tikr)] + [value[0]] + \
                               [sold_date] + [value[3]] + [value[2]] + \
                               [round((value[3] - value[2]), 2)]
                            )
    total_gain_loss += gain_loss
csvfile.close()

  #print 'gain-loss', gain_loss
  #print '\n total capital gain/loss \n', total_gain_loss
total_dividends = 0

for dividend in dividends:
  if dividend[-1] > start_date and dividend[-1] < end_date:
    amount = float(dividend[14])
    print dividend[4], 'amount: ', amount
    total_dividends += amount
print '\n\n total dividends for given range', total_dividends

print 'total_proceeds', total_proceeds
print 'total_cost_basis', total_cost_basis
print 'total_proceeds - total_cost_basis', total_proceeds - total_cost_basis
