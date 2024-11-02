import random
import time

class Dice:
    def __init__(self, player1, player2, starting_dice=200, starting_bet=1):
        #p contain integers for player ids
        self.p=[player1, player2]
        self.starting_dice=starting_dice
        self.starting_bet=starting_bet
        self.current_dice=starting_dice
        self.current_bet=starting_bet
        #0 for p1, 1 for p2
        self.turn=0
        #[0] is p1 and [1] is p2, they are always opposite of each other
        self.scores=[0,0]
        #list of tuple of (starting_player 0 or 1,[list of numbers thats the rolls])
        self.history=None
        #if the dice roll round has started no interrupt is allowed.
        self.round_started=False
        self.previous_roll=0
    
    #returns player id given the number they are assigned in game
    def return_player(self, player_num):
        try:
            return self.p[player_num];
        except:
            print("player num must be 0 or 1")
            
    #return -1 if round not end, 0 or 1 depending on who lost the round
    def round_loser(self):
        p=self.history[-1][0]
        num_turns=len(self.history[-1][1])
        if num_turns>0 and self.history[-1][1][-1]==1:
            if p==0:
                if num_turns%2==1:
                    return 0;
                else:
                    return 1;
            else:
                if num_turns%2==1:
                    return 1;
                else:
                    return 0;
        else:
            return -1;
    
    def raise_the_stake(self, raise_value):
        if self.round_started and raise_value>0:
            self.current_bet+=raise_value
        else:
            print("can't raise stake right now")
    
    #winning_plyer is 0 or 1
    def update_score(self, losing_player):
        self.scores[losing_player]-=self.current_bet;
        self.scores[(losing_player+1)%2]+=self.current_bet;
    
    #starting_player is 0 or 1
    def start_round(self, starting_player=0):
        if not self.round_started and self.history!=None:
            self.history.append((starting_player, []))
            self.round_started=True;
            self.turn=starting_player
            self.current_dice=self.starting_dice
            self.current_bet=self.starting_bet
            self.previous_roll=0
        else:
            print("round hasn't ended yet or game hasn't started. if not startd call start_game first.")
    
    
    def start_game(self):
        if self.history==None:
            self.history=[(self.turn, [])]
            self.round_started=True;
            self.current_dice=self.starting_dice
            self.current_bet=self.starting_bet
        else:
            print("game already started")
        
    def roll(self):
        if self.round_started:
            rolled_num = random.randint(1, self.current_dice)
            self.current_dice=rolled_num
            self.history[-1][1].append(rolled_num)
            self.turn=(self.turn+1)%2
            if rolled_num==1:
                self.round_started=False
                self.update_score(self.round_loser())
            if self.previous_roll==rolled_num:
                self.current_bet+=self.starting_bet
            self.previous_roll=rolled_num
            return rolled_num
        else:
            print("round didn't start")
            return -1;
        
    def stake_toString(self):
        return "Current Stake is " + str(self.current_bet) + "\n"
    
    def score_toString(self):
        return str(self.p[0])+": "+str(self.scores[0]) + ", " + str(self.p[1])+": "+str(self.scores[1]) + "\n"
    
    def turn_toString(self):
        return self.p[self.turn]+"'s Turn\n"
    
    def most_recent_roll(self):
        try:
            if self.history!=None:
                return self.history[-1][1][-1];
            else:
                return 0;
        except:
            return 0;
            