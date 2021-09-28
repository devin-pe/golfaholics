from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.tab import MDTabsBase
from kivy.properties import StringProperty
from kivy.metrics import dp
import pyrebase


# Design our different screens
class WindowManager(ScreenManager):
    pass


class MainWindow(Screen):
    pass


class LoginWindow(Screen):
    pass


class InitWindow(Screen):
    pass


class AddPlayerWindow(Screen):
    pass


class ScoreWindow(Screen):
    pass


class TableWindow(Screen):
    pass


class ConfirmationWindow(Screen):
    pass


class FinalWindow(Screen):
    pass


class Tab1(MDFloatLayout, MDTabsBase):
    """Class implementing content for the 1st type of tab."""
    icon = StringProperty()
    title = StringProperty()
    font_size = '14sp'


class Tab2(MDFloatLayout, MDTabsBase):
    """Class implementing content for the 2nd type of tab."""
    icon = StringProperty()
    title = StringProperty()
    font_size = '14sp'


class Tab3(MDFloatLayout, MDTabsBase):
    """Class implementing content for the 3rd type of tab."""
    icon = StringProperty()
    title = StringProperty()
    font_size = '14sp'


class Tab4(MDFloatLayout, MDTabsBase):
    """Class implementing content for the 4th type of tab."""
    icon = StringProperty()
    title = StringProperty()
    font_size = '14sp'


def validate_score(text):
    """Validates scores before they are entered in the table"""
    if not text.isdigit():
        return 'N/A'
    else:
        return text


def username_is_in_db(reg_db_dic, guest_db_dic, username):
    for key in reg_db_dic:
        if key == username:
            return True
    for key in guest_db_dic:
        if key == username:
            return True
    return False


class ScoresApp(MDApp):
    def __init__(self):
        """Constructor"""
        super().__init__()
        # Attributes for controlling buttons on AddPlayerWindow screen
        self.is_p1_clicked = False
        self.is_p2_clicked = False
        self.is_p3_clicked = False
        self.is_p4_clicked = False
        self.is_p1_set = False
        self.is_p2_set = False
        self.is_p3_set = False
        self.is_p4_set = False
        # Attribute for determining how many players are in the game
        self.n_of_players = 1
        # Attribute for incrementing tab hole numbers
        self.hole_number = 1
        # List attribute that contains all scores
        self.row_data = []
        # Attribute for holding the score data
        self.score_data = []
        # Attribute for storing the game number
        self.game_number = 0
        # Accessing DB
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

    def validate_login(self):
        """Validates the data in login box when the confirm button is pressed on the LoginWindow screen and
        moves user to correct screen"""
        username = self.kv.get_screen('login').ids.username
        error_label = self.kv.get_screen('login').ids.error
        reg_db_dic = dict(self.db.child('regulars').get().val())
        guest_db_dic = dict(self.db.child('guests').get().val())

        if username.text == '':
            username.hint_text = 'Enter username again'
            error_label.text = 'Username field cannot be empty'

        elif not username.text.isalpha():
            username.text = ''
            username.hint_text = 'Enter username again'
            error_label.text = 'Username field cannot contain numbers'

        elif len(username.text) > 6:
            username.text = ''
            username.hint_text = 'Enter username again'
            error_label.text = 'Username field cannot contain more than 6 characters'

        elif self.is_username_duplicate(username):
            username.text = ''
            username.hint_text = 'Enter username again'
            error_label.text = 'The player has already been added to the game'

        elif not username_is_in_db(reg_db_dic, guest_db_dic, username.text):
            username.text = ''
            username.hint_text = 'Enter username again'
            error_label.text = 'The player has not been added to the database'

        elif self.is_p2_clicked or self.is_p3_clicked or self.is_p4_clicked:
            error_label.text = ''
            self.update_correct_button()
            username.text = ''
            self.root.current = 'add_player'
        else:
            self.is_p1_clicked = True
            error_label.text = ''
            self.update_correct_button()
            username.text = ''
            self.root.current = 'add_player'

    def validate_init(self):
        """Ensures the entered game number is valid.
        Confirms that the course selection and options are valid
        Moves user to ScoreWindow screen if this is the case. """
        if self.kv.get_screen('init').ids.game_num.text.isdigit():
            self.set_game_number(int(self.kv.get_screen('init').ids.game_num.text))
            if self.game_number < 1 or self.game_number > 20:
                self.reset_init()
                self.kv.get_screen('init').ids.error.text = 'Enter a game number from 1 to 20 inclusive'
            else:
                self.add_correct_tab_widget()
                self.root.current = 'score'
        else:
            self.kv.get_screen('init').ids.error.text = 'Enter a game number from 1 to 20 inclusive'

    def reset_init(self):
        self.kv.get_screen('init').ids.game_num.text = ''

    def set_game_number(self, game_number):
        """Sets the self.game_number attribute"""
        self.game_number = game_number

    def validate_button(self):
        """Ensures the user does not update the text of the wrong button on the AddPlayerWindow screen.
        Moves user to LoginWindow screen if this is the case. """
        if self.is_p2_clicked and not self.is_p1_set:
            self.kv.get_screen('add_player').ids.add_player_error.text = 'Add player 1 before player 2'
            self.is_p2_clicked = False
        elif self.is_p3_clicked and (not self.is_p1_set or not self.is_p2_set):
            self.kv.get_screen('add_player').ids.add_player_error.text = 'Add player 2 before player 3'
            self.is_p3_clicked = False
        elif self.is_p4_clicked and (not self.is_p1_set or not self.is_p2_set or not self.is_p3_set):
            self.kv.get_screen('add_player').ids.add_player_error.text = 'Add player 3 before player 4'
            self.is_p4_clicked = False
        else:
            self.root.current = 'login'

    def update_correct_button(self):
        """Updates the text of the button on the AddPlayerWindow screen."""
        if self.is_p1_clicked:
            self.kv.get_screen('add_player').ids.player1.text = self.kv.get_screen('login').ids.username.text
            self.is_p1_clicked = False
            self.is_p1_set = True
        elif self.is_p2_clicked and self.is_p1_set:
            self.kv.get_screen('add_player').ids.player2.text = self.kv.get_screen('login').ids.username.text
            self.is_p2_clicked = False
            self.is_p2_set = True
        elif self.is_p3_clicked and self.is_p1_set and self.is_p2_set:
            self.kv.get_screen('add_player').ids.player3.text = self.kv.get_screen('login').ids.username.text
            self.is_p3_clicked = False
            self.is_p3_set = True
        elif self.is_p4_clicked and self.is_p1_set and self.is_p2_set and self.is_p3_set:
            self.kv.get_screen('add_player').ids.player4.text = self.kv.get_screen('login').ids.username.text
            self.is_p4_clicked = False
            self.is_p4_set = True

    def is_username_duplicate(self, username):
        """Returns True if the entered username is a duplicate and False otherwise"""
        if self.is_p3_set:
            if username.text == self.kv.get_screen('add_player').ids.player1.text:
                return True
            elif username.text == self.kv.get_screen('add_player').ids.player2.text:
                return True
            elif username.text == self.kv.get_screen('add_player').ids.player3.text:
                return True
            else:
                return False
        elif self.is_p2_set:
            if username.text == self.kv.get_screen('add_player').ids.player1.text:
                return True
            elif username.text == self.kv.get_screen('add_player').ids.player2.text:
                return True
            else:
                return False
        elif self.is_p1_set:
            if username.text == self.kv.get_screen('add_player').ids.player1.text:
                return True
            else:
                return False
        else:
            return False

    def go_to_correct_screen(self):
        if self.is_p2_clicked or self.is_p3_clicked or self.is_p4_clicked:
            self.root.current = 'add_player'
        else:
            self.root.current = 'main'

    def add_correct_number_of_tabs(self):
        """Returns the number of holes being played which serves to create tabs in another function."""
        for val in dict(self.db.child('games').child('game{0}'.format(self.game_number)).get().val()).values():
            if val == 'Full 18':
                return 18
            elif val == 'Front 9':
                return 9
            elif val == 'Back 9':
                return 9
            elif val == 'France':
                return 9
            elif val == 'Luxembourg':
                return 9
            elif val == 'Germany':
                return 9
            else:
                raise Exception('No hole options added to game.')

    def create_tab_type1(self, correct_num_of_tabs):
        """Creates the tabs for 1 player."""
        game_num = self.get_latest_game_num()
        if self.hole_number == correct_num_of_tabs:
            tab_type1 = Tab1(text='Hole {0}'.format(self.hole_number))
            tab_type1.ids.tab_layout.add_widget(
                MDRoundFlatButton(
                    text='Confirm',
                    size_hint=(None, None),
                    width=self.root.width * 0.9,
                    pos_hint={'x': 0.44, 'top': 0.07},
                    on_release=lambda x: self.go_to_confirmation_window()
                )
            )
            # Add button with on_release property set
        else:
            tab_type1 = Tab1(text='Hole {0}'.format(self.hole_number))
            # Otherwise create normal tab
        tab_type1.ids.tab_layout.add_widget(
            MDLabel(
                text='Par ' + str(self.get_hole_par(self.hole_number, game_num)),
                font_size='16sp',
                halign='center',
                size_hint=(None, None),
                width=self.root.width,
                height=self.root.height / 22,
                pos_hint={'x': 0, 'top': 0.92},
            )
        )
        tab_type1.ids.tab_layout.add_widget(
            MDLabel(
            text = 'Hole Index: {0}'.format(self.get_hole_index(self.hole_number, game_num)),
            color = (255 / 255, 0, 0, 0.64),
            halign = 'center',
            size_hint =  (None, None),
            width = self.root.width,
            height = self.root.height / 30,
            pos_hint = {'x': 0, 'top': 0.86},
            )
        )
        return tab_type1

    def create_tab_type2(self, correct_num_of_tabs):
        """Creates the tabs for 2 players."""
        game_num = self.get_latest_game_num()
        if self.hole_number == correct_num_of_tabs:
            tab_type2 = Tab2(text='Hole {0}'.format(self.hole_number))
            tab_type2.ids.tab_layout.add_widget(
                MDRoundFlatButton(
                    text='Confirm',
                    size_hint=(None, None),
                    width=self.root.width * 0.9,
                    pos_hint={'x': 0.44, 'top': 0.07},
                    on_release=lambda x: self.go_to_confirmation_window()
                )
            )
            # Remove button on last tab and add identical one with on_release property set
        else:
            tab_type2 = Tab2(text='Hole {0}'.format(self.hole_number))
            # Otherwise create normal tab
        tab_type2.ids.tab_layout.add_widget(
            MDLabel(
                text='Par ' + str(self.get_hole_par(self.hole_number, game_num)),
                font_size='16sp',
                halign='center',
                size_hint=(None, None),
                width=self.root.width,
                height=self.root.height / 22,
                pos_hint={'x': 0, 'top': 0.92},
            )
        )
        tab_type2.ids.tab_layout.add_widget(
            MDLabel(
                text='Hole Index: {0}'.format(self.get_hole_index(self.hole_number, game_num)),
                color=(255 / 255, 0, 0, 0.64),
                halign='center',
                size_hint=(None, None),
                width=self.root.width,
                height=self.root.height / 30,
                pos_hint={'x': 0, 'top': 0.86},
            )
        )
        return tab_type2

    def create_tab_type3(self, correct_num_of_tabs):
        """Creates the tabs for 3 players."""
        game_num = self.get_latest_game_num()
        if self.hole_number == correct_num_of_tabs:
            tab_type3 = Tab3(text='Hole {0}'.format(self.hole_number))
            tab_type3.ids.tab_layout.add_widget(
                MDRoundFlatButton(
                    text='Confirm',
                    size_hint=(None, None),
                    width=self.root.width * 0.9,
                    pos_hint={'x': 0.44, 'top': 0.07},
                    on_release=lambda x: self.go_to_confirmation_window()
                )
            )
            # Remove button on last tab and add identical one with on_release property set
        else:
            tab_type3 = Tab3(text='Hole {0}'.format(self.hole_number))
            # Otherwise create normal tab
        tab_type3.ids.tab_layout.add_widget(
            MDLabel(
                text='Par ' + str(self.get_hole_par(self.hole_number, game_num)),
                font_size='16sp',
                halign='center',
                size_hint=(None, None),
                width=self.root.width,
                height=self.root.height / 22,
                pos_hint={'x': 0, 'top': 0.92},
            )
        )
        tab_type3.ids.tab_layout.add_widget(
            MDLabel(
                text='Hole Index: {0}'.format(self.get_hole_index(self.hole_number, game_num)),
                color=(255 / 255, 0, 0, 0.64),
                halign='center',
                size_hint=(None, None),
                width=self.root.width,
                height=self.root.height / 30,
                pos_hint={'x': 0, 'top': 0.86},
            )
        )
        return tab_type3

    def create_tab_type4(self, correct_num_of_tabs):
        """Creates the tabs for 4 players."""
        game_num = self.get_latest_game_num()
        if self.hole_number == correct_num_of_tabs:
            tab_type4 = Tab4(text='Hole {0}'.format(self.hole_number))
            tab_type4.ids.tab_layout.add_widget(
                MDRoundFlatButton(
                    text='Confirm',
                    size_hint=(None, None),
                    width=self.root.width * 0.9,
                    pos_hint={'x': 0.44, 'top': 0.07},
                    on_release=lambda x: self.go_to_confirmation_window()
                )
            )
            # Remove button on last tab and add identical one with on_release property set
        else:
            tab_type4 = Tab4(text='Hole {0}'.format(self.hole_number))
            # Otherwise create normal tab
        tab_type4.ids.tab_layout.add_widget(
            MDLabel(
                text='Par ' + str(self.get_hole_par(self.hole_number, game_num)),
                font_size='16sp',
                halign='center',
                size_hint=(None, None),
                width=self.root.width,
                height=self.root.height / 22,
                pos_hint={'x': 0, 'top': 0.92},
            )
        )
        tab_type4.ids.tab_layout.add_widget(
            MDLabel(
                text='Hole Index: {0}'.format(self.get_hole_index(self.hole_number, game_num)),
                color=(255 / 255, 0, 0, 0.64),
                halign='center',
                size_hint=(None, None),
                width=self.root.width,
                height=self.root.height / 30,
                pos_hint={'x': 0, 'top': 0.86},
            )
        )
        return tab_type4

    def add_correct_tab_widget(self):
        """Adds the right type and number of Tab widgets to the screen depending on
        how many players are in the game and how many holes are being played."""
        correct_num_of_tabs = self.add_correct_number_of_tabs()
        # Set the number of tabs to be added
        while self.hole_number <= correct_num_of_tabs:
            if self.is_p1_set and not self.is_p2_set:
                tab_type1 = self.create_tab_type1(correct_num_of_tabs)
                # Create the 1st type of tab if only player1 is set
                self.kv.get_screen('score').ids['tab{0}'.format(self.hole_number)] = tab_type1
                self.kv.get_screen('score').ids.score_layout.add_widget(tab_type1)
                # Give tab an ID and add it to the 'score' screen
            elif self.is_p2_set and not self.is_p3_set:
                tab_type2 = self.create_tab_type2(correct_num_of_tabs)
                # Create the 2nd type of tab if player2 is set
                self.kv.get_screen('score').ids['tab{0}'.format(self.hole_number)] = tab_type2
                self.kv.get_screen('score').ids.score_layout.add_widget(tab_type2)
                # Give tab an ID and add it to the 'score' screen
            elif self.is_p3_set and not self.is_p4_set:
                tab_type3 = self.create_tab_type3(correct_num_of_tabs)
                # Create the 3rd type of tab if player3 is set
                self.kv.get_screen('score').ids['tab{0}'.format(self.hole_number)] = tab_type3
                self.kv.get_screen('score').ids.score_layout.add_widget(tab_type3)
                # Give tab an ID and add it to the 'score' screen
            elif self.is_p4_set:
                tab_type4 = self.create_tab_type4(correct_num_of_tabs)
                # Create the 4th type of tab if player4 is set
                self.kv.get_screen('score').ids['tab{0}'.format(self.hole_number)] = tab_type4
                self.kv.get_screen('score').ids.score_layout.add_widget(tab_type4)
                # Give tab an ID and add it to the 'score' screen
            self.hole_number += 1

    def go_to_confirmation_window(self):
        """Defines tables in the TableWindow1 and TableWindow2 and moves to TableWindow1."""
        self.set_row_data()
        self.create_table1(self.get_column_data(), self.row_data)
        self.root.current = 'table'

    def set_row_data(self):
        """Adds all input data from MDTextFields to a list of lists
        Returns the list of lists containing the input scores.
        Sets the n_of_players attribute that is used later."""
        scores_list = [[], [], [], []]
        hole_n = 0  # Start at 0 to avoid the score_layout id in the next loop
        for key1 in self.kv.get_screen('score').ids.items():
            if key1[0] == 'tab{0}'.format(hole_n):
                for key2 in key1[1].ids.items():
                    # Loop through ids in tabs to access the text of the MDTextFields
                    if self.is_p4_set:
                        # If there are 4 players in game
                        if key2[0] == 'hole_user_input_p1':
                            scores_list[0].append(validate_score(key2[1].text))
                        elif key2[0] == 'hole_user_input_p2':
                            scores_list[1].append(validate_score(key2[1].text))
                        elif key2[0] == 'hole_user_input_p3':
                            scores_list[2].append(validate_score(key2[1].text))
                        elif key2[0] == 'hole_user_input_p4':
                            scores_list[3].append(validate_score(key2[1].text))

                    elif self.is_p3_set:
                        # If there are 3 players in game
                        if key2[0] == 'hole_user_input_p1':
                            scores_list[0].append(validate_score(key2[1].text))
                        elif key2[0] == 'hole_user_input_p2':
                            scores_list[1].append(validate_score(key2[1].text))
                        elif key2[0] == 'hole_user_input_p3':
                            scores_list[2].append(validate_score(key2[1].text))

                    elif self.is_p2_set:
                        # If there are 2 players in game
                        if key2[0] == 'hole_user_input_p1':
                            scores_list[0].append(validate_score(key2[1].text))
                        if key2[0] == 'hole_user_input_p2':
                            scores_list[1].append(validate_score(key2[1].text))

                    elif self.is_p1_set:
                        # If there is 1 player in game
                        if key2[0] == 'hole_user_input_p1':
                            scores_list[0].append(validate_score(key2[1].text))

            hole_n += 1
        self.row_data = self.get_list_of_score_tuples(scores_list)
        # Manipulate row data to be in correct format

    def get_list_of_score_tuples(self, scores_list):
        """Removes the empty lists from the list of lists.
        Adds the player's username to the front for table formatting purposes.
        Transforms the list of lists into a list of tuples.
        Returns the list of tuple(s) containing input scores."""
        counter = 0
        if self.is_p4_set:
            # If 4 players are added to the game
            self.n_of_players = 4
            for key in self.kv.get_screen('add_player').ids.items():
                # Loop through the ids in the the AddPlayerWindow
                if counter < 4:
                    scores_list[counter].insert(0, key[1].text)
                    scores_list[counter] = tuple(scores_list[counter])
                    # Add player name in the AddPlayerWindow to the front of each nested list
                    # Convert the list into a tuple
                counter += 1
        elif self.is_p3_set:
            self.n_of_players = 3
            del scores_list[3]
            for key in self.kv.get_screen('add_player').ids.items():
                if counter < 3:
                    scores_list[counter].insert(0, key[1].text)
                    scores_list[counter] = tuple(scores_list[counter])
                counter += 1
        elif self.is_p2_set:
            self.n_of_players = 4
            del scores_list[2:4]
            for key in self.kv.get_screen('add_player').ids.items():
                if counter < 2:
                    scores_list[counter].insert(0, key[1].text)
                    scores_list[counter] = tuple(scores_list[counter])
                counter += 1
        elif self.is_p1_set:
            self.n_of_players = 1
            del scores_list[1:4]
            scores_list[0].insert(0, self.kv.get_screen('add_player').ids.player1.text)
            scores_list[0] = tuple(scores_list[0])

        else:
            raise Exception('Fatal error, the number of players in the game must be between 1 and 4 inclusive')

        return scores_list

    def get_column_data(self):
        """Returns list of tab names for tables on TableWindow screen."""
        hole_n = 1
        column_data = [('Players', dp(30))]
        # Add first column header
        for key, value in self.kv.get_screen('score').ids.items():
            if key == 'tab{0}'.format(hole_n):
                column_data.append((value.text, dp(30)))
                # Add hole names as column headers
                hole_n += 1
        return column_data

    def create_table1(self, column_data, row_data):
        """Creates table containing input scores of all holes to be displayed
        on the TableWindow screen"""
        table = MDDataTable(
            size_hint=(None, None),
            pos_hint={'x': 0, 'top': 0.95},
            width=self.root.width,
            height=self.root.height * 0.6,
            column_data=column_data,
            row_data=row_data)
        self.kv.get_screen('table').ids.table_layout.add_widget(table)
        # Add table to TableWindow screen

    def validate_table(self):
        """Ensures that no fields have been left blank, contain negative numbers
        or positive numbers that are too large.
        If this is the case the error label on the TableWindow screen will be set.
        If all entries are valid, jump to ConfirmationScreen"""
        no_errors = True
        error_text = ''
        for row in self.row_data:
            # Loop through list
            i = 1
            while i < len(row):
                j = 1
                while j <= self.n_of_players:
                    # Loop through tuple, validate each item
                    if not row[i].isdigit():
                        error_text = 'Please enter a valid number in every field, ' \
                                     'consult the table above to locate fields marked "N/A"'
                        no_errors = False
                    elif int(row[i]) > 10:
                        error_text = 'Fields cannot contain a number exceeding 10. ' \
                                     'Please scratch the hole by entering 0 or double check your entry in the table.'
                        no_errors = False
                    j += 1
                    self.kv.get_screen('table').ids.error.text = error_text
                i += 1

        if no_errors:
            self.root.current = 'confirmation'

    def get_latest_game_num(self):
        """Returns the most recent game number, the one we use to update the db and create pdfs"""
        num_list = []
        for game in dict(self.db.child('games').get().val()).keys():
            num_list.append(int(game[4:]))
        return max(num_list)

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

    def get_handicap(self):
        """Determines a player's global handicap from information stored in DB"""
        return 15  # Replace this default value

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

    def get_data(self):
        """Creates a dictionary of scores using self.row_data"""
        for tup in self.row_data:
            counter = 0
            temp_dict = {}
            while counter <= len(tup) - 1:
                if counter == 0:
                    temp_dict['username'] = tup[counter]
                else:
                    temp_dict['h{0}score'.format(counter)] = int(tup[counter])
                counter += 1
            self.score_data.append(temp_dict)

    def store_data(self):
        """Stores all entered data into the DB"""
        self.get_data()  # Set self.score_data
        for dic in self.score_data:
            key_found = False
            if self.db.child('games').child('game{0}'.format(self.game_number)).get().val() is None:
                # If this is the first time any scores are being stored for a particular game
                self.db.child('games').child('game{0}'.format(self.game_number)).child(dic['username']).set(dic)
                # Set the score data in the DB
            else:
                for key in dict(self.db.child('games').child('game{0}'.format(self.game_number)).get().val()).keys():
                    # Loop through dict of scores
                    if key == dic['username']:
                        # If a matching username is found
                        self.db.child('games').child('game{0}'.format(self.game_number)).child(dic['username']).update(dic)
                        # Update the DB
                        key_found = True
                        break  # End for loop if the key is found
                if not key_found:
                    # If the username is not found in the list of already stored data
                    self.db.child('games').child('game{0}'.format(self.game_number)).child(dic['username']).set(dic)
                    # Set the score data in the DB

    def build(self):
        """Builds the app"""
        self.kv = Builder.load_file('golfaholics.kv')
        return self.kv


if __name__ == '__main__':
    ScoresApp().run()
