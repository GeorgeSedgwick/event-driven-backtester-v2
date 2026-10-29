import pandas as pd
import os

class DummyUniverseManager():
    def __init__(self, universe_name):
        self.paths = {
            "SPX": "~/python-projects/ed-backtest/backtester/data/bloomberg_data/sp500_historical_constituents.csv"
        }
        self.path = self.paths[universe_name]
        self.latest_d = None
        self.load_all_members()

    def load_all_members(self):
        df = pd.read_csv(os.path.expanduser(self.path))
        df['Index Member'] = df['Index Member'].str.split().str[0] # Strip the bloomberg specific coding (US/UN/UA etc.)

        values = {} # Create a dict which will allow access to members at a given time
        dates = sorted(set(df.as_of_date))
        for s in dates: # Sorted set puts all unique month-ends in chronological order
            values[s] = df.loc[df.as_of_date == s, ['Index Member']] # Put all the members into their dict to be accessed

        self.all_members = values
        


    def update_current_members(self, dt): # Pass the current dt, convert the dt
        d = str(dt.date()) # Strip the time and convert remaining date to a string
        if self.latest_d is None:
            closest = max(date for date in self.all_members.keys() if date <= d)


            add_members = list(self.all_members[closest]['Index Member']) # List all the added members (in this case as its the first update every member is added)
            drop_members = [] # List all the dropped members (in this case no member is dropped)

            self.latest_members = add_members # Store all the latest members for future comparison
            self.latest_d = closest # Set the latest date used to compare

            print(f"First UPDATE: CLOSEST DATE: {closest} \n{add_members}")
            
            return add_members, drop_members


        else:
            if self.latest_d == max(date for date in self.all_members.keys() if date <= d): # If the latest_d is the same as the closest to current, return no adds/drops (no change in members)
                return [], []

            else:   # If the closest isn't the same as the last, assess changes
                closest = max(date for date in self.all_members.keys() if date <= d) # Get the closest date 

                members_at_date = list(self.all_members[closest]['Index Member']) # Find all the members at the new closest date of membership recording

                add_members = [t for t in members_at_date if t not in self.latest_members and t in members_at_date] # Record all the new added members
                drop_members = [t for t in self.latest_members if t in self.latest_members and t not in members_at_date] # Record all the dropped members

                self.latest_members = members_at_date
                self.latest_d = closest

                return add_members, drop_members # Return both the newly added and dropped members

