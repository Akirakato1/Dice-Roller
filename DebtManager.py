import json
class DebtManager:
    def __init__(self,json_path="./ledger.json"):
        self.json_path=json_path
        self.data={}
    
    def retrieve_data(self):
        try:
            with open(self.json_path, 'r') as file:
                self.data = json.load(file)
                return 0;
        except FileNotFoundError:
            print("The JSON file was not found.")
            return -1;
        except json.JSONDecodeError:
            print("JSON decode error - the file may not contain valid JSON.")
            return -1;
    
    def store_data(self):
        # Open the file for writing
        with open(self.json_path, 'w') as file:
            # Convert the Python dictionary to a JSON string and write it to a file
            json.dump(self.data, file, indent=4) 
            
    def update_data(self, debtorid,creditorid, amount):
        self.retrieve_data()
        if str(debtorid) not in self.data.keys():
            self.data[str(debtorid)]={}
        if str(creditorid) not in self.data[str(debtorid)].keys():
            self.data[str(debtorid)][str(creditorid)]=-1*amount
        else:
            self.data[str(debtorid)][str(creditorid)]-=amount
        if str(creditorid) not in self.data.keys():
            self.data[str(creditorid)]={}
        if str(debtorid) not in self.data[str(creditorid)].keys():
            self.data[str(creditorid)][str(debtorid)]=amount 
        else:
            self.data[str(creditorid)][str(debtorid)]+=amount
        self.store_data()
    
    def get_ledger(self, playerid):
        self.retrieve_data()
        if str(playerid) not in self.data.keys():
            return {}
        return self.data[str(playerid)]
    
    def get_score(self, playerid):
        self.retrieve_data()
        total=0
        string=""
        if str(playerid) not in self.data.keys():
            return "Player Not Found"
        
        for key, value in self.data[str(playerid)].items():
            string+=key+" owes "+str(value)+"\n"
            total+=value
        string+="Total worth: "+str(total)
        return string