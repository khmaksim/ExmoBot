import time
import logging
import decimal

class Bot:
	def __init__(self, token, currency_buy, currency_sell):
		self.token = token
		self.pair = '{0}_{1}'.format(currency_buy, currency_sell)
		self.currency_sell = currency_sell
		self.currency_buy = currency_buy
		self.balances = {}
		self.profit = 0.1 / 100
		self.logger = logging.getLogger('Bot')

	def trade(self):
		order_life_time = 3
		open_orders = self.token.api_query('user_open_orders')
		orders_pair = open_orders.get(self.pair)

		if orders_pair == None:
			print(u'Открытых ордеров нет')
			self.logger.info(u'Открытых ордеров нет')
			self.update_balance()

			pair_list = self.token.api_query('pair_settings')
			
			if pair_list[self.pair] != None:
				cur_min_quantity = float(pair_list[self.pair].get('min_quantity'))
				commission_maker_percent = float(pair_list[self.pair].get('commission_maker_percent')) / 100

				if float(self.balances[self.currency_buy]) >= cur_min_quantity:
					avg_price = self.avg_price_period(self.pair, 3)
					wanna_get = avg_price + avg_price * (commission_maker_percent + self.profit)

					if wanna_get != 0:
						# amount_currency = wanna_get / float(self.balances[self.currency_buy])
						self.create_order(float(self.balances[self.currency_buy]), wanna_get, 'sell')

				if float(self.balances[self.currency_sell]) >= 0:
					avg_price = self.avg_price_period(self.pair, 3)
					need_price = avg_price - avg_price * (commission_maker_percent + self.profit)
					
					if need_price != 0:
						amount_currency = float(self.balances[self.currency_sell]) / need_price
					
						if amount_currency > cur_min_quantity:
							self.create_order(amount_currency, need_price, 'buy')
		else:
			orders_buy = []		# Список орденов на покупку	
			for order in orders_pair:
				if order.get('type') == 'sell':
					continue
				elif order.get('type') == 'buy':
					orders_buy.append(order)

			for order_buy in orders_buy:
				id_order = order_buy.get('order_id')
				
				if id_order == None:
					continue

				try:
					res = self.token.api_query('order_trades', {'order_id': id_order})
					# по ордеру уже есть частичное выполнение
				except ScriptError as e:
					if 'Error 50304' in str(e):
						print(u'Частично исполненных ордеров нет')

					time_passed = time.time() - order_buy.get('created')
					if time_passed > order_life_time * 60:
						cancel_order(id_order)

	def create_order(self, amount, price, type_order):
		# Округление до 2-х знаков после запятой (ограничение EXMO)
		decimal_price = decimal.Decimal(str(price)).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
		price = float(decimal_price)

		res = self.token.api_query('order_create', {'pair': self.pair, 
											'quantity': amount,
    										'price': price,
    										'type': type_order})
		if res.get('result') == True:
			if type_order == 'buy':
				self.logger.info(u'Создан ордер #{0} на покупку'.format(res.get('order_id')))
			else:
				self.logger.info(u'Создан ордер #{0} на продажу'.format(res.get('order_id')))

			print(u'Создан ордер #{0}'.format(res.get('order_id')))

	def cancel_order(self, id_order):
		res = self.token.api_query('order_cancel', {'order_id': id_order})

		if res.get('result') == True:
			self.logger.info(u'Отменен ордер #{0}'.format(id_order))				
			print(u'Отменен ордер #{0}'.format(id_order))

	def update_balance(self):
		user_info = self.token.api_query('user_info')
		
		for k, v in user_info['balances'].items():
			self.balances[k] = v
			if v != '0':
				print('{0} [{1}]'.format(k, v))

	def avg_price_period(self, pair=None, period=1):
		if pair == None:
			pair = self.pair

		trades = self.token.api_query('trades', {'pair': pair})
		sum_trade = 0
		n = 0

		for trade in trades[pair]:
			time_passed = time.time() - trade.get('date')
			
			if time_passed < (period * 60):
				sum_trade += float(trade.get('price'))
				n += 1

		if n == 0:
			n = 1
		
		return (sum_trade / n)		





