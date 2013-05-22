"""
by Charles Steinke

dependencies:
httplib2
json

"""

import httplib2
import json

####### DEFINITIONS #######

### holder class
class Exchange(object):
	""" A exchange represents one exchange rate, aka USD_JPY@75 or usd to jpy at 1 to 75 """
	def __init__(self, start_currency, end_currency, rate):
		self.start_currency = start_currency
		self.end_currency = end_currency
		self.rate = float(rate)

	def exchangeit(self, an_amount):
		return an_amount * self.rate

	def __repr__(self):
		return "<Exchange %s to %s at %s>" % (self.start_currency, self.end_currency, self.rate)


#### arbitrage finding stuff

def is_valid_trade_path(x, y, z):
	"""x exchange to y exchange to z exchange"""
	if x.end_currency == y.start_currency:
		if y.end_currency == z.start_currency:
			if x.start_currency == z.end_currency:
				# then is valid path
				return True

	return False

### loop through master dict garnering valid trade paths
def find_valid_trade_routes(currency, masterdict):
	valid_paths = []
	for exchange in masterdict[currency]:
		for secondary_exchange in masterdict[exchange.end_currency]:
			for tertiary_exchange in masterdict[secondary_exchange.end_currency]:
				if is_valid_trade_path(exchange, secondary_exchange, tertiary_exchange):
					path = (exchange, secondary_exchange, tertiary_exchange)
					valid_paths.append(path)

	return valid_paths

def find_percent_profit(paths):
	results = []
	for path in paths:
		start_amount = 1.0

		## execute exchanges
		after_first_exchange = path[0].exchangeit(start_amount)
		after_second_exchange = path[1].exchangeit(after_first_exchange)
		after_third_exchange = path[2].exchangeit(after_second_exchange)

		## convert to %
		percent = int((after_third_exchange - start_amount) * 100)

		str_repr = (
			"trading from " + path[0].start_currency + 
			" to " +  path[1].start_currency + 
			" to " + path[2].start_currency + 
			" back to " + path[2].end_currency +
			" results in " + str(percent) + " percent net gain/loss."
		)
		### this broken up so results can be sorted by %
		result_tuple = (percent, str_repr)
		results.append(result_tuple)

	return results


### http fetching and stuff

def connect_and_fetch(dest_url):
	h = httplib2.Http()
	try:
		resp, content = h.request(dest_url)
	except httplib2.ServerNotFoundError:
		return "Error connecting to requested server."

	if resp["content-type"] == "application/json; charset=UTF-8":
		# convert content to a dict
		return json.loads(content)
	else:
		return "Content type was not valid json or was not labeled correctly in header."

###################  

##################

if __name__ == "__main__":

	content = connect_and_fetch("http://fx.priceonomics.com/v1/rates/")

	### build list of all currencies
	currencies = []
	for key in content.keys():
		tmp = key.split("_")
		if tmp[0] not in currencies:
			currencies.append(tmp[0])

	print "\n available currencies were " + str(currencies) + "\n"

	### build list of exchange objects for each currency (where the exchange starts in that currency)

	# masterdict will look like this
	# { currencyname : [ list of exchanges starting with currency ]}
	masterdict = {}

	for currency in currencies:
		masterdict[currency] = []

	# loop all keys once and assign exchanges to mastdict
	# content data should look like this (hopefully) { USD_JPY : somenumber }
	for key in content.keys():
		tmp = key.split("_")
		start_currency = tmp[0]
		end_currency = tmp[1]
		rate = content[key]

		### ignore the self to self exchanges
		if start_currency != end_currency:
	 		masterdict[start_currency].append( Exchange( start_currency, end_currency, rate ) )

	### find paths and return results
	for currency in currencies:
		paths = find_valid_trade_routes( currency, masterdict )
		print "-------" + currency + "-------"
		## sort results by perecent and print
		for x in sorted(find_percent_profit( paths ), key= lambda x:x[0], reverse=True):
			print x[1]
