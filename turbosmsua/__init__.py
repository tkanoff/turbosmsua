# -*- coding: utf-8 -*-
from suds.client import Client
import threading


class Turbosms:
    username = None
    password = None

    reauth_after = None

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = Client('http://turbosms.in.ua/api/wsdl.html')

        self.reauth_after = 120

        # Do auth
        self.authenticate()

    def authenticate(self):
        """
        Currently the 'auth session' at Turbosms drops after
        an undefined time span. 
        The code below will try to ensure the session is
        by requesting the 'auth session' again.
        """

        auth_result = self.client.service.Auth(
            self.username, self.password
        ).encode('utf8')
        
        # Some debug
        print "TurboSMS authentication attempt"
        
        if auth_result != "Вы успешно авторизировались":
            raise ValueError("Auth error: %s" % auth_result)

        # Do daemonize for more control
        t_timer = threading.Timer(self.reauth_after, self.authenticate)
        t_timer.daemon = True
        t_timer.start()

    def balance(self):
        balance_result = self.client.service.GetCreditBalance().encode('utf8')

        try:
            balance = float(balance_result)
        except ValueError:
            raise ValueError("Balance error: %s" % balance_result)

        return balance

    def send_text(self, sender, destinations, text, wappush=False):
        if not type(destinations) is list:
            destinations = [destinations]

        def format_destination(d):
            d = str(d)
            if len(d) == 9:
                return "+380%s" % d
            if len(d) == 10:
                return "+38%s" % d
            if len(d) == 11:
                return "+3%s" % d
            if len(d) == 12:
                return "+%s" % d
            if len(d) == 13:
                return d
            raise Exception("Invalid destination: %s" % d)

        destinations_formated = ",".join(map(format_destination, destinations))

        if not wappush:
            send_result = self.client.service.SendSMS(
                sender,
                destinations_formated,
                text.decode('utf8')
            ).ResultArray
        else:
            send_result = self.client.service.SendSMS(
                sender,
                destinations_formated,
                text.decode('utf8'),
                wappush
            ).ResultArray

        send_status = send_result.pop(0).encode('utf8')

        to_return = {"status": send_status}
        for i, sms_id in enumerate(send_result):
            to_return[destinations[i]] = sms_id

        return to_return

    def message_status(self, message_id):
        status = self.client.service.GetMessageStatus(message_id)
        return status.encode('utf8')
