import webapp2


class Hello(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello world!')

app = webapp2.WSGIApplication([('/', Hello)], debug=True)