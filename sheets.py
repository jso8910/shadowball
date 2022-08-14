import gspread


class ShadowballSheet:
    def __init__(self):
        self.client = gspread.service_account(filename="creds.json")
        self.spreadsheet = self.client.open_by_key("1eeSWjQR34ie2o6-CyOsUoqawhW5HmxScYZ06xxRoWGo")
        home_sheet = self.spreadsheet.worksheet("Shadowball (cumulative)")
        current_game = home_sheet.get("R1")
        if current_game == []:
            self.game = None
        else:
            self.game = current_game[0][0]
        # template = self.spreadsheet.worksheet("Template")
    
    def new_game(self, away, home, day):
        template = self.spreadsheet.worksheet("Template")
        template.duplicate(insert_sheet_index=1, new_sheet_name=f"{away} v {home} {day}")

    def set_game(self, sheet_name):
        if sheet_name not in self.get_games():
            return "Something went wrong and you didn't enter a real game"
        self.game = sheet_name
        home_sheet = self.spreadsheet.worksheet("Shadowball (cumulative)")
        home_sheet.update("R1", sheet_name)

    def get_games(self):
        """Returns the titles of all sheets other than the general"""
        return [sheet.title for sheet in self.spreadsheet.worksheets()[1:-2]]

    def make_guess(self, username, guess):
        """Enters the guess of a user into the sheet"""
        username = str(username)
        if guess < 1 or guess > 1000:
            raise ValueError("Guess a number from 1–1000. No more, no less.")
        already_made_guess = False
        if self.game == None:
            raise ValueError("Current game hasn't been set. Try using (or telling your GM to use) /set_game")
        game_sheet = self.spreadsheet.worksheet(self.game)
        lookup = self.spreadsheet.worksheet("Player lookup").get("A1:B21")
        idx = None
        for index, row in enumerate(lookup):
            if row[1] == username:
                idx = index
                break
        if idx == None:
            raise ValueError("You aren't a Panther, stop using this bot smh")
        player_name = lookup[idx][0]

        current_guesses = game_sheet.get("P3:R21")
        for index, row in enumerate(current_guesses):
            if player_name in row:
                idx = index
                break

        if current_guesses[idx][1] != 0:
            already_made_guess = True
        current_guesses[idx][2] = "=true"
        current_guesses[idx][1] = guess
        game_sheet.update("P3:R21", current_guesses, value_input_option='USER_ENTERED')
        return already_made_guess

    def finish_pitch(self, pitch, homer_diff):
        """Calculates the number of points owned by a pitch, whether a homer has been guessed, and primes the spreadsheet for the next pitch"""
        if pitch < 1 or pitch > 1000:
            raise ValueError("Pitch must be a number from 1–1000. No more, no less.")
        if self.game == None:
            raise ValueError("Current game hasn't been set. Try using /set_game. You should know this, you're a GM!")
        game_sheet = self.spreadsheet.worksheet(self.game)
        guesses = game_sheet.get("P3:R21")
        leaderboard = game_sheet.get("B3:D21")
        homerball = game_sheet.get("F3:H21")
        for row in guesses:
            if int(row[1]) == 0:
                continue
            idx = None
            for index, leaderboard_row in enumerate(leaderboard):
                if row[0] in leaderboard_row:
                    idx = index
            if idx == None:
                raise ValueError(f"I really don't know what went wrong but just complain to me (jso#4316). Tell me that probably it had something to do with {row[0]} not being in the leaderboard.")
            leaderboard[idx][1] = int(leaderboard[idx][1]) + 1
            # Also for some reason the leaderboards aren't updating, I assume it has something to do with this diff formula
            diff = abs(pitch - int(row[1]))
            if diff > 500: diff = 1000 - diff
            if diff <= 50:
                leaderboard[idx][2] = int(leaderboard[idx][2]) + 4
            elif diff <= 100:
                leaderboard[idx][2] = int(leaderboard[idx][2]) + 3
            elif diff <= 150:
                leaderboard[idx][2] = int(leaderboard[idx][2]) + 2
            elif diff <= 200:
                leaderboard[idx][2] = int(leaderboard[idx][2]) + 1

            idx = None
            for index, homerball_row in enumerate(homerball):
                if row[0] in homerball_row:
                    idx = index
            if idx == None:
                raise ValueError(f"I really don't know what went wrong but just complain to me (jso#4316). Tell me that it probably had something to do with {row[0]} not being in the homer leaderboard.")
            if diff <= homer_diff:
                homerball[idx][2] = int(homerball[idx][2]) + 1

        for index, row in enumerate(guesses):
            guesses[index][1] = 0
            guesses[index][2] = "=FALSE"

        game_sheet.update("P3:R21", guesses, value_input_option='USER_ENTERED')
        game_sheet.update("B3:D21", leaderboard)
        game_sheet.update("F3:H21", homerball)

    def get_leaderboard(self, min_pitches):
        """Returns a leaderboard sorted by points per pitch for the current game"""
        if self.game == None:
            raise ValueError("Current game hasn't been set. Try using /set_game. You should know this, you're a GM!")
        game_sheet = self.spreadsheet.worksheet(self.game)
        leaderboard = game_sheet.get("B3:D21")

        filtered_leaderboard = list(filter(lambda row: int(row[1]) >= min_pitches, leaderboard))
        return sorted(filtered_leaderboard, key=lambda row: int(row[2]) / int(row[1]), reverse=True)

    def get_homerball_lb(self, min_pitches):
        """Returns a leaderboard sorted by points per pitch for the current game's homerball"""
        if self.game == None:
            raise ValueError("Current game hasn't been set. Try using /set_game. You should know this, you're a GM!")
        game_sheet = self.spreadsheet.worksheet(self.game)
        leaderboard = game_sheet.get("B3:D21")
        homerball = game_sheet.get("F3:H21")

        filtered_leaderboard = list(filter(lambda row: int(row[1]) >= min_pitches, leaderboard))
        filtered_homerball = []
        for row in filtered_leaderboard:
            for homer_row in homerball:
                if row[0] in homer_row:
                    homer_row.append(row[1])
                    filtered_homerball.append(homer_row)
        return sorted(filtered_homerball, key=lambda row: int(row[2]), reverse=True)