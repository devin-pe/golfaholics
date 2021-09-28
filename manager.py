from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
import pyrebase
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import darkblue, black
from reportlab.lib.pagesizes import landscape, A4


# Defining our different screens


class WindowManager(ScreenManager):
    pass


class MainWindow(Screen):
    pass


class CreateGameWindow(Screen):
    pass


class AddRegularWindow(Screen):
    pass


class AddGuestWindow(Screen):
    pass


class PdfMenuWindow(Screen):
    pass


class CreateGamePopup(Popup):
    pass


class UpdatePopup(Popup):
    pass


class AddPlayerPopup(Popup):
    pass

# Defining useful functions


def create_username(fullname):
    """String: fullname, the entered name of the player to be added to the DB
    Returns the created username from first three letters of first name and last three of surname"""
    username = fullname[:3].lower()
    i = len(fullname) - 1
    last_space_found = False
    while i > 0 and not last_space_found:
        if fullname[i] == ' ':
            username = username + fullname[i + 1:i + 4].lower()
            last_space_found = True
        i -= 1
    return username


def password_is_valid(password):
    """String: password, the entered password
    Returns True if the user entered the correct password, False otherwise"""
    if password == 'golf':
        return True
    else:
        return False


def fullname_is_valid(fullname):
    """String: fullname, the entered name of the player to be added to the DB
    Returns True the fullname contains alphabetic characters only and if there is at least one space
    Return False otherwise"""
    start = 0
    end = 0
    new_fullname = ''
    for char in fullname:
        if char == ' ':
            new_fullname = new_fullname + fullname[start:end]
            if end + 1 < len(fullname):
                start = end + 1
        end += 1
    new_fullname = new_fullname + fullname[start:end]
    if new_fullname.isalpha():
        return True
    else:
        return False


def handicap_is_valid(handicap):
    """String: handicap, the entered handicap
        Returns True if valid and false otherwise"""
    count = 0
    for i in range(len(handicap)):
        if handicap[0] == '-':
            count = 1
        elif handicap[i].isdigit() or handicap[i] == '.':
            count += 1
    if count == len(handicap) and count != 0:
        return True
    else:
        return False


def week_num_is_valid(week_num):
    """String: week_num, the entered week_num
        Returns True if valid and false otherwise"""
    if week_num.isdigit():
        if 1 <= int(week_num) <= 20:
            return True
    return False


def year_is_valid(year):
    """String: year, the entered year
    Returns True if valid and false otherwise"""
    if year.isdigit():
        if 2021 <= int(year) <= 2121:
            return True
    return False


def calc_points(hcp, par, hole_index, h_score):
    """int: hcp, the player's HCP
    int: par, the par of the hole
    int: hole_index, the hole index
    int: h_score, the number of strokes the player made on the hole
    Returns the number of points the player obtained on the hole"""
    points = 0
    if hcp >= hole_index:
        if par == 4:
            if h_score - 1 == 0:
                points = 6
            elif h_score - 1 == 1:
                points = 5
            elif h_score - 1 == 2:
                points = 4
            elif h_score - 1 == 3:
                points = 3
            elif h_score - 1 == 4:
                points = 2
            elif h_score - 1 == 5:
                points = 1
            else:
                pass

    elif hcp == 19 and (hole_index == 1 or hole_index == 2):  # i.e. 9.5 for 9 holes
        if par == 4:
            if h_score - 2 == -1:
                points = 7
            elif h_score - 2 == 0:
                points = 6
            elif h_score - 2 == 0:
                points = 5
            elif h_score - 2 == 1:
                points = 4
            elif h_score - 2 == 2:
                points = 3
            elif h_score - 2 == 3:
                points = 2
            elif h_score - 2 == 4:
                points = 1
            else:
                pass

    else:
        if par == 4:
            if h_score == 1:
                points = 5
            elif h_score == 2:
                points = 4
            elif h_score == 3:
                points = 3
            elif h_score == 4:
                points = 2
            elif h_score == 5:
                points = 1
            else:
                pass
    return points


def det_cut(hcp):
    """int: hcp, the player's HCP
    Returns the amount to be cut from the current HCP"""
    if -36 <= hcp <= 3.4:
        return 0.2
    elif 3.5 <= hcp <= 7.4:
        return 0.3
    elif 7.5 <= hcp <= 10.4:
        return 0.4
    elif 10.5 <= hcp <= 36:
        return 0.4
    else:
        raise Exception('Handicap falls outside of valid range')


def calc_new_hcp(hcp, points, std_scratch):
    """int: hcp, the player's HCP
    int: points, the number of points the player obtained in the game
    int: std_scratch, the standard scratch of the game
    Return handicap from scores obtained from the mobile app"""
    if points > std_scratch:
        difference = points - std_scratch
        if -36 <= hcp <= 3.4:
            hcp -= difference * det_cut(hcp)
        elif 3.5 <= hcp <= 7.4:
            while difference > 0:
                hcp -= det_cut(hcp)
                difference -= 1
        elif 7.5 <= hcp <= 10.4:
            while difference > 0:
                hcp -= det_cut(hcp)
                difference -= 1
        elif 10.5 <= hcp <= 36:
            while difference > 0:
                hcp -= det_cut(hcp)
                difference -= 1
        else:
            raise Exception('Handicap falls outside of valid range')
    elif points < std_scratch:
        hcp = hcp + 0.2
    return hcp


def compute_total_money(money_dic):
    """Dict: money_dic a dictionary containing the player's name and position in the game as a key and the money as a val
    Returns a dictionary with the name of the player as a key and the total money from all games in the season
    as a value"""
    total_dic = {}
    for name in money_dic:
        total = 0
        if len(money_dic[name]) >= 9:
            for i in range(9):  # take top 9 money
                total += money_dic[name][i]
        else:
            for i in range(len(money_dic[name])):  # take top len(money_dic[name]) money
                total += money_dic[name][i]
        total_dic[name] = total
    return total_dic


def get_games_played(money_dic):
    """
    Dict: money_dic a dictionary containing the player's name and position in the game as a key and the money as a val
    Returns a dic containing the name of the player as a key and the number of games played
    as a value."""
    played_dic = {}
    for name in money_dic:
        played_dic[name] = len(money_dic[name])
    return played_dic


def get_top_three_dic(total_score_dic):
    """Dict: total_score_dic containing the player names as keys and the lists of total strokes over par as values
    Returns a dictionary containing the player names as keys and the a list with the top 3 lowest totals over par as values"""
    top_three_dic = {}
    for name in total_score_dic:
        total_score_dic[name].sort()
        if len(total_score_dic[name]) >= 3:
            top_three_dic[name] = total_score_dic[name][:3]
        else:
            top_three_dic[name] = total_score_dic[name][:]
    return top_three_dic


def calc_total_of_top_three(top_three_dic):
    """Dict: top_three_dic containing the player names as keys and the lists with the top 3 lowest totals over par as values
    Returns a dictionary containing player names as keys and the total of the top 3 lowest totals over par as values"""
    total_dic = {}
    for name in top_three_dic:
        total = 0
        for i in range(len(top_three_dic[name])):
            total += top_three_dic[name][i]
        total_dic[name] = total
    return total_dic

# Defining our app


class DesktopApp(App):

    def __init__(self):
        super().__init__()
        self.kv = Builder.load_file('manager.kv')
        self.on_regular_screen = False
        self.on_guest_screen = False
        self.on_create_game_screen = False
        self.on_pdf_menu_screen = False
        self.par_is_selected = False
        self.handicap_is_selected = False
        # Initializing attributes for create_game
        self.course = StringProperty('')
        self.options = StringProperty('')
        self.game_num = -1
        self.week_num = -1
        self.year = -1
        # Initializing attributes for add_regular and add_guest
        self.fullname = StringProperty('')
        self.username = StringProperty('')
        self.handicap = StringProperty('')
        # Initializing attributes for create_pdfs
        self.points_dic = {}
        self.total_dic = {}
        self.std_scratch = -1
        self.rank_list = []
        self.pos_list = []
        self.points_list = []
        self.last_six_list = []
        self.last_three_list = []
        self.last_two_list = []
        self.last_list = []
        config = {
            'apiKey': "AIzaSyAY031Y_qNLOTZG6x8C9ZtkQ7amCtt9770",
            'authDomain': "gscore-tracker-74250.firebaseapp.com",
            'databaseURL': "https://gscore-tracker-74250-default-rtdb.europe-west1.firebasedatabase.app/",
            'projectId': "gscore-tracker-74250",
            'storageBucket': "gscore-tracker-74250.appspot.com",
            'messagingSenderId': "1019989080117",
            'appId': "1:1019989080117:web:c6ee96395b0237efb1d97c",
            'measurementId': "G-9J1F1KTV4W"

        }
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()

    def create_game(self):
        """Updates the DB with new game info on the click of the confirm button on the create_game screen"""
        password = self.kv.get_screen('create_game').ids.password.text
        self.course = self.kv.get_screen('create_game').ids.course_menu.text
        week_num = self.kv.get_screen('create_game').ids.week_num.text
        year = self.kv.get_screen('create_game').ids.year.text
        try:
            self.options = self.kv.get_screen('create_game').ids.options.text
            if password_is_valid(password) and self.course != 'Choose a course' and self.options != 'Choose hole options':
                self.game_num = self.find_game_num()
                if week_num_is_valid(week_num) and year_is_valid(year):
                    self.week_num = int(week_num)
                    self.year = int(year)
                    self.db.child('games').child('game{0}'.format(self.game_num)).set({'week{0}'.format(self.week_num): self.year})
                    self.db.child('games').child('game{0}'.format(self.game_num)).update({self.course: self.options})
                    popup = CreateGamePopup()
                    popup.open()
        except:
            pass
        self.reset_create_screen()

    def find_game_num(self):
        num_list = []
        for game in dict(self.db.child('games').get().val()).keys():
            num_list.append(int(game[4:]))
        return max(num_list) + 1

    def create_spinner1(self):
        """Returns the 1st type of spinner for if Kikuoka, Longwy Amneville, Baden Hills, Bitburg or Grand Ducal
        are selected"""
        spinner = Spinner(text='Choose hole options',
                          values=('Full 18', 'Front 9', 'Back 9'),
                          size_hint=(None, None),
                          size=(self.root.width/2, self.root.height/18),
                          pos_hint={'center_x': 0.5, 'top': 0.65}
                          )
        return spinner

    def create_spinner2(self):
        """Returns the 2nd type of spinner for if Presich is selected"""
        spinner = Spinner(text='Choose hole options',
                          values=('France', 'Germany', 'Luxembourg'),
                          size_hint=(None, None),
                          size=(self.root.width/2, self.root.height/18),
                          pos_hint={'center_x': 0.5, 'top': 0.65}
                          )
        return spinner

    def create_spinner3(self):
        """Returns the 3rd type of spinner for if Belenhaff is selected"""
        spinner = Spinner(text='Choose hole options',
                          values=('Full 18', 'Front 9'),
                          size_hint=(None, None),
                          size=(self.root.width / 2, self.root.height / 18),
                          pos_hint={'center_x': 0.5, 'top': 0.65}
                          )
        return spinner

    def make_hole_options(self):
        """Removes the placeholder spinner and adds a new spinner based on the course_menu selection."""
        self.kv.get_screen('create_game').ids.game_layout.remove_widget(self.kv.get_screen('create_game').ids.options_menu)
        if self.kv.get_screen('create_game').ids.course_menu.text == 'Choose a course':
            pass
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Kikuoka':
            spinner = self.create_spinner1()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Longwy':
            spinner = self.create_spinner2()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Preisch':
            spinner = self.create_spinner2()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Grand Ducal':
            spinner = self.create_spinner1()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Amneville':
            spinner = self.create_spinner1()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Baden Hills':
            spinner = self.create_spinner1()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Bitburg':
            spinner = self.create_spinner1()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        elif self.kv.get_screen('create_game').ids.course_menu.text == 'Belenhaff':
            spinner = self.create_spinner3()
            self.kv.get_screen('create_game').ids.game_layout.add_widget(spinner)
            self.kv.get_screen('create_game').ids['options'] = spinner
        else:
            raise Exception('Course menu text error')

    def add_user(self):
        """Adds a new regular or guest to the DB"""
        if self.on_regular_screen:
            # Set local variables that will be used if the user is adding a regular
            screen_name = 'add_regular'
            category = 'regulars'
            self.on_regular_screen = False

        elif self.on_guest_screen:
            # Set local variables that will be used if the user is adding a guest
            screen_name = 'add_guest'
            category = 'guests'
            self.on_guest_screen = False
        else:
            raise Exception('Error with the boolean attributes that control screen selection!')
        self.fullname = self.kv.get_screen(screen_name).ids.username.text
        self.handicap = self.kv.get_screen(screen_name).ids.handicap.text
        if password_is_valid(self.kv.get_screen(screen_name).ids.password.text) and fullname_is_valid(self.fullname) and handicap_is_valid(self.handicap):

            self.username = create_username(self.fullname)
            dic = {self.username: self.fullname + self.handicap}  # Create the dictionary to be added to the DB
            # Erase text inputs
            self.kv.get_screen(screen_name).ids.username.text = ''
            self.kv.get_screen(screen_name).ids.password.text = ''
            self.kv.get_screen(screen_name).ids.handicap.text = ''
            self.db.child(category).update(dic)  # Add the regular or guest to the DB
            # Open popup screen
            popup = AddPlayerPopup()
            popup.open()

    def return_to_main(self):
        """Resets fields and sends user to main screen."""
        if self.on_regular_screen:
            screen_name = 'add_regular'
            self.kv.get_screen(screen_name).ids.username.text = ''
            self.kv.get_screen(screen_name).ids.password.text = ''
            self.on_regular_screen = False
        elif self.on_guest_screen:
            screen_name = 'add_guest'
            self.kv.get_screen(screen_name).ids.username.text = ''
            self.kv.get_screen(screen_name).ids.password.text = ''
            self.on_guest_screen = False
        elif self.on_create_game_screen:
            self.reset_create_screen()
        elif self.on_pdf_menu_screen:
            self.on_pdf_menu_screen = False
        else:
            raise Exception('Error with the boolean attributes that control screen selection!')

        self.root.current = 'main'

    def do_hcp_computations(self, player_dic, hcp_dic, game_num, c):
        """Dict: player_dic, containing the entries in the DB for each player
        Dict: hcp_dic, containing the usernames of all users as keys and HCPs as values
        Combines all the necessary computations to calculate the HCPs"""
        for username in player_dic.keys():  # for each username in the player_dic
            for hcp_key in hcp_dic.keys():  # for each username in the hcp_dic
                if username == hcp_key:
                    hcp = hcp_dic[username]
                    points_list = []
                    if c == 1:
                        for hole_num in range(1, len(player_dic[username])):
                            par = self.get_hole_par(hole_num, game_num)
                            hole_index = self.get_hole_index(hole_num, game_num)
                            h_score = self.get_player_score(hole_num, game_num, username)
                            points = calc_points(hcp, par, hole_index, h_score)
                            points_list.append(points)
                        self.points_dic[username] = points_list
                        break  # to stop loop from continuing once username is found
                    else:
                        for hole_num in range(1, len(player_dic[username]) - 1):
                            par = self.get_hole_par(hole_num, game_num)
                            hole_index = self.get_hole_index(hole_num, game_num)
                            h_score = self.get_player_score(hole_num, game_num, username)
                            points = calc_points(hcp, par, hole_index, h_score)
                            points_list.append(points)
                        self.points_dic[username] = points_list
                        break  # to stop loop from continuing once username is found

    def extract_and_calc_points_hcp(self, t):
        """Updates the HCPs in the DB
        String: t, the type (either 'regulars' or 'guests')"""
        game_num = self.get_latest_game_num()
        player_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).get().val())
        hcp_dic = self.get_old_hcp_dic(t)

        self.do_hcp_computations(player_dic, hcp_dic, game_num, 2)

        new_hcp_dic = self.create_new_hcp_dic(t)
        hcp_dic_from_db = dict(self.db.child('{0}'.format(t)).get().val())
        for username in new_hcp_dic:
            for hcp_key in hcp_dic_from_db:
                if username == hcp_key:
                    i = len(hcp_dic_from_db[username]) - 1
                    handicap_found = False
                    while i >= 0 and not handicap_found:
                        if hcp_dic_from_db[username][i] == '-':
                            hcp_dic_from_db[username] = hcp_dic_from_db[username].replace(hcp_dic_from_db[username][i:],
                                                                                          str(new_hcp_dic[username]))
                            handicap_found = True
                        elif hcp_dic_from_db[username][i].isdigit and hcp_dic_from_db[username][i - 1].isalpha():
                            hcp_dic_from_db[username] = hcp_dic_from_db[username].replace(hcp_dic_from_db[username][i:],
                                                                                          str(new_hcp_dic[username]))
                            handicap_found = True
                        i -= 1
        if 'game_num' not in player_dic.keys():
            player_dic['game_num'] = game_num
            self.db.child('games').child('game{0}'.format(game_num)).set(player_dic)
            self.db.child('{0}'.format(t)).set(hcp_dic_from_db)
        elif 'n_players' not in player_dic.keys():
            player_dic['n_players'] = len(player_dic) - 3
            self.db.child('games').child('game{0}'.format(game_num)).set(player_dic)
            self.db.child('{0}'.format(t)).set(hcp_dic_from_db)

    def set_std_scratch(self):
        """Sets the std_scratch of the game"""
        game_num = self.get_latest_game_num()
        player_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).get().val())
        hcp_dic = self.get_old_hcp_dic('regulars')
        hcp_dic.update(self.get_old_hcp_dic('guests'))

        self.do_hcp_computations(player_dic, hcp_dic, game_num, 1)  # Calculates points

        self.std_scratch = self.calc_std_scratch()

    def get_std_scratch(self):
        """Returns the std_scratch of the game"""
        return self.std_scratch

    def create_new_hcp_dic(self, t):
        """Returns a dictionary with the player's usernames as keys and their new handicaps as values
        String: t, the type (either 'regulars' or 'guests')"""
        old_hcp_dic = self.get_old_hcp_dic(t)
        new_hcp_dic = {}
        for username in self.points_dic.keys():
            for hcp_key in old_hcp_dic.keys():
                if hcp_key == username:
                    total_points = self.calc_last_x_points(username, 1, len(self.points_dic[username]))
                    new_hcp_dic[username] = round(calc_new_hcp(old_hcp_dic[username], total_points, self.std_scratch), 1)
        return new_hcp_dic

    def get_name_dic_for_pdf(self):
        """Returns a dictionary containing player names as keys and points list as values"""
        new_dic = {}
        db_dic = dict(self.db.child('regulars').get().val())
        db_dic.update(dict(self.db.child('guests').get().val()))
        for username in self.points_dic:
            for key in db_dic:
                if username == key:
                    i = len(db_dic[username]) - 1
                    handicap_found = False
                    while i >= 0 and not handicap_found:
                        if db_dic[username][i] == '-':
                            name = db_dic[username][:i]
                            new_dic[name] = username
                            handicap_found = True
                        elif db_dic[username][i].isdigit and db_dic[username][i-1].isalpha():
                            name = db_dic[username][:i]
                            new_dic[name] = username
                            handicap_found = True
                        i -= 1
        return new_dic

    def calc_last_x_points(self, username, start, end):
        """String: username the username of the player
        int: start the starting hole
        int: the end boundary for the holes
        Calculates the total points on the last x holes for a player."""
        total_points = 0
        for key in self.points_dic.keys():
            if key == username:
                for hole_num in range(start, end):  # variable start and end points to be used to calculate last6, etc
                    total_points += self.points_dic[username][hole_num]
                break  # break outer loop once username is found
        return total_points

    def calc_std_scratch(self):
        """Calculates the standard scratch of the game"""
        total_points = 0
        total_players = 0
        for username in self.points_dic.keys():
            total_players += 1
            for hole_num in range(1, len(self.points_dic[username])):
                total_points += self.points_dic[username][hole_num]
        return round(total_points/total_players) + 2

    def get_latest_game_num(self):
        """Returns the most recent game number, the one we use to update the db and create pdfs"""
        num_list = []
        for game in dict(self.db.child('games').get().val()).keys():
            num_list.append(int(game[4:]))
        return max(num_list)

    def get_hole_index(self, hole_num, game_num):
        """int: hole_num the number of the hole
        int: game_num the game number
        Returns the hole_index (hole_hcp) of the specific hole"""
        game_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).get().val())
        for key in game_dic.keys():
            if key == 'Preisch' or key == 'Longwy' or key == 'Grand Ducal' or key == 'Kikuoka' or key == 'Amneville' or key == 'Baden Hills' or key == 'Belenhaff' or key == 'Bitburg':
                course_name = key
                hole_options = game_dic[key]
                course_dic = dict(self.db.child('courses').child(course_name).child(hole_options).get().val())
                for k in course_dic.keys():
                    if k[0] == str(hole_num) and k[1] == 'h':  # 1st char is hole_num, after that it's either par or hcp
                        return course_dic[k]
                    elif k[0:2] == str(hole_num) and k[2] == 'h':  # 1st and 2nd chars are hole_num, after that it's either par or hcp
                        return course_dic[k]

    def get_hole_par(self, hole_num, game_num):
        """int: hole_num the number of the hole
        int: game_num the game number
        Returns the par of the specific hole"""
        game_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).get().val())
        for key in game_dic.keys():
            if key == 'Preisch' or key == 'Longwy' or key == 'Grand Ducal' or key == 'Kikuoka' or key == 'Amneville' or key == 'Baden Hills' or key == 'Belenhaff' or key == 'Bitburg':
                course_name = key
                hole_options = game_dic[key]
                course_dic = dict(self.db.child('courses').child(course_name).child(hole_options).get().val())
                for k in course_dic.keys():
                    if k[0] == str(hole_num) and k[1] == 'p':  # 1st char is hole_num, after that it's either par or hcp
                        return course_dic[k]
                    elif k[0:2] == str(hole_num) and k[2] == 'p':  # 1st and 2nd chars are hole_num, after that it's either par or hcp
                        return course_dic[k]

    def get_player_score(self, hole_num, game_num, username):
        """int: hole_num the number of the hole
        int: game_num the game number
        String: username the username of the player
        Returns the player's score on a specific hole"""
        player_score_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).child(username).get().val())
        for key in player_score_dic.keys():
            if key[1] == str(hole_num):  # 2nd char in the entry stored in the DB is the number
                return player_score_dic[key]
            elif key[1:3] == str(hole_num):  # 2nd and 3rd chars in the entry stored in the DB is the number
                return player_score_dic[key]

    def get_old_hcp_dic_for_pdf(self):
        """Returns a dict containing the player names as keys and old HCPs as values
        String: t, the type (either 'regulars' or 'guests')"""
        dic = {}
        db_dic = dict(self.db.child('regulars').get().val())
        db_dic.update(dict(self.db.child('guests').get().val()))
        for value in db_dic.values():
            i = len(value) - 1
            handicap_found = False
            while i >= 0 and not handicap_found:
                if value[i] == '-':
                    name = value[:i]
                    handicap = float(value[i:])
                    dic[name] = handicap
                    handicap_found = True
                elif value[i].isdigit and value[i - 1].isalpha():
                    name = value[:i]
                    handicap = float(value[i:])
                    dic[name] = handicap
                    handicap_found = True
                i -= 1
        return dic

    def get_old_hcp_dic(self, t):
        """Returns a dict containing the players' usernames as keys and old HCPs as values
        String: t, the type (either 'regulars' or 'guests')"""
        dic = {}
        db_dic = dict(self.db.child('{0}'.format(t)).get().val())
        for key in db_dic.keys():
            i = len(db_dic[key]) - 1
            handicap_found = False
            while i >= 0 and not handicap_found:
                if db_dic[key][i] == '-':
                    handicap = float(db_dic[key][i:])
                    dic[key] = handicap
                    handicap_found = True
                elif db_dic[key][i].isdigit and db_dic[key][i - 1].isalpha():
                    handicap = float(db_dic[key][i:])
                    dic[key] = handicap
                    handicap_found = True
                i -= 1
        return dic

    def get_course_and_hole_opt(self):
        """Returns a list containing the course name and hole options of the game"""
        course_and_hole_opt = []
        game_num = self.get_latest_game_num()
        db_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).get().val())
        for key in db_dic.keys():
            if key == 'Grand Ducal' or key == 'Kikuoka' or key == 'Preisch' or key == 'Longwy' \
                    or 'Amneville' or 'Baden Hills' or 'Belenhaff' or 'Bitburg' :
                course_and_hole_opt.append(key)
                course_and_hole_opt.append(db_dic[key])
                return course_and_hole_opt

    def get_week_num(self):
        """Returns the week number of the game"""
        game_num = self.get_latest_game_num()
        db_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).get().val())
        for key in db_dic.keys():
            if key[:4] == 'week':
                return key[4:]

    def get_year(self):
        """Returns the year of the game"""
        game_num = self.get_latest_game_num()
        db_dic = dict(self.db.child('games').child('game{0}'.format(game_num)).get().val())
        for key in db_dic.keys():
            if key[:4] == 'week':
                return db_dic[key]

    def get_new_hcp_dic(self, t):
        """Returns the new guest dic with updated HCPs as values and full names as keys
        String: t, the type (either 'regulars' or 'guests')"""
        self.extract_and_calc_points_hcp('{0}'.format(t))
        new_dic = {}
        for value in dict(self.db.child('{0}'.format(t)).get().val()).values():
            i = len(value) - 1
            handicap_found = False
            while i >= 0 and not handicap_found:
                if value[i] == '-':
                    name = value[:i]
                    handicap = float(value[i:])
                    new_dic[name] = handicap
                    handicap_found = True
                elif value[i].isdigit and value[i - 1].isalpha():
                    name = value[:i]
                    handicap = float(value[i:])
                    new_dic[name] = handicap
                    handicap_found = True
                i -= 1
        return new_dic

    def create_points_lists(self, name_dic, player_hcp_dic):
        """Dict: name_dic containing the player names as keys and usernames as values
        Dict: player_hcp_dic containing the player's names as keys and HCPs as values
        Creates the parameters necessary for the set_ranking_list method"""
        for name in player_hcp_dic:
            for key in name_dic:
                if name == key:
                    self.rank_list.append(name)
                    self.points_list.append(self.calc_last_x_points(name_dic[name], 0, 9))
                    self.last_six_list.append(self.calc_last_x_points(name_dic[name], 3, 9))
                    self.last_three_list.append(self.calc_last_x_points(name_dic[name], 6, 9))
                    self.last_two_list.append(self.calc_last_x_points(name_dic[name], 7, 9))
                    self.last_list.append(self.calc_last_x_points(name_dic[name], 8, 9))

    def create_count_update_points(self, points_list, pos_list, c):
        """Helper function for self.set_pos_list
        Updates points list with the points of the remaining positions, those not in self.pos_list
        Returns a copy of the relevant attribute point list"""
        if c == 1:
            i = 0
            while i < len(pos_list):
                points_list.append(self.points_list[pos_list[i]])
                i += 1
            return self.points_list[:]
        elif c == 2:
            i = 0
            while i < len(pos_list):
                points_list.append(self.last_six_list[pos_list[i]])
                i += 1
            return self.last_six_list[:]
        elif c == 3:
            i = 0
            while i < len(pos_list):
                points_list.append(self.last_three_list[pos_list[i]])
                i += 1
            return self.last_three_list[:]
        elif c == 4:
            i = 0
            while i < len(pos_list):
                points_list.append(self.last_two_list[pos_list[i]])
                i += 1
            return self.last_two_list[:]
        else:
            i = 0
            while i < len(pos_list):
                points_list.append(self.last_list[pos_list[i]])
                i += 1
            return self.last_list[:]

    def create_max(self, points_list, count_list, pos_list):
        """Helper function for self.set_pos_list
        Returns a list containing all positions of the max value"""
        max_pos_list = []
        m = max(points_list)
        i = 0
        start = 0
        # Find all maxes and add their positions to max_pos_list
        while i < len(count_list):
            if count_list[i] == m:
                index = count_list.index(m, start)
                start = index + 1
                if index not in self.pos_list and index in pos_list:
                    max_pos_list.append(index)
            i += 1
        return max_pos_list

    def set_pos_list(self, pos_list, c):
        """Returns an ordered list of positions based off of points, last6, last3, last2 and finally last1"""
        if len(self.pos_list) == len(self.rank_list):
            return self.pos_list  # end condition
        points_list = []
        count_list = self.create_count_update_points(points_list, pos_list, c)
        max_pos_list = self.create_max(points_list, count_list, pos_list)
        if len(max_pos_list) == 1 or c == 0:
            self.pos_list.append(max_pos_list[0])
            rem_indices = []
            x = 0
            while x < len(count_list):
                if x not in self.pos_list:
                    rem_indices.append(x)
                x += 1
            return self.set_pos_list(rem_indices, 1)
        else:
            c += 1
            if c == 2:
                return self.set_pos_list(max_pos_list, c)
            elif c == 3:
                return self.set_pos_list(max_pos_list, c)
            elif c == 4:
                return self.set_pos_list(max_pos_list, c)
            elif c == 5:
                c = 0
                return self.set_pos_list(max_pos_list, c)

    def order_lists(self):
        """Orders the relevant lists"""
        temp_rank_list = self.rank_list[:]
        temp_points_list = self.points_list[:]
        for i in range(len(self.rank_list)):
            temp_rank_list[self.pos_list[i]] = self.rank_list[i]
            temp_points_list[self.pos_list[i]] = self.points_list[i]
        self.rank_list = temp_rank_list[:]
        self.points_list = temp_points_list[:]

    def create_points_dic(self):
        """Helper function for self.calc_money
        Returns dictionary with points as keys and n of occurrences in self.points_list as values"""
        points_dic = {}
        for i in self.points_list:
            if i not in points_dic:
                points_dic[i] = 1
            else:
                points_dic[i] += 1
        return points_dic

    def calc_money(self):
        """Calculates the money for each player in the game and returns it in a dictionary.
        Returns the position as part of the key"""
        points_dic = self.create_points_dic()
        money_dic = {}
        money = 200000
        j = 0
        pos = 1
        while j < len(self.points_list) and money > 0:
            n = points_dic[self.points_list[j]]
            total_money = money
            for k in range(j, j + n - 1):
                money -= 4000
                total_money += money
            for x in range(j, j + n):
                key = '{0}{1}'.format(self.rank_list[x], pos)
                money_dic[key] = total_money/n
            money -= 4000
            j += n
            pos += 1
        return money_dic

    def update_player_dic(self, money_dic, name_dic):
        """Dict: money_dic a dictionary containing the player's name and position in the game as a key and the money as a val
        Dict: name_dic containing the player names as keys and usernames as values
        Updates the user's section in the game DB with the position as a key and the money as a value."""
        game_num = self.get_latest_game_num()
        for key in money_dic:
            i = len(key) - 1
            pos_found = False
            while i >= 0 and not pos_found:
                if key[i].isdigit and key[i - 1].isalpha():
                    name_key = key[:i]
                    pos = key[i:]
                    pos_found = True
                    for name in name_dic:
                        if name_key == name:
                            self.db.child('games').child('game{0}'.format(game_num)).child(name_dic[name]).update({'pos{0}'.format(pos): money_dic[key]})
                i -= 1

    def pos_is_set(self):
        """Helper function that determines whether the position and money entry has been added to the DB.
        This is used to avoid creating the pdfs again."""
        game_num = self.get_latest_game_num()
        player_dic = self.db.child('games').child('game{0}'.format(game_num)).get().val()
        for username in player_dic:
            if len(username) == 6:  # len == 6 means its actually a username not a course name or week num
                player_score_dic = self.db.child('games').child('game{0}'.format(game_num)).child(username).get().val()
                for key in player_score_dic:
                    if key[:3] == 'pos':
                        return True
        return False

    def get_money(self, username, game_num):
        """String: username, the player's username
        int: game_num, the game number
        Returns the money from the DB"""
        player_score_dic = self.db.child('games').child('game{0}'.format(game_num)).child(username).get().val()
        for key in player_score_dic:
            if key[:3] == 'pos':
                return player_score_dic[key]

    def find_top_nine_money(self):
        """Returns an ordered list containing the top 9 rewards from the season."""
        name_dic = self.get_name_dic_for_pdf()
        latest_game_num = self.get_latest_game_num()
        week_num = int(self.get_week_num())
        money_dic = {}
        game_num = latest_game_num
        while game_num > latest_game_num - week_num:
            player_dic = self.db.child('games').child('game{0}'.format(game_num)).get().val()
            for entry in player_dic:
                for name in name_dic:
                    if entry == name_dic[name]:
                        money = self.get_money(name_dic[name], game_num)
                        if name in money_dic:
                            money_dic[name].append(money)
                        else:
                            money_dic[name] = [money]
            game_num -= 1
        for name in money_dic:
            money_dic[name].sort(reverse=True)
        return money_dic

    def return_score_dic(self):
        """Updates self.total_dic with names as keys and total strokes as values
        Returns a dic with names as keys and score list as values."""
        name_dic = self.get_name_dic_for_pdf()
        game_num = self.get_latest_game_num()
        player_dic = self.db.child('games').child('game{0}'.format(game_num)).get().val()
        score_dic = {}
        for username in player_dic:
            for name in name_dic:
                if username == name_dic[name]:
                    score_dic[name] = []
                    total = 0
                    for hole_num in range(1, len(player_dic[username]) - 1):  # -1 to remove the pos entry
                        score = self.get_player_score(hole_num, game_num, username)
                        if score == 0:
                            score = 99
                        score_dic[name].append(score)
                        total += score
                    self.total_dic[name] = total
        return score_dic

    def get_strokes_over_par(self, h_score, hole_num, game_num):
        """int: h_score, the player's score on the hole
        int: hole_num, the hole number
        int: game_num, the game number
        Returns the number of strokes the user has shot over par"""
        return h_score - self.get_hole_par(hole_num, game_num)

    def get_total_score_dic(self, name_dic):
        """Dict: name_dic containing the player names as keys and usernames as values
        Finds the top 3 games where the player has shot the least over par
        Or top 1 or 2 if the player has played less than three games
        Returns a dic with the name as a key and the list containing the top 3 as values"""
        total_score_dic = {}
        latest_game_num = self.get_latest_game_num()
        week_num = int(self.get_week_num())
        game_num = latest_game_num
        while game_num > latest_game_num - week_num:
            player_dic = self.db.child('games').child('game{0}'.format(game_num)).get().val()
            for entry in player_dic:
                for name in name_dic:
                    if entry == name_dic[name]:
                        total = 0
                        user_dic = self.db.child('games').child('game{0}'.format(game_num)).child(entry).get().val()
                        for hole_num in range(1, len(user_dic) - 1):
                            score = self.get_player_score(hole_num, game_num, entry)
                            if score == 0:
                                strokes_over_par = 99
                            else:
                                strokes_over_par = self.get_strokes_over_par(score, hole_num, game_num)
                            total += strokes_over_par
                        if name in total_score_dic:
                            total_score_dic[name].append(total)
                        else:
                            total_score_dic[name] = [total]
            game_num -= 1
        return total_score_dic

    def create_weekly_report(self, name_dic, hcp_dic, week_num, year):
        """Creates the weekly report pdf"""
        self.create_points_lists(name_dic, hcp_dic)
        self.set_pos_list([x for x in range(len(self.points_list))], 1)
        self.order_lists()
        course_and_hole_opt = self.get_course_and_hole_opt()
        std_scratch = self.get_std_scratch()
        # Open canvas
        weekly_report = Canvas('weekly-results-report-week{0}-{1}.pdf'.format(week_num, year), bottomup=0)

        # Consistent formatting
        weekly_report.line(2 * cm, 2.5 * cm, 19 * cm, 2.5 * cm)
        weekly_report.line(2 * cm, 5.5 * cm, 19 * cm, 5.5 * cm)
        weekly_report.line(2 * cm, 7 * cm, 19 * cm, 7 * cm)
        weekly_report.setFont('Times-Italic', 30)
        weekly_report.setFillColor(darkblue)
        weekly_report.drawString(2 * cm, 2 * cm, 'Week Results Full Report')
        weekly_report.setFont('Times-Italic', 22)
        weekly_report.drawString(2 * cm, 3.5 * cm, 'Course')
        weekly_report.drawString(2 * cm, 5 * cm, 'Year')
        weekly_report.drawString(8 * cm, 5 * cm, 'Week')
        weekly_report.drawString(14 * cm, 5 * cm, 'Std Scratch')
        weekly_report.setFont('Times-Italic', 18)
        weekly_report.drawString(2 * cm, 6.5 * cm, 'Surname')
        weekly_report.drawString(4.5 * cm, 6.5 * cm, 'Name')
        weekly_report.drawString(6.5 * cm, 6.5 * cm, 'HCP')
        weekly_report.drawString(8.5 * cm, 6.5 * cm, 'Points')
        weekly_report.drawString(11 * cm, 6.5 * cm, 'Last6')
        weekly_report.drawString(13.25 * cm, 6.5 * cm, 'Last3')
        weekly_report.drawString(15.5 * cm, 6.5 * cm, 'Last2')
        weekly_report.drawString(17.75 * cm, 6.5 * cm, 'Last')

        weekly_report.setFillColor(black)
        weekly_report.setFont('Times-Roman', 25)
        weekly_report.drawString(6 * cm, 3.5 * cm, '{0} - {1}'.format(course_and_hole_opt[0], course_and_hole_opt[1]))  # Course name and options
        weekly_report.setFont('Times-Roman', 22)
        weekly_report.drawString(4 * cm, 5 * cm, '{0}'.format(year))  # Year
        weekly_report.drawString(10 * cm, 5 * cm, '{0}'.format(week_num))  # Week number
        weekly_report.drawString(18 * cm, 5 * cm, '{0}'.format(std_scratch))  # Standard scratch

        y = 8.0
        weekly_report.setFont('Times-Roman', 15)
        for name in self.rank_list:
            points = self.calc_last_x_points(name_dic[name], 0, 9)
            last_six = self.calc_last_x_points(name_dic[name], 3, 9)
            last_three = self.calc_last_x_points(name_dic[name], 6, 9)
            last_two = self.calc_last_x_points(name_dic[name], 7, 9)
            last = self.calc_last_x_points(name_dic[name], 8, 9)
            if y > 28:
                weekly_report.showPage()
                # Consistent formatting
                weekly_report.line(2 * cm, 2.5 * cm, 19 * cm, 2.5 * cm)
                weekly_report.setFillColor(darkblue)
                weekly_report.setFont('Times-Italic', 18)
                weekly_report.drawString(2 * cm, 2 * cm, 'Surname')
                weekly_report.drawString(4.5 * cm, 2 * cm, 'Name')
                weekly_report.drawString(6.5 * cm, 2 * cm, 'HCP')
                weekly_report.drawString(8.5 * cm, 2 * cm, 'Points')
                weekly_report.drawString(11 * cm, 2 * cm, 'Last6')
                weekly_report.drawString(13.25 * cm, 2 * cm, 'Last3')
                weekly_report.drawString(15.5 * cm, 2 * cm, 'Last2')
                weekly_report.drawString(17.75 * cm, 2 * cm, 'Last')
                weekly_report.setFillColor(black)
                weekly_report.setFont('Times-Roman', 15)
                y = 3.5
            i = 0
            space_found = False
            surname = ''
            first_name = ''
            while i <= len(name) and not space_found:
                if name[i] == ' ':
                    first_name = name[:i]
                    surname = name[i + 1:]
                    space_found = True
                i += 1
            weekly_report.drawString(2 * cm, y * cm, surname)
            weekly_report.drawString(4.5 * cm, y * cm, first_name)
            weekly_report.drawString(6.75 * cm, y * cm, str(hcp_dic[name]))  # Handicap
            weekly_report.drawString(8.95 * cm, y * cm, '{0}'.format(points))
            weekly_report.drawString(11.15 * cm, y * cm, '{0}'.format(last_six))
            weekly_report.drawString(13.35 * cm, y * cm, '{0}'.format(last_three))
            weekly_report.drawString(15.55 * cm, y * cm, '{0}'.format(last_two))
            weekly_report.drawString(17.75 * cm, y * cm, '{0}'.format(last))
            y += 0.7

        # Save pdf
        weekly_report.save()

    def create_money_report(self, name_dic, hcp_dic, money_dic, week_num, year):
        """Creates the money report pdf"""
        # Open canvas
        money_report = Canvas('money-report-week{0}-{1}.pdf'.format(week_num, year), bottomup=0)

        # Consistent formatting
        money_report.line(2 * cm, 3.5 * cm, 19 * cm, 3.5 * cm)
        money_report.line(2 * cm, 5 * cm, 19 * cm, 5 * cm)
        money_report.setFont('Times-Italic', 30)
        money_report.setFillColor(darkblue)
        money_report.drawString(2 * cm, 2 * cm, 'The Money Report')
        money_report.setFont('Times-Italic', 15)
        money_report.drawString(13 * cm, 2 * cm, 'Year')
        money_report.drawString(13 * cm, 3 * cm, 'Week')
        money_report.drawString(2 * cm, 4.5 * cm, 'Money')
        money_report.drawString(3.75 * cm, 4.5 * cm, 'Pos')
        money_report.drawString(5 * cm, 4.5 * cm, 'Surname')
        money_report.drawString(7.25 * cm, 4.5 * cm, 'Name')
        money_report.drawString(9 * cm, 4.5 * cm, 'HCP')
        money_report.drawString(10.5 * cm, 4.5 * cm, 'Points')
        money_report.drawString(12.5 * cm, 4.5 * cm, 'Last6')
        money_report.drawString(14.25 * cm, 4.5 * cm, 'Last3')
        money_report.drawString(16 * cm, 4.5 * cm, 'Last2')
        money_report.drawString(17.75 * cm, 4.5 * cm, 'Last')

        # Variable text
        money_report.setFillColor(black)
        money_report.setFont('Times-Roman', 15)
        money_report.drawString(15 * cm, 2 * cm, '{0}'.format(year))
        money_report.drawString(15 * cm, 3 * cm, '{0}'.format(week_num))

        money_report.setFont('Times-Roman', 12)
        y = 6
        for fullname in self.rank_list:
            for key in money_dic:
                if y > 28:
                    money_report.showPage()
                    # Consistent formatting
                    money_report.line(2 * cm, 2.5 * cm, 19 * cm, 2.5 * cm)
                    money_report.setFont('Times-Italic', 15)
                    money_report.drawString(2 * cm, 2 * cm, 'Money')
                    money_report.drawString(3.75 * cm, 2 * cm, 'Pos')
                    money_report.drawString(5 * cm, 2 * cm, 'Surname')
                    money_report.drawString(7.25 * cm, 2 * cm, 'Name')
                    money_report.drawString(9 * cm, 2 * cm, 'HCP')
                    money_report.drawString(10.5 * cm, 2 * cm, 'Points')
                    money_report.drawString(12.5 * cm, 2 * cm, 'Last6')
                    money_report.drawString(14.25 * cm, 2 * cm, 'Last3')
                    money_report.drawString(16 * cm, 2 * cm, 'Last2')
                    money_report.drawString(17.75 * cm, 2 * cm, 'Last')
                    y = 3.5
                i = len(key) - 1
                pos_found = False
                while i >= 0 and not pos_found:
                    if key[i].isdigit and key[i - 1].isalpha():
                        name_key = key[:i]
                        pos = key[i:]
                        pos_found = True
                        if name_key == fullname:
                            points = self.calc_last_x_points(name_dic[fullname], 0, 9)
                            last_six = self.calc_last_x_points(name_dic[fullname], 3, 9)
                            last_three = self.calc_last_x_points(name_dic[fullname], 6, 9)
                            last_two = self.calc_last_x_points(name_dic[fullname], 7, 9)
                            last = self.calc_last_x_points(name_dic[fullname], 8, 9)
                            j = 0
                            space_found = False
                            surname = ''
                            first_name = ''
                            while j <= len(fullname) and not space_found:
                                if fullname[j] == ' ':
                                    first_name = fullname[:j]
                                    surname = fullname[j + 1:]
                                    space_found = True
                                j += 1
                            money_report.drawString(2 * cm, y * cm, '£{0}'.format(money_dic[key]))
                            money_report.drawString(4.25 * cm, y * cm, '{0}'.format(pos))
                            money_report.drawString(5 * cm, y * cm, surname)
                            money_report.drawString(7.25 * cm, y * cm, first_name)
                            money_report.drawString(9.5 * cm, y * cm, '{0}'.format(hcp_dic[fullname]))
                            money_report.drawString(11 * cm, y * cm, '{0}'.format(points))
                            money_report.drawString(13 * cm, y * cm, '{0}'.format(last_six))
                            money_report.drawString(14.75 * cm, y * cm, '{0}'.format(last_three))
                            money_report.drawString(16.5 * cm, y * cm, '{0}'.format(last_two))
                            money_report.drawString(18.25 * cm, y * cm, '{0}'.format(last))
                            y += 0.7
                        i -= 1

        # Save pdf
        money_report.save()

    def create_best_brut_report(self, hcp_dic, week_num, year):
        """Creates the best brut report pdf"""
        score_dic = self.return_score_dic()
        course_and_hole_opt = self.get_course_and_hole_opt()
        # Create pdf
        best_brut_report = Canvas('best-brut-report-{0}-{1}.pdf'.format(week_num, year), bottomup=0)

        # Consistent text
        best_brut_report.line(2 * cm, 4.5 * cm, 19 * cm, 4.5 * cm)
        best_brut_report.setFont('Times-Italic', 30)
        best_brut_report.setFillColor(darkblue)
        best_brut_report.drawString(2 * cm, 2 * cm, 'Best Brut')
        best_brut_report.drawString(9 * cm, 2 * cm, 'Year')
        best_brut_report.drawString(15 * cm, 2 * cm, 'Week')
        best_brut_report.setFont('Times-Italic', 18)
        best_brut_report.drawString(2 * cm, 4 * cm, 'HCP')
        best_brut_report.drawString(4 * cm, 4 * cm, 'Surname')
        best_brut_report.drawString(7 * cm, 4 * cm, 'Name')
        best_brut_report.drawString(9 * cm, 4 * cm, 'Course Name')
        best_brut_report.drawString(13 * cm, 4 * cm, '1')
        best_brut_report.drawString(13.5 * cm, 4 * cm, '2')
        best_brut_report.drawString(14 * cm, 4 * cm, '3')
        best_brut_report.drawString(14.5 * cm, 4 * cm, '4')
        best_brut_report.drawString(15 * cm, 4 * cm, '5')
        best_brut_report.drawString(15.5 * cm, 4 * cm, '6')
        best_brut_report.drawString(16 * cm, 4 * cm, '7')
        best_brut_report.drawString(16.5 * cm, 4 * cm, '8')
        best_brut_report.drawString(17 * cm, 4 * cm, '9')
        best_brut_report.drawString(18 * cm, 4 * cm, 'Total')

        # Variable text
        best_brut_report.setFont('Times-Roman', 25)
        best_brut_report.drawString(11.5 * cm, 2 * cm, '2021')
        best_brut_report.drawString(18 * cm, 2 * cm, '4')
        best_brut_report.setFillColor(black)
        best_brut_report.setFont('Times-Roman', 12)
        y = 5.5
        for name in score_dic:
            for i in range(len(self.rank_list)):
                if name == self.rank_list[i]:
                    if y > 28.7:
                        best_brut_report.showPage()
                        best_brut_report.line(2 * cm, 2.5 * cm, 19 * cm, 2.5 * cm)
                        best_brut_report.setFillColor(darkblue)
                        best_brut_report.setFont('Times-Italic', 18)
                        best_brut_report.drawString(2 * cm, 2 * cm, 'HCP')
                        best_brut_report.drawString(3.75 * cm, 4 * cm, 'Surname')
                        best_brut_report.drawString(6.5 * cm, 4 * cm, 'Name')
                        best_brut_report.drawString(8.75 * cm, 4 * cm, 'Course Name')
                        best_brut_report.drawString(13 * cm, 4 * cm, '1')
                        best_brut_report.drawString(13.5 * cm, 4 * cm, '2')
                        best_brut_report.drawString(14 * cm, 4 * cm, '3')
                        best_brut_report.drawString(14.5 * cm, 4 * cm, '4')
                        best_brut_report.drawString(15 * cm, 4 * cm, '5')
                        best_brut_report.drawString(15.5 * cm, 4 * cm, '6')
                        best_brut_report.drawString(16 * cm, 4 * cm, '7')
                        best_brut_report.drawString(16.5 * cm, 4 * cm, '8')
                        best_brut_report.drawString(17 * cm, 4 * cm, '9')
                        best_brut_report.drawString(18 * cm, 4 * cm, 'Total')
                        best_brut_report.setFillColor(black)
                        best_brut_report.setFont('Times-Roman', 12)
                        y = 3.5
                    j = 0
                    space_found = False
                    surname = ''
                    first_name = ''
                    while j <= len(name) and not space_found:
                        if name[j] == ' ':
                            first_name = name[:j]
                            surname = name[j + 1:]
                            space_found = True
                        j += 1
                    best_brut_report.drawString(2 * cm, y * cm, '{0}'.format(hcp_dic[name]))
                    best_brut_report.drawString(3.75 * cm, y * cm, surname)
                    best_brut_report.drawString(6.25 * cm, y * cm, first_name)
                    best_brut_report.drawString(8.75 * cm, y * cm, '{0} - {1}'.format(course_and_hole_opt[0], course_and_hole_opt[1]))
                    best_brut_report.drawString(13 * cm, y * cm, '{0}'.format(score_dic[name][0]))
                    best_brut_report.drawString(13.5 * cm, y * cm, '{0}'.format(score_dic[name][1]))
                    best_brut_report.drawString(14 * cm, y * cm, '{0}'.format(score_dic[name][2]))
                    best_brut_report.drawString(14.5 * cm, y * cm, '{0}'.format(score_dic[name][3]))
                    best_brut_report.drawString(15 * cm, y * cm, '{0}'.format(score_dic[name][4]))
                    best_brut_report.drawString(15.5 * cm, y * cm, '{0}'.format(score_dic[name][5]))
                    best_brut_report.drawString(16 * cm, y * cm, '{0}'.format(score_dic[name][6]))
                    best_brut_report.drawString(16.5 * cm, y * cm, '{0}'.format(score_dic[name][7]))
                    best_brut_report.drawString(17 * cm, y * cm, '{0}'.format(score_dic[name][8]))
                    best_brut_report.drawString(18 * cm, y * cm, '{0}'.format(self.total_dic[name]))
                    y += 0.7
        # Save pdf
        best_brut_report.save()

    def create_best_nine_report(self, week_num, year):
        """Creates the best 9 report pdf"""
        money_dic = self.find_top_nine_money()
        total_dic = compute_total_money(money_dic)
        played_dic = get_games_played(money_dic)

        # Create pdf
        best_nine_report = Canvas('best-9-report-week{0}-{1}.pdf'.format(week_num, year), pagesize=landscape(A4), bottomup=0)

        # Consistent formatting
        best_nine_report.line(2 * cm, 4 * cm, 28 * cm, 4 * cm)
        best_nine_report.setFont('Times-Italic', 30)
        best_nine_report.setFillColor(darkblue)
        best_nine_report.drawString(12 * cm, 2 * cm, 'Best 9 Report')
        best_nine_report.setFont('Times-Italic', 18)
        best_nine_report.drawString(3 * cm, 3.5 * cm, 'Played')
        best_nine_report.drawString(4.75 * cm, 3.5 * cm, 'Total')
        best_nine_report.drawString(7.5 * cm, 3.5 * cm, 'Surname')
        best_nine_report.drawString(10.5 * cm, 3.5 * cm, 'Name')
        best_nine_report.drawString(13 * cm, 3.5 * cm, '1')
        best_nine_report.drawString(14.75 * cm, 3.5 * cm, '2')
        best_nine_report.drawString(16.5 * cm, 3.5 * cm, '3')
        best_nine_report.drawString(18.25 * cm, 3.5 * cm, '4')
        best_nine_report.drawString(20 * cm, 3.5 * cm, '5')
        best_nine_report.drawString(21.75 * cm, 3.5 * cm, '6')
        best_nine_report.drawString(23.5 * cm, 3.5 * cm, '7')
        best_nine_report.drawString(25.25 * cm, 3.5 * cm, '8')
        best_nine_report.drawString(27 * cm, 3.5 * cm, '9')

        # Variable formatting
        best_nine_report.setFillColor(black)
        best_nine_report.setFont('Times-Roman', 11)

        y = 5
        for name in list(total_dic):
            values = total_dic.values()
            m = max(values)
            if total_dic[name] == m:
                if y > 19:
                    best_nine_report.showPage()
                    # Consistent formatting
                    best_nine_report.line(2 * cm, 2.5 * cm, 28 * cm, 2.5 * cm)
                    best_nine_report.setFillColor(darkblue)
                    best_nine_report.setFont('Times-Italic', 18)
                    best_nine_report.drawString(2 * cm, 2 * cm, 'Played')
                    best_nine_report.drawString(5 * cm, 2 * cm, 'Total')
                    best_nine_report.drawString(7.5 * cm, 2 * cm, 'Surname')
                    best_nine_report.drawString(10.5 * cm, 2 * cm, 'Name')
                    best_nine_report.drawString(13 * cm, 2 * cm, '1')
                    best_nine_report.drawString(14.75 * cm, 2 * cm, '2')
                    best_nine_report.drawString(16.5 * cm, 2 * cm, '3')
                    best_nine_report.drawString(18.25 * cm, 2 * cm, '4')
                    best_nine_report.drawString(20 * cm, 2 * cm, '5')
                    best_nine_report.drawString(21.75 * cm, 2 * cm, '6')
                    best_nine_report.drawString(23.5 * cm, 2 * cm, '7')
                    best_nine_report.drawString(25.25 * cm, 2 * cm, '8')
                    best_nine_report.drawString(27 * cm, 2 * cm, '9')
                    best_nine_report.setFillColor(black)
                    best_nine_report.setFont('Times-Roman', 10)
                    y = 3.5
                j = 0
                space_found = False
                surname = ''
                first_name = ''
                while j <= len(name) and not space_found:
                    if name[j] == ' ':
                        first_name = name[:j]
                        surname = name[j + 1:]
                        space_found = True
                    j += 1
                # Variable text
                best_nine_report.drawString(3 * cm, y * cm, '{0}'.format(played_dic[name]))
                best_nine_report.drawString(4.75 * cm, y * cm, '£{0}'.format(total_dic[name]))
                best_nine_report.drawString(7.5 * cm, y * cm, surname)
                best_nine_report.drawString(10.5 * cm, y * cm, first_name)
                best_nine_report.drawString(12.5 * cm, y * cm, '£{0}'.format(money_dic[name][0]))
                if len(money_dic[name]) > 1:
                    best_nine_report.drawString(14.25 * cm, y * cm, '£{0}'.format(money_dic[name][1]))
                if len(money_dic[name]) > 2:
                    best_nine_report.drawString(16 * cm, y * cm, '£{0}'.format(money_dic[name][2]))
                if len(money_dic[name]) > 3:
                    best_nine_report.drawString(17.75 * cm, y * cm, '£{0}'.format(money_dic[name][3]))
                if len(money_dic[name]) > 4:
                    best_nine_report.drawString(19.5 * cm, y * cm, '£{0}'.format(money_dic[name][4]))
                if len(money_dic[name]) > 5:
                    best_nine_report.drawString(21.25 * cm, y * cm, '£{0}'.format(money_dic[name][5]))
                if len(money_dic[name]) > 6:
                    best_nine_report.drawString(23 * cm, y * cm, '£{0}'.format(money_dic[name][6]))
                if len(money_dic[name]) > 7:
                    best_nine_report.drawString(24.75 * cm, y * cm, '£{0}'.format(money_dic[name][7]))
                if len(money_dic[name]) > 8:
                    best_nine_report.drawString(26.5 * cm, y * cm, '£{0}'.format(money_dic[name][8]))
                # Remove from dictionaries
                total_dic.pop(name)
                money_dic.pop(name)
                played_dic.pop(name)
                y += 0.7
        # Save pdf
        best_nine_report.save()

    def create_best_three_brut_rep(self, name_dic, week_num, year):
        """Creates the best 3 brut report pdf"""
        top_three_dic = get_top_three_dic(self.get_total_score_dic(name_dic))
        total_dic = calc_total_of_top_three(top_three_dic)
        # Create pdf
        best_three_report = Canvas('best-3-brut-report-week{0}-{1}.pdf'.format(week_num, year), bottomup=0)

        # Consistent formatting
        best_three_report.line(2 * cm, 4.5 * cm, 19 * cm, 4.5 * cm)
        best_three_report.setFont('Times-Italic', 25)
        best_three_report.setFillColor(darkblue)
        best_three_report.drawString(7 * cm, 2 * cm, 'Best 3 Brut Scores')
        best_three_report.setFont('Times-Italic', 16)
        best_three_report.drawString(2 * cm, 3.5 * cm, 'Total')
        best_three_report.drawString(2 * cm, 4 * cm, 'over par')
        best_three_report.drawString(5 * cm, 4 * cm, 'Surname')
        best_three_report.drawString(8 * cm, 4 * cm, 'Name')
        best_three_report.drawString(10 * cm, 4 * cm, 'Best Result')
        best_three_report.drawString(14 * cm, 3.5 * cm, '2nd best')
        best_three_report.drawString(14 * cm, 4 * cm, 'result')
        best_three_report.drawString(17 * cm, 3.5 * cm, '3rd best')
        best_three_report.drawString(17 * cm, 4 * cm, 'result')

        # Variable text

        best_three_report.setFillColor(black)
        best_three_report.setFont('Times-Roman', 13)
        y = 5.5
        for name in top_three_dic:
            if y > 28.7:
                best_three_report.showPage()
                # Consistent formatting
                best_three_report.line(2 * cm, 3 * cm, 3 * cm, 3 * cm)
                best_three_report.setFont('Times-Italic', 16)
                best_three_report.setFillColor(darkblue)
                best_three_report.drawString(2 * cm, 2 * cm, 'Total')
                best_three_report.drawString(2 * cm, 2.5 * cm, 'over par')
                best_three_report.drawString(5 * cm, 2.5 * cm, 'Surname')
                best_three_report.drawString(8 * cm, 2.5 * cm, 'Name')
                best_three_report.drawString(10 * cm, 2.5 * cm, 'Best Result')
                best_three_report.drawString(14 * cm, 2 * cm, '2nd best')
                best_three_report.drawString(14 * cm, 2.5 * cm, 'result')
                best_three_report.drawString(17 * cm, 2 * cm, '3rd best')
                best_three_report.drawString(17 * cm, 2.5 * cm, 'result')
                best_three_report.setFillColor(black)
                best_three_report.setFont('Times-Roman', 13)
                y = 3.5
            j = 0
            space_found = False
            surname = ''
            first_name = ''
            while j <= len(name) and not space_found:
                if name[j] == ' ':
                    first_name = name[:j]
                    surname = name[j + 1:]
                    space_found = True
                j += 1
            # Variable text
            best_three_report.drawString(2 * cm, y * cm, '{0}'.format(total_dic[name]))
            best_three_report.drawString(5 * cm, y * cm, surname)
            best_three_report.drawString(8 * cm, y * cm, first_name)
            best_three_report.drawString(11 * cm, y * cm, '{0}'.format(top_three_dic[name][0]))
            if len(top_three_dic[name]) >= 2:
                best_three_report.drawString(14 * cm, y * cm, '{0}'.format(top_three_dic[name][1]))
            if len(top_three_dic[name]) >= 3:
                best_three_report.drawString(17 * cm, y * cm, '{0}'.format(top_three_dic[name][2]))
            y += 0.7
        # Save pdf
        best_three_report.save()

    def create_reg_hcp_rep(self, week_num, year):
        """Creates the regular handicap report pdf"""
        reg_dic = self.get_new_hcp_dic('regulars')

        # Create pdf
        reg_handicap_report = Canvas('regular-handicap-report-week{0}-{1}.pdf'.format(week_num, year), bottomup=0)

        # Consistent formatting
        reg_handicap_report.line(2 * cm, 4 * cm, 19 * cm, 4 * cm)
        reg_handicap_report.setFont('Times-Italic', 25)
        reg_handicap_report.setFillColor(darkblue)
        reg_handicap_report.drawString(5 * cm, 2 * cm, 'Latest Regular Handicap Report')
        reg_handicap_report.setFont('Times-Italic', 18)
        reg_handicap_report.drawString(2 * cm, 3.5 * cm, 'Surname')
        reg_handicap_report.drawString(6 * cm, 3.5 * cm, 'Name')
        reg_handicap_report.drawString(14 * cm, 3.5 * cm, 'Handicap')

        # Variable text
        reg_handicap_report.setFillColor(black)
        reg_handicap_report.setFont('Times-Roman', 15)

        y = 5
        for key in reg_dic:
            if y > 28:
                reg_handicap_report.showPage()
                # Consistent formatting
                reg_handicap_report.line(2 * cm, 2.5 * cm, 19 * cm, 2.5 * cm)
                reg_handicap_report.setFillColor(darkblue)
                reg_handicap_report.setFont('Times-Italic', 18)
                reg_handicap_report.drawString(2 * cm, 2 * cm, 'Surname')
                reg_handicap_report.drawString(6 * cm, 2 * cm, 'Name')
                reg_handicap_report.drawString(14 * cm, 32 * cm, 'Handicap')
                reg_handicap_report.setFillColor(black)
                reg_handicap_report.setFont('Times-Roman', 15)
                y = 3.5
            i = 0
            space_found = False
            surname = ''
            first_name = ''
            while i <= len(key) and not space_found:
                if key[i] == ' ':
                    first_name = key[:i]
                    surname = key[i + 1:]
                    space_found = True
                i += 1
            reg_handicap_report.drawString(2 * cm, y * cm, surname)
            reg_handicap_report.drawString(6 * cm, y * cm, first_name)
            reg_handicap_report.drawString(14 * cm, y * cm, str(reg_dic[key]))
            y += 0.7

        # Save pdf
        reg_handicap_report.save()

    def create_guest_hcp_rep(self, week_num, year):
        """Creates the guest handicap report pdf"""
        guest_dic = self.get_new_hcp_dic('guests')

        # Create pdf
        guest_handicap_report = Canvas('guest-handicap-report-week{0}-{1}.pdf'.format(week_num, year), bottomup=0)

        # Consistent formatting
        guest_handicap_report.line(2 * cm, 4 * cm, 19 * cm, 4 * cm)
        guest_handicap_report.setFont('Times-Italic', 25)
        guest_handicap_report.setFillColor(darkblue)
        guest_handicap_report.drawString(5 * cm, 2 * cm, 'Latest Guest Handicap Report')
        guest_handicap_report.setFont('Times-Italic', 18)
        guest_handicap_report.drawString(2 * cm, 3.5 * cm, 'Surname')
        guest_handicap_report.drawString(6 * cm, 3.5 * cm, 'Name')
        guest_handicap_report.drawString(14 * cm, 3.5 * cm, 'Handicap')

        # Variable text
        guest_handicap_report.setFillColor(black)
        guest_handicap_report.setFont('Times-Roman', 15)

        y = 5
        for key in guest_dic:
            if y > 28:
                guest_handicap_report.showPage()
                # Consistent formatting
                guest_handicap_report.line(2 * cm, 2.5 * cm, 19 * cm, 2.5 * cm)
                guest_handicap_report.setFillColor(darkblue)
                guest_handicap_report.setFont('Times-Italic', 18)
                guest_handicap_report.drawString(2 * cm, 2 * cm, 'Surname')
                guest_handicap_report.drawString(6 * cm, 2 * cm, 'Name')
                guest_handicap_report.drawString(14 * cm, 32 * cm, 'Handicap')
                guest_handicap_report.setFillColor(black)
                guest_handicap_report.setFont('Times-Roman', 15)
                y = 3.5
            i = 0
            space_found = False
            surname = ''
            first_name = ''
            while i <= len(key) and not space_found:
                if key[i] == ' ':
                    first_name = key[:i]
                    surname = key[i + 1:]
                    space_found = True
                i += 1
            guest_handicap_report.drawString(2 * cm, y * cm, surname)
            guest_handicap_report.drawString(6 * cm, y * cm, first_name)
            guest_handicap_report.drawString(14 * cm, y * cm, str(guest_dic[key]))
            y += 0.7

        # Save pdf
        guest_handicap_report.save()

    def create_pdfs(self):
        """Creates all 8 PDFs"""
        password = self.kv.get_screen('pdf_menu').ids.password.text
        if password_is_valid(password) and not self.pos_is_set():
            week_num = self.get_week_num()
            year = self.get_year()
            self.set_std_scratch()
            name_dic = self.get_name_dic_for_pdf()
            hcp_dic = self.get_old_hcp_dic_for_pdf()
            # Create all weekly reports that require the old HCP
            self.create_weekly_report(name_dic, hcp_dic, week_num, year)  # created before other reports that use ranking as it sets and orders ranking list
            money_dic = self.calc_money()  # this order is important as well
            self.create_money_report(name_dic, hcp_dic, money_dic, week_num, year)
            self.update_player_dic(money_dic, name_dic)
            self.create_best_brut_report(hcp_dic, week_num, year)
            self.create_best_nine_report(week_num, year)
            self.create_best_three_brut_rep(name_dic, week_num, year)
            # Create the weekly reports that require the new HCP
            self.create_reg_hcp_rep(week_num, year)
            self.create_guest_hcp_rep(week_num, year)


    def reset_create_screen(self):
        """Resets all fields on screen on release of return to main screen button and confirm button"""
        self.kv.get_screen('create_game').ids.course_menu.text = 'Choose a course'
        self.kv.get_screen('create_game').ids.password.text = ''
        self.kv.get_screen('create_game').ids.week_num.text = ''
        self.kv.get_screen('create_game').ids.year.text = ''
        try:
            self.kv.get_screen('create_game').ids.options.text = 'Choose hole options'
        except:
            pass

    def build(self):
        return self.kv


if __name__ == '__main__':
    DesktopApp().run()
