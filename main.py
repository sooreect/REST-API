from google.appengine.ext import ndb
import webapp2
import json
import datetime

class Boat(ndb.Model):
    id = ndb.StringProperty()
    name = ndb.StringProperty(required=True)
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()

class BoatHandler(webapp2.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        new_boat = Boat(name=data['name'], type=data['type'], length=data['length'], at_sea=True)
        new_boat.put()
        new_boat.id = new_boat.key.urlsafe()
        new_boat.put()  #persist the entity to Cloud Datastore
        new_boat_dict = new_boat.to_dict() #create and return a dictionary representation of a boat instance
        new_boat_dict['self'] = '/boats/' + new_boat.key.urlsafe()
        self.response.write(json.dumps(new_boat_dict))

    def get(self, id=None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            boat_dict = boat.to_dict()
            boat_dict['self'] = '/boats/' + id
            self.response.write(json.dumps(boat_dict))
        else: #if no id is provided, return all boats
            boat_dicts = [boat.to_dict() for boat in Boat.query()]  #retrieve all entities and convert to dictionaries
            for boat in boat_dicts: 
                boat['self'] = '/boats/' + str(boat['id'])
            self.response.write(json.dumps(boat_dicts))

    def put(self, id=None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            data = json.loads(self.request.body)
            edit = 0
            if 'name' in data.keys():
                if 'at_sea' in data.keys():
                    if boat.at_sea != data['at_sea']: #modify data if at_sea statuses do not match
                        if data['at_sea'] == True:   #if new status is at_sea, modify boat status and empty slip
                            boat.at_sea = True
                            occupied_slip = Slip.query(Slip.current_boat == boat.id).get()
                            occupied_slip.current_boat = None
                            occupied_slip.arrival_date = None
                            occupied_slip.put()
                            edit = 1
                        else:  #if new status is in slip, assign it the first slip available
                            empty_slip = Slip.query(Slip.current_boat == None).get()
                            if empty_slip: 
                                boat.at_sea = False
                                empty_slip.current_boat = boat.id
                                now = datetime.datetime.now()
                                empty_slip.arrival_date = now.strftime("%m/%d/%Y")
                                empty_slip.put()
                                self.response.write('Boat has arrived at Slip #' + str(empty_slip.number) + '\n\n')
                                edit = 1
                            else:
                                self.response.set_status(403)
                                self.response.write('ERROR: 403 - Forbidden\nBoat cannot arrive at a slip. All slips are occupied.\n')
                                return
                    else:
                        edit = 1
                else: #if at_sea status is not specified, replacement is at_sea by default
                    if boat.at_sea == False:
                        boat.at_sea = True
                        occupied_slip = Slip.query(Slip.current_boat == boat.id).get()
                        occupied_slip.current_boat = None
                        occupied_slip.arrival_date = None
                        occupied_slip.put()
                        edit = 1
                boat.name = data['name']
                edit = 1
                if 'type' in data.keys():
                    boat.type = data['type']
                    edit = 1
                else: 
                    boat.type = None
                if 'length' in data.keys():
                    boat.length = data['length']
                    edit = 1
                else:
                    boat.length = None
            else:
                self.response.set_status(403)
                self.response.write('ERROR: 403 - Forbidden\nName field cannot be empty.')
            if edit == 1:
                boat.put()
                boat_dict = boat.to_dict() 
                boat_dict['self'] = '/boats/' + boat.key.urlsafe()
                self.response.write(json.dumps(boat_dict))

    def patch(self, id=None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            data = json.loads(self.request.body)
            edit = 0
            if 'name' in data.keys():   #weed out invalid name
                if data['name'] is None:
                    self.response.set_status(403)
                    self.response.write('ERROR: 403 - Forbidden\nName field cannot be empty.')
                    return
            if 'at_sea' in data.keys():
                if boat.at_sea != data['at_sea']: #modify data if at_sea statuses do not match
                    if data['at_sea'] == True:   #if new status is at_sea, modify boat status and empty slip
                        boat.at_sea = True
                        occupied_slip = Slip.query(Slip.current_boat == boat.id).get()
                        if occupied_slip:
                            occupied_slip.current_boat = None
                            occupied_slip.arrival_date = None
                            occupied_slip.put()
                        edit = 1
                    else:  #if new status is in slip, assign it the first slip available
                        empty_slip = Slip.query(Slip.current_boat == None).get()
                        if empty_slip: 
                            boat.at_sea = False
                            empty_slip.current_boat = boat.id
                            now = datetime.datetime.now()
                            empty_slip.arrival_date = now.strftime("%m/%d/%Y")
                            empty_slip.put()
                            self.response.write('Boat has arrived at Slip #' + str(empty_slip.number) + '\n\n')
                            edit = 1
                        else:
                            self.response.set_status(403)
                            self.response.write('ERROR: 403 - Forbidden\nBoat cannot arrive at a slip. All slips are occupied.')
                            return
                else:
                    edit = 1
            if 'name' in data.keys():    
                boat.name = data['name']
                edit = 1
            if 'type' in data.keys():
                boat.type = data['type']
                edit = 1
            if 'length' in data.keys():
                boat.length = data['length']
                edit = 1
            if edit == 1:
                boat.put()
                boat_dict = boat.to_dict() 
                boat_dict['self'] = '/boats/' + boat.key.urlsafe()
                self.response.write(json.dumps(boat_dict))

    def delete(self, id=None):
        if id:
            boat = ndb.Key(urlsafe=id).get()
            if boat.at_sea == False:
                occupied_slip = Slip.query(Slip.current_boat == boat.id).get()
                occupied_slip.current_boat = None
                occupied_slip.arrival_date = None
                occupied_slip.put()
            boat.key.delete()
            self.response.write('Boat successfully deleted.')


class Slip(ndb.Model):
    id = ndb.StringProperty()
    number = ndb.IntegerProperty(required=True)
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()

class SlipHandler(webapp2.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        all_slips = Slip.query()
        for s in all_slips:
            if s.number == data['number']:
                self.response.set_status(403)
                self.response.write('ERROR: 403 - Forbidden\nSlip number is already taken.')
                return
        else:
            new_slip = Slip(number=data['number'], current_boat=None, arrival_date=None)
            new_slip.put()
            new_slip.id = new_slip.key.urlsafe()
            new_slip.put()
            slip_dict = new_slip.to_dict()
            slip_dict['self'] = '/slips/' + new_slip.key.urlsafe()
            self.response.write(json.dumps(slip_dict))

    def get(self, id=None):
        if id:
            slip = ndb.Key(urlsafe=id).get()
            slip_dict = slip.to_dict()
            slip_dict['self'] = '/slips/' + id
            self.response.write(json.dumps(slip_dict))
        else: 
            slip_dicts = [slip.to_dict() for slip in Slip.query()]  #retrieve all entities and convert to dictionaries
            for slip in slip_dicts: 
                slip['self'] = '/slips/' + str(slip['id'])
            self.response.write(json.dumps(slip_dicts))

    def put(self, id=None):
        if id:
            data = json.loads(self.request.body)
            slip = ndb.Key(urlsafe=id).get()
            valid_number = False
            valid_boat = False
            valid_date = False
            edit = 0
            if 'number' in data.keys(): #put only if number is provided
                if data['number'] is not None:  #edit only if number is not null
                    if slip.number != data['number']:   #replace only if number is different
                        all_slips = Slip.query()
                        for s in all_slips:
                            if s.number == data['number']:
                                self.response.set_status(403)
                                self.response.write('ERROR: 403 - Forbidden\nSlip number is already taken.')
                                return
                    valid_number = True
                else:   #number field is null
                    self.response.set_status(403)
                    self.response.write('ERROR: 403 - Forbidden\nNumber field cannot be empty.')
                    return
            else:   #no number provided
                self.response.set_status(403)
                self.response.write('ERROR: 403 - Forbidden\nNumber field cannot be empty.')
                return
            if 'current_boat' in data.keys():   #current_boat is provided 
                if data['current_boat'] is not None:    #if moving another boat into slip
                    if slip.current_boat == None:   #if slip is already empty
                        boat_with_id = Boat.query(Boat.id == data['current_boat']).get()    #check if boat id is valid
                        if boat_with_id: 
                            valid_boat = True   #allowed to move boat into slip
                        else:   #boat id is invalid
                            self.response.set_status(400)
                            self.response.write('ERROR: 400 - Bad Request\nInvalid boat ID')
                            return
                    else:   #slip is occupied
                        if slip.current_boat != data['current_boat']:
                            self.response.set_status(403)
                            self.response.write('ERROR: 403 - Forbidden\nBoat cannot arrive at slip. Slip is currently occupied.')
                            return
                else:   #user requests to empty slip
                    if slip.current_boat is not None:
                        valid_boat = True   #allowed to empty out slip
            else:   #no boat is provided, reset current_boat to none if slip is not already empty
                if slip.current_boat is not None:
                    valid_boat = True   #allowed to empty out slip
            if 'arrival_date' in data.keys():
                if 'current_boat' in data.keys():
                    if data['current_boat'] is not None:   #if there will be a boat in slip
                        valid_date = True
                    else: 
                        self.response.set_status(403)
                        self.response.write('ERROR: 403 - Forbidden\nCannot add an arrival date without a boat in slip.')        
                        return
                elif slip.current_boat is not None:   #if there is a boat in slip
                    valid_date = True
                else:   #if there is no boat
                    if data['arrival_date'] is not None:
                        self.response.set_status(403)
                        self.response.write('ERROR: 403 - Forbidden\nCannot add an arrival date without a boat in slip.')        
                        return
            else:
                valid_date = True
            if valid_number: 
                slip.number = data['number']
                edit = 1
            if valid_boat:
                if 'current_boat' not in data.keys():   #empty slip
                    if slip.current_boat is not None:
                        old_boat = Boat.query(Boat.id == slip.current_boat).get()
                        if old_boat:
                            old_boat.at_sea = True
                            old_boat.put()
                        slip.current_boat = None
                        edit = 1
                else:
                    if data['current_boat'] is None:    #empty slip
                        if slip.current_boat is not None:
                            old_boat = Boat.query(Boat.id == slip.current_boat).get()
                            if old_boat:
                                old_boat.at_sea = True
                                old_boat.put()
                            slip.current_boat = None
                            edit = 1
                    else:   #move boat to slip
                        former_slip = Slip.query(Slip.current_boat == boat_with_id.id).get()    #check if boat is in another slip
                        if former_slip: #empty old slip
                            former_slip.current_boat = None
                            former_slip.arrival_date = None
                            former_slip.put()
                        slip.current_boat = data['current_boat']    
                        boat_with_id.at_sea = False
                        boat_with_id.put()
                        self.response.write('Boat has arrived at Slip #' + str(slip.number) + '.\n\n')
                        edit = 1
            if valid_date:
                if 'arrival_date' not in data.keys():
                    if data['current_boat'] is None:
                        slip.arrival_date = None
                        edit = 1
                    else: 
                        now = datetime.datetime.now()
                        slip.arrival_date = now.strftime("%m/%d/%Y")
                else:
                    if slip.current_boat is not None:
                        slip.arrival_date = data['arrival_date']
                        edit = 1
            slip.put()
            if edit == 1:
                slip_dict = slip.to_dict() 
                slip_dict['self'] = '/slips/' + slip.key.urlsafe()
                self.response.write(json.dumps(slip_dict))

    def patch(self, id=None):
        if id:
            data = json.loads(self.request.body)
            slip = ndb.Key(urlsafe=id).get()
            valid_number = False
            valid_boat = False
            valid_date = False
            edit = 0
            if 'number' in data.keys(): 
                if slip.number != data['number']:
                    all_slips = Slip.query()
                    for s in all_slips:
                        if s.number == data['number']:
                            self.response.set_status(403)
                            self.response.write('ERROR: 403 - Forbidden\nSlip number is already taken.')
                            return
                valid_number = True
            if 'current_boat' in data.keys():
                if data['current_boat'] is not None:    #if not emptying slip
                    if slip.current_boat == None:   #if slip is already empty
                        boat_with_id = Boat.query(Boat.id == data['current_boat']).get()    #check if boat id is valid
                        if boat_with_id: 
                            valid_boat = True
                        else:   #boat id is invalid
                            self.response.set_status(400)
                            self.response.write('ERROR: 400 - Bad Request\nInvalid boat ID')
                            return
                    else:   #slip is occupied
                        if slip.current_boat != data['current_boat']:
                            self.response.set_status(403)
                            self.response.write('ERROR: 403 - Forbidden\nBoat cannot arrive at slip. Slip is currently occupied.')
                            return
                else:   #if emptying slip
                    if slip.current_boat is not None:
                        valid_boat = True
            if 'arrival_date' in data.keys():
                if 'current_boat' in data.keys():
                    if data['current_boat'] is not None:   #if there will be a boat in slip
                        valid_date = True
                    else: 
                        self.response.set_status(403)
                        self.response.write('ERROR: 403 - Forbidden\nCannot add an arrival date without a boat in slip.')        
                        return
                elif slip.current_boat is not None:   #if there is a boat in slip
                    valid_date = True
                else:   #if there is no boat
                    if data['arrival_date'] is not None:
                        self.response.set_status(403)
                        self.response.write('ERROR: 403 - Forbidden\nCannot add an arrival date without a boat in slip.')        
                        return
            if valid_number:
                slip.number = data['number']
                edit = 1
            if valid_boat:
                if data['current_boat'] is not None:    #if moving boat into sea
                    former_slip = Slip.query(Slip.current_boat == boat_with_id.id).get()    #check if boat is in another slip
                    if former_slip: #empty old slip
                        former_slip.current_boat = None
                        former_slip.arrival_date = None
                        former_slip.put()
                    slip.current_boat = data['current_boat']    
                    boat_with_id.at_sea = False
                    boat_with_id.put()
                    if 'arrival_date' not in data.keys(): #update arrival date
                        now = datetime.datetime.now()
                        slip.arrival_date = now.strftime("%m/%d/%Y")
                    self.response.write('Boat has arrived at Slip #' + str(slip.number) + '.\n\n')
                    edit = 1
                else:   #if emptying slip
                    old_boat = Boat.query(Boat.id == slip.current_boat).get()
                    if old_boat:
                        old_boat.at_sea = True
                        old_boat.put()
                        edit = 1
                    slip.current_boat = None
            if valid_date:
                if slip.current_boat is not None:
                    slip.arrival_date = data['arrival_date']
                    edit = 1
            slip.put()
            if edit == 1:
                slip_dict = slip.to_dict() 
                slip_dict['self'] = '/slips/' + slip.key.urlsafe()
                self.response.write(json.dumps(slip_dict))

    def delete(self, id=None):
        if id:
            slip = ndb.Key(urlsafe=id).get()
            if slip.current_boat is not None:
                boat = Boat.query(Boat.id == slip.current_boat).get()
                boat.at_sea = True
                boat.put()
            slip.key.delete()
            self.response.write('Slip successfully deleted.')


class SlipBoatHandler(webapp2.RequestHandler):
    def get(self, id=None):
        if id:
            slip = ndb.Key(urlsafe=id).get()
            if slip.current_boat is None:
                self.response.write('There is no boat in slip.')
            else:
                boat = Boat.query(Boat.id == slip.current_boat).get()
                boat_dict = boat.to_dict()
                boat_dict['self'] = '/boats/' + slip.current_boat
                self.response.write(json.dumps(boat_dict))

    def put(self, id=None):
        if id: 
            data = json.loads(self.request.body)
            slip = ndb.Key(urlsafe=id).get()
            valid_boat = False
            valid_date = False
            if 'current_boat' in data.keys():   #current_boat is provided 
                if data['current_boat'] is not None:    #if moving another boat into slip
                    if slip.current_boat == None:   #if slip is already empty
                        boat_with_id = Boat.query(Boat.id == data['current_boat']).get()    #check if boat id is valid
                        if boat_with_id: 
                            valid_boat = True   #allowed to move boat into slip
                        else:   #boat id is invalid
                            self.response.set_status(400)
                            self.response.write('ERROR: 400 - Bad Request\nInvalid boat ID')
                            return
                    else:   #slip is occupied
                        if slip.current_boat != data['current_boat']:
                            self.response.set_status(403)
                            self.response.write('ERROR: 403 - Forbidden\nBoat cannot arrive at slip. Slip is currently occupied.')
                            return
                else:   #user requests to empty slip
                    if slip.current_boat is not None:
                        valid_boat = True   #allowed to empty out slip
            else:   #no boat is provided, reset current_boat to none if slip is not already empty
                if slip.current_boat is not None:
                    valid_boat = True   #allowed to empty out slip
            if 'arrival_date' in data.keys():
                if 'current_boat' in data.keys():
                    if data['current_boat'] is not None:   #if there will be a boat in slip
                        valid_date = True
                    else: 
                        if data['arrival_date'] is not None:
                            self.response.set_status(403)
                            self.response.write('ERROR: 403 - Forbidden\nCannot add an arrival date without a boat in slip.')        
                            return
                elif slip.current_boat is not None:   #if there is a boat in slip
                    valid_date = True
                else:   #if there is no boat
                    if data['arrival_date'] is not None:
                        self.response.set_status(403)
                        self.response.write('ERROR: 403 - Forbidden\nCannot add an arrival date without a boat in slip.')        
                        return
            else:
                valid_date = True
            if valid_boat:
                if 'current_boat' not in data.keys():   #empty slip
                    if slip.current_boat is not None:
                        old_boat = Boat.query(Boat.id == slip.current_boat).get()
                        if old_boat:
                            old_boat.at_sea = True
                            old_boat.put()
                        slip.current_boat = None
                        edit = 1
                else:
                    if data['current_boat'] is None:    #empty slip
                        if slip.current_boat is not None:
                            old_boat = Boat.query(Boat.id == slip.current_boat).get()
                            if old_boat:
                                old_boat.at_sea = True
                                old_boat.put()
                            slip.current_boat = None
                            edit = 1
                    else:   #move boat to slip
                        former_slip = Slip.query(Slip.current_boat == boat_with_id.id).get()    #check if boat is in another slip
                        if former_slip: #empty old slip
                            former_slip.current_boat = None
                            former_slip.arrival_date = None
                            former_slip.put()
                        slip.current_boat = data['current_boat']    
                        boat_with_id.at_sea = False
                        boat_with_id.put()
                        self.response.write('Boat has arrived at Slip #' + str(slip.number) + '.\n\n')
                        edit = 1
            if valid_date:
                if 'arrival_date' not in data.keys():
                    if data['current_boat'] is None:
                        slip.arrival_date = None
                        edit = 1
                    else: 
                        now = datetime.datetime.now()
                        slip.arrival_date = now.strftime("%m/%d/%Y")
                else:
                    if slip.current_boat is not None:
                        slip.arrival_date = data['arrival_date']
                        edit = 1
            slip.put()
            if slip.current_boat is None:
                self.response.write('There is no boat in slip.')
            else:
                boat = Boat.query(Boat.id == slip.current_boat).get()
                boat_dict = boat.to_dict()
                boat_dict['self'] = '/boats/' + slip.current_boat
                self.response.write(json.dumps(boat_dict))

    def patch(self, id=None):
        if id: 
            data = json.loads(self.request.body)
            slip = ndb.Key(urlsafe=id).get()
            if 'current_boat' in data.keys():
                if slip.current_boat is None:   #slip is empty
                    if data['current_boat'] is not None:
                        boat_with_id = Boat.query(Boat.id == data['current_boat']).get()
                        if boat_with_id:    #valid boat id, move boat to slip
                            if boat_with_id.at_sea == False:    #if boat is already in a different slip
                                former_slip = Slip.query(Slip.current_boat == boat_with_id.id).get()
                                former_slip.current_boat = None
                                former_slip.arrival_date = None
                                former_slip.put()
                                boat_with_id.at_sea = True
                                boat_with_id.put()
                            slip.current_boat = data['current_boat']
                            if 'arrival_date' not in data.keys():
                                now = datetime.datetime.now()
                                slip.arrival_date = now.strftime("%m/%d/%Y")
                                #slip.arrival_date = data['arrival_date']
                            boat_with_id.at_sea = False
                            boat_with_id.put()
                        else:   #invalid boat id
                            self.response.set_status(400)
                            self.response.write('ERROR: 400 - Bad Request\nInvalid boat ID')
                            return
                else:   #slip already occupied
                    if data['current_boat'] is None:    #empty slip
                        old_boat = Boat.query(Boat.id == slip.current_boat).get()
                        old_boat.at_sea = True
                        old_boat.put()
                        slip.current_boat = None
                        slip.arrival_date = None
                    else:   #403 error if not the same boat
                        if slip.current_boat != data['current_boat']:
                            self.response.set_status(403)
                            self.response.write('ERROR: 403 - Forbidden\nBoat cannot arrive at slip. Slip is currently occupied.\n\n')
            if 'arrival_date' in data.keys():
                if slip.current_boat is not None:
                    slip.arrival_date = data['arrival_date']
                else:
                    if data['arrival_date'] is not None:
                        self.response.set_status(403)
                        self.response.write('ERROR: 403 - Forbidden\nCannot add an arrival date without a boat in slip.\n\n')
                        return
            slip.put()
            if slip.current_boat is None:
                self.response.write('There is no boat in slip.')
            else:
                boat = Boat.query(Boat.id == slip.current_boat).get()
                boat_dict = boat.to_dict()
                boat_dict['self'] = '/boats/' + slip.current_boat
                self.response.write(json.dumps(boat_dict))

    def delete(self, id=None):  
        if id:
            slip = ndb.Key(urlsafe=id).get()
            if slip.current_boat is not None:
                boat = ndb.Key(urlsafe=slip.current_boat).get()
                boat.key.delete()
                self.response.write('Boat successfully deleted.\n')
            slip.current_boat = None
            slip.arrival_date = None
            slip.put()
            self.response.write('There is no boat in slip.')


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write("Hello, Marina!")
        

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boats', BoatHandler), 
    ('/boats/(.*)', BoatHandler),
    ('/slips', SlipHandler), 
    ('/slips/(.*)/boat', SlipBoatHandler), 
    ('/slips/(.*)', SlipHandler)
], debug=True)
