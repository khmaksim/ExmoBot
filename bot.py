import time
import logging
import decimal

class ScriptError(Exception):
    pass

class ScriptQuitCondition(Exception):
	pass

class Bot:
	def __init__(self, token, currency_buy, currency_sell, debug_mode=False):
		self.token = token
		self.pair = '{0}_{1}'.format(currency_buy, currency_sell)
		self.currency_sell = currency_sell
		self.currency_buy = currency_buy
		self.balances = {}
		self.profit = 0.1 / 100
		self.logger = logging.getLogger('Bot')
		self.debug_mode = debug_mode
		self.last_price_pair = 0

	def trade(self):
		try:
			order_life_time = 3
			open_orders = self.token.api_query('user_open_orders')
			orders_pair = open_orders.get(self.pair)

			self.current_price()
			return

			if orders_pair == None:
				if self.debug_mode:
					print(u'Открытых ордеров нет')
				self.logger.info(u'Открытых ордеров нет')

				if self.last_price_pair == 0:


				pair_list = self.token.api_query('pair_settings')
				
				if pair_list[self.pair] != None:
					self.balance()		# Обновление баланса
					cur_min_quantity = float(pair_list[self.pair].get('min_quantity'))		# Минимальное количество валюты для покупки/продажи
					commission_maker_percent = float(pair_list[self.pair].get('commission_maker_percent')) / 100

					# Если валюты больше чем минимальное количество крипты для покупки/продажи
					if float(self.balances[self.currency_buy]) >= cur_min_quantity:
						avg_price = self.avg_price_period(self.pair, 3)
						wanna_get = avg_price + avg_price * (commission_maker_percent + self.profit)

						if wanna_get != 0:
							# amount_currency = wanna_get / float(self.balances[self.currency_buy])
							self.create_order(float(self.balances[self.currency_buy]), wanna_get, 'sell')

					# Если баланс валюты для покупки продажи не нулевой
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
						raise ScriptQuitCondition('Выход, ждем пока не исполнятся/закроются все ордера на продажу')
					elif order.get('type') == 'buy':
						orders_buy.append(order)

				for order_buy in orders_buy:
					id_order = order_buy.get('order_id')
					
					if id_order == None:
						continue

					if self.debug_mode:
						print('Проверяем отложенный ордер', id_order)

					try:
						res = self.token.api_query('order_trades', {'order_id': id_order})
						# по ордеру уже есть частичное выполнение
						print(res)
						raise ScriptQuitCondition('Выход, продолжаем докуать валюту по тому курсу, по которому уже купили часть')
					except ScriptError as e:
						if 'Error 50304' in str(e):
							print(u'Частично исполненных ордеров нет')

							time_passed = time.time() - int(order_buy.get('created'))
							if time_passed > order_life_time * 60:
								self.cancel_order(id_order)
								raise ScriptQuitCondition('Отменяем ордер #' + str(id_order))
							else:
								raise ScriptQuitCondition('Выход, продолжаем надеяться купить валюту по указанному ранее курсу, со времени создания ордера прошло %s секунд' % str(time_passed))
						else:
							raise ScriptQuitCondition(str(e))
		except ScriptError as e:
			print(e)
		except ScriptQuitCondition as e:
			if self.debug_mode:
				print(e)
			pass
		except Exception as e:
			print("!!!!",e)

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

	# Получение баланса по всем валютам
	def balance(self):
		user_info = self.token.api_query('user_info')
		
		for k, v in user_info['balances'].items():
			self.balances[k] = v
			if v != '0':
				print('{0} [{1}]'.format(k, v))

	# Получение средней цены валюты за период времени
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

	def current_price(self):
		tickers = self.token.api_query('ticker')

		if ticker[self.pair] != None:
			print('Max price', ticker[self.pair]['high'])
			print('Min price', ticker[self.pair]['low'])






