from pybit import WebSocket, HTTP
import time
import argparse


class TradingPair:
    def __init__(self, traded_symbol: str, qty: float, round_qty: int, round_price: int, step: float, modif: float, max_size_buy: float, max_size_sell:float, trailing:bool, stop_loss:float):
        self.symbol = traded_symbol
        self.qty = qty
        self.round_qty = round_qty
        self.round_price = round_price
        self.step_to_takeprofit = step
        self.modif = modif
        self.max_size_buy = max_size_buy
        self.max_size_sell = max_size_sell
        self.trailing = trailing
        self.stop_loss = stop_loss

class Trader:
    def __init__(self, pair: TradingPair, api_public, api_secret):
        self.pair = pair
        self.private_subs = ['position', 'order', 'execution']
        self.public_subs = []
        self.session = HTTP(endpoint='https://api.bybit.com', api_key=api_public, api_secret=api_secret)
        if pair.symbol.endswith('USD'):
            url_publ = 'realtime'
            url_priv = 'realtime'
            self.public_subs.append('klineV2.1.' + pair.symbol)
        else:
            self.public_subs.append('candle.1.' + pair.symbol)
            url_publ = 'realtime_public'
            url_priv = 'realtime_private'
        self.public_subs.append('orderBookL2_25.' + pair.symbol)
        self.ws_private = WebSocket(endpoint='wss://stream.bybit.com/'+ url_priv, subscriptions=self.private_subs, api_key=api_public, api_secret=api_secret)
        self.ws_public = WebSocket(endpoint='wss://stream.bybit.com/'+ url_publ, subscriptions=self.public_subs)
        self.in_buy_position = 0
        self.in_sell_position = 0
        self.exit_buy_id = None
        self.entry_buy_id = None
        self.exit_sell_id = None
        self.entry_sell_id = None
        self.last_buy_entry_price = 0
        self.last_sell_entry_price = 0
        self.last_buy_exit_price = 0
        self.last_sell_exit_price = 0
        self.need_to_repair = False
        self.realised_pnl = 0
        self.cum_realised_pnl = 0
        self.total_quantities = [self.pair.qty*2**i for i in range(7)]

    def get_position_unrpnl(self):
        self.unrealised_pnl_percent = float(0)
        if self.pair.symbol in self.position:
            try:
                self.position_open = self.session.my_position(symbol=self.pair.symbol)['result']
                # For invers perpetual contract
                if self.pair.symbol.endswith('USD'):
                    self.unrealised_pnl = float(self.position_open['unrealised_pnl'])
                    #print(self.position_open)
                    self.stop = float(format(round(self.wallet_balance * (-self.pair.stop_loss/100), 9), '.9f'))
                    self.unrealised_pnl_percent = float(format(round(self.unrealised_pnl / self.wallet_balance, 9), '.9f'))
                    print('To STOP BOT: Balance {} STOP {} {}% UnRealizedPNL {} {}%'.format(self.wallet_balance, self.stop, -self.pair.stop_loss, self.unrealised_pnl, self.unrealised_pnl_percent))
                if self.pair.symbol.endswith('USDT'):
                    self.unrealised_pnl = float(self.position_open[0]['unrealised_pnl']) + float(self.position_open[1]['unrealised_pnl'])
                    self.unrealised_pnl = float(format(round(self.unrealised_pnl, 9), '.9f')) if float(self.unrealised_pnl) != 0 else 0
                    self.stop = float(format(round(self.wallet_balance * (-self.pair.stop_loss/100), 9), '.9f'))
                    self.unrealised_pnl_percent = float(format(round(self.unrealised_pnl / self.wallet_balance, 9), '.9f')) if float(self.unrealised_pnl) != 0 else 0
                    print('To STOP BOT: Balance {} STOP {} {}% UnRealizedPNL {} {}%'.format(self.wallet_balance, self.stop, -self.pair.stop_loss, self.unrealised_pnl, self.unrealised_pnl_percent))
            except:
                print("Repeat try get_position_open()")

    def reload_position (self):
        self.position = self.ws_private.fetch('position')
        if self.pair.symbol in self.position:
            # For invers perpetual contract
            if self.pair.symbol.endswith('USD'):
                    if 'side' in self.position[self.pair.symbol]:
                        self.position_side = self.position[self.pair.symbol]['side']
                    if 'size' in self.position[self.pair.symbol]:
                        self.position_buy_size = float(self.position[self.pair.symbol]['size'])
                        self.position_sell_size = float(self.position[self.pair.symbol]['size'])
                    if 'entry_price' in self.position[self.pair.symbol]:
                        self.position_buy_entry_price = float(self.position[self.pair.symbol]['entry_price'])
                        self.position_sell_entry_price = float(self.position[self.pair.symbol]['entry_price'])
                    if 'order_margin' in self.position[self.pair.symbol]:
                        self.position_buy_order_margin = float(self.position[self.pair.symbol]['order_margin'])
                        self.position_sell_order_margin = float(self.position[self.pair.symbol]['order_margin'])
                    self.realised_pnl = float(self.position[self.pair.symbol]['realised_pnl'])
                    self.cum_realised_pnl = float(self.position[self.pair.symbol]['cum_realised_pnl'])
                    self.wallet_balance = float(self.position[self.pair.symbol]['wallet_balance'])
            else:
                self.position_side = self.position[self.pair.symbol]
                self.position_buy_size = self.position[self.pair.symbol]['Buy']['size']
                self.position_sell_size = self.position[self.pair.symbol]['Sell']['size']
                self.position_buy_entry_price = self.position[self.pair.symbol]['Buy']['entry_price']
                self.position_sell_entry_price = self.position[self.pair.symbol]['Sell']['entry_price']
                self.position_buy_order_margin = self.position[self.pair.symbol]['Buy']['order_margin']
                self.position_sell_order_margin = self.position[self.pair.symbol]['Sell']['order_margin']
                self.realised_pnl = float(self.position[self.pair.symbol]['Buy']['realised_pnl']) + float(self.position[self.pair.symbol]['Sell']['realised_pnl'])
                cum_pnl_buy = float(self.position[self.pair.symbol]['Buy']['cum_realised_pnl'])
                cum_pnl_sell = float(self.position[self.pair.symbol]['Sell']['cum_realised_pnl'])
                self.cum_realised_pnl = cum_pnl_buy if cum_pnl_buy != 0 else cum_pnl_sell
                self.position_margin = self.position[self.pair.symbol]['Buy']['position_margin'] if self.position[self.pair.symbol]['Buy']['position_margin'] != 0 else self.position[self.pair.symbol]['Sell']['position_margin']
                self.wallet_balance = float(self.position_buy_order_margin) + float(self.position_sell_order_margin) + float(self.position_margin)

    def create_sell_entry(self, order_type='Limit', time_in_force='PostOnly', side='Sell', reduce_only=False):
        self.reload_position()
        geometry_modif = False
        new_qty = self.pair.qty
        new_price = 0.0
        if self.pair.symbol in self.position:
            if 'Sell' in self.position_side and self.position_sell_size > self.pair.max_size_sell:
                    return
            if 'Sell' in self.position_side and self.position_sell_size > 0:
                new_qty = round(self.position_sell_size, self.pair.round_qty)
                if geometry_modif == True :
                    if self.position_buy_size > self.pair.qty * 30 :
                        qty = self.pair.qty / 10
                    else:
                        qty = self.pair.qty
                    new_price = round(self.position_buy_entry_price * (1 + (self.position_buy_size / qty) * self.pair.modif), self.pair.round_price)
                else:
                    new_price = round(self.position_sell_entry_price * (1 + (self.position_sell_size / self.pair.qty) * self.pair.modif), self.pair.round_price)
        book_price = 99999
        book = self.ws_public.fetch(self.public_subs[1])
        for o in book:
            if o['side'] == 'Sell' and float(o['size']) > 10:
                book_price = min(book_price, round(float(o['price']), self.pair.round_price))
        if new_price == 0:
            new_price = book_price
        else:
            new_price = max(new_price, book_price)
        repeat_try = False
        print("Create sell entry Qty:{} Price:{} Day_pnl: {} Cum_pnl: {}".format(new_qty, new_price, self.realised_pnl, self.cum_realised_pnl))
        try:
            if new_price > 0:
                result = self.session.place_active_order(side=side, symbol=self.pair.symbol, order_type=order_type, qty=new_qty, price=new_price, time_in_force=time_in_force, reduce_only=reduce_only, close_on_trigger=False)['result']
                self.entry_sell_id = result['order_id']
                self.last_sell_entry_price = new_price
                print("Result create sell entry", result)
            else:
                print("Bad price on websocket data waiting 30 sec :: try to create sell entry", new_qty, new_price)
                time.sleep(30)
                repeat_try = True
        except:
            print("Repeat try to create sell entry", new_qty, new_price)
            repeat_try = True
        if repeat_try:
            self.create_sell_entry()

    def create_buy_entry(self, order_type='Limit', time_in_force='PostOnly', side='Buy', reduce_only=False):
        self.reload_position()
        geometry_modif = False
        new_qty = self.pair.qty
        new_price = 0.0
        if self.pair.symbol in self.position:
                if 'Buy' in self.position_side and self.position_buy_size > self.pair.max_size_buy:
                        return
                if 'Buy' in self.position_side and self.position_buy_size > 0:
                    new_qty = round(self.position_buy_size, self.pair.round_qty)
                    if geometry_modif == True :
                        if self.position_buy_size > self.pair.qty * 30 :
                            qty = self.pair.qty / 10
                        else:
                            qty = self.pair.qty
                        new_price = round(self.position_buy_entry_price * (1 - (self.position_buy_size / qty) * self.pair.modif), self.pair.round_price)
                    else:
                        new_price = round(self.position_buy_entry_price * (1 - (self.position_buy_size / self.pair.qty) * self.pair.modif), self.pair.round_price)
        book_price = 0
        book = self.ws_public.fetch(self.public_subs[1])
        for o in book:
            if o['side'] == 'Buy' and float(o['size']) > 10:
                book_price = max(book_price, round(float(o['price']), self.pair.round_price))
        if new_price == 0:
            new_price = book_price
        else:
            new_price = min(new_price, book_price)
        repeat_try = False
        print("Create buy entry Qty:{} Price:{} Day_pnl: {} Cum_pnl: {}".format(new_qty, new_price, self.realised_pnl, self.cum_realised_pnl))
        try:
            if new_price > 0:
                result = self.session.place_active_order(side=side, symbol=self.pair.symbol, order_type=order_type, qty=new_qty, price=new_price, time_in_force=time_in_force, reduce_only=reduce_only, close_on_trigger=False)['result']
                self.entry_buy_id = result['order_id']
                self.last_buy_entry_price = new_price
                print("result create buy entry", result)
            else:
                print("Bad price on websocket data waiting 30 sec :: try to create buy entry", new_qty, new_price)
                time.sleep(30)
                repeat_try = True
        except:
            print("Repeat try to create buy entry", new_qty, new_price)
            repeat_try = True
        if repeat_try:
            self.create_buy_entry()

    def update_buy_entry(self):
        new_price = 0
        book = self.ws_public.fetch(self.public_subs[1])
        check_order = False
        for o in book:
            if o['side'] == 'Buy':
                new_price = max(new_price, round(float(o['price']), self.pair.round_price))
        if abs(new_price - self.last_buy_entry_price) < 1e-6:
            return
        try:
            self.session.replace_active_order(symbol=self.pair.symbol, order_id=self.entry_buy_id, p_r_price=new_price, p_r_qty=self.pair.qty)
            self.last_buy_entry_price = new_price
        except:
            print('Error! Cannot update entry order!')
            check_order = True
        print("update buy entry Qty:{} Price:{} Day_pnl: {} Cum_pnl: {}".format(self.pair.qty, new_price, self.realised_pnl, self.cum_realised_pnl))
        if check_order:
            try:
                orders = self.session.get_active_order(symbol=self.pair.symbol)['result']['data']
            except:
                return
            found = False
            for o in orders:
                if self.entry_buy_id == o['order_id'] and o['order_status'] in ['New', 'Created', 'PartiallyFilled']:
                    found = True
            if not found:
                try:
                    self.session.cancel_active_order(symbol=self.pair.symbol, order_id=self.entry_buy_id)
                except:
                    print('Old entry buy order was not cancelled. Probably it does not exist')
                    self.need_to_repair = True

    def update_sell_entry(self):
        new_price = self.last_sell_entry_price
        book = self.ws_public.fetch(self.public_subs[1])
        check_order = False
        for o in book:
            if o['side'] == 'Sell':
                new_price = min(new_price, round(float(o['price']), self.pair.round_price))
        if abs(new_price - self.last_sell_entry_price) < 1e-6:
            return
        try:
            self.session.replace_active_order(symbol=self.pair.symbol, order_id=self.entry_sell_id, p_r_price=new_price, p_r_qty=self.pair.qty)
            self.last_sell_entry_price = new_price
        except:
            print('Error! Cannot update entry order!')
            check_order = True
        print("update sell entry Qty:{} Price:{} Day_pnl: {} Cum_pnl: {}".format(self.pair.qty, new_price, self.realised_pnl, self.cum_realised_pnl))
        if check_order:
            try:
                orders = self.session.get_active_order(symbol=self.pair.symbol)['result']['data']
            except:
                return
            found = False
            for o in orders:
                if self.entry_sell_id == o['order_id'] and o['order_status'] in ['New', 'Created', 'PartiallyFilled']:
                    found = True
            if not found:
                try:
                    self.session.cancel_active_order(symbol=self.pair.symbol, order_id=self.entry_sell_id)
                except:
                    print('Old entry sell order was not cancelled. Probably it does not exist')
                    self.need_to_repair = True

    def create_buy_exit(self, order_type='Limit', time_in_force='PostOnly'):
        self.reload_position()
        if self.pair.symbol in self.position:
            if 'Buy' in self.position_side and self.position_buy_size > 0:
                new_price = round(self.position_buy_entry_price + self.pair.step_to_takeprofit, self.pair.round_price)
                book = self.ws_public.fetch(self.public_subs[1])
                book_price = new_price
                for o in book:
                    if o['side'] == 'Buy' and self.pair.trailing:
                        book_price = max(book_price, round(float(o['price']) + self.pair.step_to_takeprofit, self.pair.round_price))
                    if o['side'] == 'Sell' and not self.pair.trailing:
                        if book_price == new_price:
                            book_price = round(float(o['price']), self.pair.round_price)
                        book_price = min(book_price, round(float(o['price']), self.pair.round_price))
                new_price = max(new_price, book_price)
                print("create buy exit Qty:{} Price:{} Day_pnl: {} Cum_pnl: {}".format(self.position_buy_size, new_price, self.realised_pnl, self.cum_realised_pnl))
                if self.exit_buy_id is None:
                    try:
                        result = self.session.place_active_order(side='Sell', symbol=self.pair.symbol, order_type=order_type, qty=self.position_buy_size, price=new_price, time_in_force=time_in_force, reduce_only=True, close_on_trigger=False)['result']
                        self.exit_buy_id = result['order_id']
                        self.last_buy_exit_price = new_price
                    except:
                        print('Error! Cannot create buy exit order')
                        self.need_to_repair = True
                elif abs(new_price - self.last_buy_exit_price) > 1e-6:
                    try:
                        self.session.replace_active_order(symbol=self.pair.symbol, order_id=self.exit_buy_id, p_r_price=new_price, p_r_qty=self.position_buy_size)
                        self.last_buy_exit_price = new_price
                    except:
                        print('Error! Cannot update buy exit order')
                        self.need_to_repair = True

    def create_sell_exit(self, order_type='Limit', time_in_force='PostOnly'):
        self.reload_position()

        if self.pair.symbol in self.position:
            if 'Sell' in self.position_side and self.position_sell_size > 0:
                new_price = round(self.position_sell_entry_price - self.pair.step_to_takeprofit, self.pair.round_price)
                book = self.ws_public.fetch(self.public_subs[1])
                book_price = new_price
                for o in book:
                    if o['side'] == 'Sell' and self.pair.trailing:
                        book_price = min(book_price, round(float(o['price']) - self.pair.step_to_takeprofit, self.pair.round_price))
                    if o['side'] == 'Buy' and not self.pair.trailing:
                        if book_price == new_price:
                            book_price = round(float(o['price']), self.pair.round_price)
                        book_price = max(book_price, round(float(o['price']), self.pair.round_price))
                new_price = min(new_price, book_price)
                print("create sell exit Qty:{} Price:{} Day_pnl: {} Cum_pnl: {}".format(self.position_sell_size, new_price, self.realised_pnl, self.cum_realised_pnl))
                if self.exit_sell_id is None:
                    try:
                        result = self.session.place_active_order(side='Buy', symbol=self.pair.symbol, order_type=order_type, qty=self.position_sell_size, price=new_price, time_in_force=time_in_force, reduce_only=True, close_on_trigger=False)['result']
                        self.exit_sell_id = result['order_id']
                        self.last_sell_exit_price = new_price
                    except:
                        print('Error! Cannot create sell exit order')
                        self.need_to_repair = True
                elif abs(new_price - self.last_sell_exit_price) > 1e-6:
                    try:
                        self.session.replace_active_order(symbol=self.pair.symbol, order_id=self.exit_sell_id, p_r_price=new_price, p_r_qty=self.position_sell_size)
                        self.last_sell_exit_price = new_price
                    except:
                        print('Error! Cannot update sell exit order')
                        self.need_to_repair = True
    def run(self):
        last_entry_buy_try = time.time()
        last_entry_sell_try = time.time()
        check_orders = time.time()
        try:
            self.session.cancel_all_active_orders(symbol=self.pair.symbol)
        except:
            print("Cannot cancel all orders")
        self.need_to_repair = True
        while 1:
            time.sleep(0.25)
            self.reload_position()
            #execution = self.ws_private.fetch('execution')
            #if len(execution) > 0:
            #    print(execution)
            # if len(position) > 0:
            #    print('Buy', position[self.pair.symbol]['Buy'])
            #    print('Sell', position[self.pair.symbol]['Sell'])
            if self.pair.symbol not in self.position:
                last_entry_buy_try = time.time()
                last_entry_sell_try = time.time()
                self.exit_buy_id = None
                self.exit_sell_id = None
                self.in_buy_position = 0
                self.in_sell_position = 0
                try:
                    self.session.cancel_all_active_orders(symbol=self.pair.symbol)
                except:
                    print("Cannot cancel all orders")
                if self.pair.max_size_buy > 0:
                    self.create_buy_entry()
                if self.pair.max_size_sell > 0:
                    self.create_sell_entry()
                time.sleep(1)
            else:
                # create exits and new entries when position size has changed
                if 'Buy' in self.position_side and self.position_buy_order_margin == 0:
                    if self.pair.max_size_buy > 0:
                        self.create_buy_entry()
                        self.create_buy_exit()
                        time.sleep(1)
                elif 'Buy' in self.position_side and self.in_buy_position > 0 and self.position_buy_size == 0:
                    self.exit_buy_id = None
                    self.in_buy_position = 0
                    if self.entry_buy_id is not None:
                        try:
                            self.session.cancel_active_order(symbol=self.pair.symbol, order_id=self.entry_buy_id)
                        except:
                            print("Cannot cancel old entry sell order")
                        self.entry_buy_id = None
                elif 'Buy' in self.position_side and self.in_buy_position < self.position_buy_size and self.position_buy_size in self.total_quantities:
                    self.in_buy_position = self.position_buy_size
                    if self.pair.max_size_buy > 0:
                        self.create_buy_exit()

                if 'Sell' in self.position_side and self.position_sell_order_margin == 0:
                    if self.pair.max_size_sell > 0:
                        self.create_sell_entry()
                        self.create_sell_exit()
                        time.sleep(1)
                elif 'Sell' in self.position_side and self.in_sell_position > 0 and self.position_sell_size == 0:
                    self.exit_sell_id = None
                    self.in_sell_position = 0
                    if self.entry_sell_id is not None:
                        try:
                            self.session.cancel_active_order(symbol=self.pair.symbol, order_id=self.entry_sell_id)
                        except:
                            print("Cannot cancel old entry sell order")
                        self.entry_sell_id = None
                elif 'Sell' in self.position_side and self.in_sell_position < self.position_sell_size and self.position_sell_size in self.total_quantities:
                    self.in_sell_position = self.position_sell_size
                    if self.pair.max_size_sell > 0:
                        self.create_sell_exit()

                # update first buy entry
                if ('Buy' in self.position_side or 'None' in self.position_side) and last_entry_buy_try + 1 < time.time() and self.position_buy_size  == 0  and self.position_buy_order_margin > 0:
                    if self.pair.max_size_buy > 0:
                        self.update_buy_entry()
                        last_entry_buy_try = time.time()

                # update first sell entry
                if ('Sell' in self.position_side or 'None' in self.position_side) and last_entry_sell_try + 1 < time.time() and self.position_sell_size == 0 and self.position_sell_order_margin > 0:
                    if self.pair.max_size_sell > 0:
                        self.update_sell_entry()
                        last_entry_sell_try = time.time()

                # repair all orders when something went wrong
                if self.need_to_repair:
                    self.need_to_repair = False
                    print("TIME TO REPAIR!")
                    try:
                        self.session.cancel_all_active_orders(symbol=self.pair.symbol)
                    except:
                        print("Cannot cancel all orders")
                    self.exit_buy_id = None
                    self.exit_sell_id = None
                    if self.pair.max_size_buy > 0:
                        self.create_buy_exit()
                        self.create_buy_entry()
                    if self.pair.max_size_sell > 0:
                        self.create_sell_exit()
                        self.create_sell_entry()
                    time.sleep(1)

                if check_orders + 10 < time.time():
                    #STOP LOSS and STOP BOT 
                    self.get_position_unrpnl()
                    if self.unrealised_pnl_percent <= -self.pair.stop_loss/100:
                        self.session.cancel_all_active_orders(symbol=self.pair.symbol)
                        print("TIME TO STOP BOT!")
                        if 'Buy' in self.position_side:
                            if self.pair.max_size_buy > 0:
                                time.sleep(0.25)
                                self.create_buy_entry(order_type='Market', time_in_force='GoodTillCancel', side='Sell', reduce_only=True)
                        if 'Sell' in self.position_side:
                            if self.pair.max_size_sell > 0:
                                time.sleep(0.25)
                                self.create_sell_entry(order_type='Market', time_in_force='GoodTillCancel', side='Buy', reduce_only=True)
                        time.sleep(5)
                        break
                    try:
                        orders = self.session.get_active_order(symbol=self.pair.symbol)['result']['data']
                    except:
                        orders = []
                    buy_exit_found = False
                    sell_exit_found = False
                    for o in orders:
                        if o['order_status'] in ['New', 'PartiallyFilled'] and ( ('reduce_only' in o and o['reduce_only']) or o['time_in_force'] in ['GoodTillCancel','PostOnly'] ):
                            if o['side'] == 'Buy':
                                sell_exit_found = True
                            else:
                                buy_exit_found = True
                    if not sell_exit_found:
                        self.exit_sell_id = None
                    if not buy_exit_found:
                        self.exit_buy_id = None
                    if 'Sell' in self.position_side and self.position_sell_size > 0:
                        if self.pair.max_size_sell > 0:
                            self.create_sell_exit()
                    if 'Buy' in self.position_side and self.position_buy_size > 0:
                        if self.pair.max_size_buy > 0:
                            self.create_buy_exit()
                    if 'None' in self.position_side and self.position_buy_size == 0 and self.position_buy_order_margin == 0:
                        print("NO POSITION, NEED REPAIR")
                        self.need_to_repair = True
                    check_orders = time.time()

parser = argparse.ArgumentParser()
parser.add_argument("--ticker", type=str, required=False, help="trade ticker, example: 'BITUSD'", default='BITUSD')
parser.add_argument("--qty", type=float, required=False, help="qty, exapmle: 0.3", default=64)
parser.add_argument("--round_qty", type=int, required=False, help="round qty, example: 1", default=1)
parser.add_argument("--round_price", type=int, required=False, help="round price, example: 3", default=3)
parser.add_argument("--step", type=float, required=False, help="step to take profit, example: 0.001", default=0.002)
parser.add_argument("--modif", type=float, required=False, help="modif to average position, example: 0.01", default=0.0025)
parser.add_argument("--max_size_buy", type=float, required=False, help="max size buy position, example: 0.01", default=3700)
parser.add_argument("--max_size_sell", type=float, required=False, help="max size sell position, example: 0.01", default=0)
parser.add_argument("--trailing", type=bool, required=False, help="change price buy/sell position if current price very close to closing price, example: False", default=False)
parser.add_argument("--stop_loss", type=float, required=False, help="close the market position when the unrealized PnL percentage of the wallet balance reaches the specified number, example: 99.98", default=3.7)
args = parser.parse_args()
trader = Trader(TradingPair(args.ticker, args.qty, args.round_qty, args.round_price, args.step, args.modif, args.max_size_buy, args.max_size_sell, args.trailing, args.stop_loss), 'API-KEY', 'API-SECRET')
trader.run()