import tkinter as tk 
from tkinter import ttk, simpledialog
from web3.auto import w3
from web3 import Web3, exceptions, gas_strategies, middleware, eth
import json
from web3.middleware import geth_poa_middleware 
from datetime import datetime 
from tkinter.filedialog import askopenfile 
from time import time, sleep 



class Connect4Dapp(tk.Tk):
    def __init__(self, *args, title="Connect4 Dapp", **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("1000x700") 
        self.wm_title(title) 
        self.config(bg="white")
        self.frame = tk.Frame(self, bg="white")
        self.frame.pack(expand=1, fill='both')

        try:
            self.config = json.load(open("config.json"))
        except:
            self.config = {"network": {"rinkeby": {"accounts": []}}, "default_gas_values": {"challengeOpponent": 600000, 
                                                                                            "acceptChallenge": 600000, 
                                                                                            "move": 600000, 
                                                                                            "moveCFW": 1000000, 
                                                                                            "declareRefundDueToChallengeExpiration": 600000, 
                                                                                            "declareWinDueToOverstall": 600000, 
                                                                                            "withdraw": 600000}}

        self.ribbon = tk.Frame(self.frame) 
        self.ribbon.pack(side="top", fill="x") 

        self.game_data = {}
        self.address = None 
        self.current_game = None 
        self.target_slot = None 
        self.taken_slots = []

        self.new_game_btn = ttk.Button(self.ribbon, width=5, text="+", state='disabled') 
        self.new_game_btn.pack(side="right", padx=5) 
        self.new_game_btn.bind("<Button-1>", self.new_game)
        
        self.clock = tk.Label(self.ribbon, text="") 
        self.clock.pack(side="left", padx=10)

        self.load_game_sb = tk.Spinbox(self.ribbon, width=5, from_=0, to=0, command=lambda: self.load_game()) 
        self.load_game_sb.pack(side="left", padx=10) 
        

        render_setup = self.load_web3(init=True)

        settings_btn = ttk.Button(self.ribbon, text="Settings") 
        settings_btn.pack(side="right", padx=10)
        settings_btn.bind("<Button-1>", lambda e: self.setup_app())

        self.canvas = tk.Canvas(self.frame, width=600, height=450, bg="blue")
        self.canvas.pack(side="top", pady=20) 

        ygap = 35 
        xgap = 35

        ctop = 10
        cleft = 35
        cheight = 40
        cwidth = 40
        
        self.ovals = {}
        for i in range(7): 
            for ii in reversed(range(6)):
                oval = self.canvas.create_oval((cleft, ctop, cleft + cwidth, ctop + cheight), fill="white") 
                text_x = (cleft + (cleft + cwidth)) / 2 
                text_y = (ctop + (ctop + cheight)) / 2
                oval_label = f"{str(i+1)},{str(ii+1)}"
                # self.canvas.create_text((text_x, text_y), text=oval_label)
                self.ovals[oval_label] = oval
                ctop += cheight + ygap 
            cleft += cwidth + xgap
            ctop = 10 

        self.game_frame = tk.Frame(self.frame) 
        self.game_frame.pack(side="top", fill="both", expand=1) 

        self.game_ribbon = tk.Frame(self.game_frame) 
        self.game_ribbon.pack(side="top", fill="x") 

        self.refresh_btn = ttk.Button(self.game_ribbon, text="Refresh") 
        self.refresh_btn.pack(side="right", padx=10) 
        self.refresh_btn.bind("<Button-1>", self.refresh_game)

        self.withdraw_btn = ttk.Button(self.game_ribbon, text="Withdraw", state='disabled') 
        self.withdraw_btn.pack(side="right", padx=10) 
        
        try:
            nicknames = [acct["nickname"] for acct in self.config['network']['rinkeby']['accounts']]
        except:
            nicknames = []
        
        self.accounts_dd = ttk.Combobox(self.game_ribbon, values=nicknames)
        self.accounts_dd.pack(side="left", padx=5)
        self.accounts_dd.bind("<<ComboboxSelected>>", self.set_account)

        self.balance_label = tk.Label(self.game_ribbon, text="Balance: ")
        self.balance_label.pack(side="left", padx=5)

        self.gf_row1_frame = tk.Frame(self.game_frame) 
        self.gf_row1_frame.pack(side="top", fill="x") 

        self.player1_label = tk.Label(self.gf_row1_frame, text="Player 1: ", fg="red")
        self.player1_label.pack(side="left", padx=5) 
        self.player1_vlabel = tk.Label(self.gf_row1_frame, text="") 
        self.player1_vlabel.pack(side="left", padx=5) 

        self.gf_row2_frame = tk.Frame(self.game_frame) 
        self.gf_row2_frame.pack(side="top", fill="x", pady=5)

        self.player2_label = tk.Label(self.gf_row2_frame, text="Player 2: ", fg="#de9726")
        self.player2_label.pack(side="left", padx=5)
        self.player2_vlabel = tk.Label(self.gf_row2_frame, text="") 
        self.player2_vlabel.pack(side="left", padx=5)

        self.gf_row3_frame = tk.Frame(self.game_frame) 
        self.gf_row3_frame.pack(side="top", fill="x", pady=5)       
        
        lmt_label = tk.Label(self.gf_row3_frame, text="Last Move: ")
        lmt_label.pack(side="left", padx=5)       
        self.lmt_vlabel = tk.Label(self.gf_row3_frame, text="")
        self.lmt_vlabel.pack(side="left", padx=5)

        self.claim_win_btn = ttk.Button(self.gf_row3_frame, text="Claim Win", state="disabled", width=30)
        self.claim_win_btn.pack(side="right", padx=10)
        
        self.move_btn = ttk.Button(self.gf_row3_frame, text="Move", state="disabled", width=30) 
        self.move_btn.pack(side="right", padx=5)

        self.gf_row4_frame = tk.Frame(self.game_frame) 
        self.gf_row4_frame.pack(side="top", fill="x", pady=5)   

        self.claim_refund_btn = ttk.Button(self.gf_row4_frame, text="Claim Refund", state="disabled", width=30)
        self.claim_refund_btn.pack(side="right", padx=10)

        cd_label = tk.Label(self.gf_row4_frame, text="Challenge Date: ")
        cd_label.pack(side="left", padx=5)       
        self.cd_vlabel = tk.Label(self.gf_row4_frame, text="")
        self.cd_vlabel.pack(side="left", padx=5)        

        self.accept_challenge_btn = ttk.Button(self.gf_row4_frame, text="Accept", state='disabled', width=30) 
        self.accept_challenge_btn.pack(side="right", padx=5)

        if render_setup:
            self.setup_app()
     
        self.protocol("WM_DELETE_WINDOW", lambda: self.save_config(destroy=True))
        self.after(1000, self.update_clock)

    def update_clock(self):
        now = datetime.now() 
        self.clock.config(text=str(now.strftime('%Y-%m-%d %H:%M:%S')))
        self.after(1000, self.update_clock)
    
    def datetime_from_timestamp(self, timestamp):
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def save_config(self, destroy=False):
        json.dump(self.config, open("config.json", "w"))
        if destroy == True:
            self.destroy()

    def setup_app(self):
        def save_settings(url=None, co=None, ac=None, m1=None, m2=None, w=None, dw=None, dr=None):       
            self.config['network']['rinkeby']['url'] = url 
            self.config['default_gas_values']['challengeOpponent'] = int(co)
            self.config['default_gas_values']['acceptChallenge'] = int(ac)
            self.config['default_gas_values']['move'] = int(m1)
            self.config['default_gas_values']['moveCFW'] = int(m2)
            self.config['default_gas_values']['withdraw'] = int(w)
            self.config['default_gas_values']['declareWinDueToOverstall'] = int(dw)            
            self.config['default_gas_values']['declareRefundDueToChallengeExpiration'] = int(dr)
            self.save_config()
            old_url = self.rinkeby_url
            if url != old_url:
                self.rinkeby_url = url 
            self.load_web3()
            popup.destroy()


        popup = tk.Toplevel(self)
        self.position_popup(popup, dimensions="400x900")

        network_frame = tk.Frame(popup)
        network_frame.pack(side="top", fill='both', expand=1, pady=10, padx=5)
        network_label = tk.Label(network_frame, text="Network Settings")
        network_label.pack(side="top")
        rinkeby_frame = tk.Frame(network_frame)
        rinkeby_frame.pack(side="top", fill='both', expand=1, pady=5)
        provider_frame = tk.Frame(rinkeby_frame)
        provider_frame.pack(side="top", fill="x", pady=10, padx=5)
        provider_label = tk.Label(provider_frame, text="HTTP Provider (url): ")
        provider_label.pack(side="left") 
        provider_entry = tk.Entry(provider_frame, width=50) 
        provider_entry.pack(side="left", padx=5)
        provider_entry.insert(0, self.config['network']['rinkeby']['url'])

        accts_frame = tk.Frame(rinkeby_frame)
        accts_frame.pack(side="top", fill='both', padx=10, pady=5)
        accts_top_frame = tk.Frame(accts_frame)
        accts_top_frame.pack(side="top", fill='x') 
        accts_label = tk.Label(accts_top_frame, text="Accounts")
        accts_label.pack(side="left") 
        add_acct_btn = ttk.Button(accts_top_frame, text="+", width=5) 
        add_acct_btn.pack(side="right", padx=10) 
        
        accts_box = tk.Listbox(accts_frame, height=10)
        for acct in self.config['network']['rinkeby']['accounts']:
            try:
                acct_str = "   |   ".join([str(v) for k,v in acct.items()])
            except Exception as e:
                acct_str = e
            accts_box.insert(tk.END, acct_str)
        
        accts_box.pack(side="top", fill='x', pady=5)
        add_acct_btn.bind("<Button-1>", lambda e: self.add_account(popup=popup, listbox=accts_box))

        gas_frame = tk.Frame(popup) 
        gas_frame.pack(side="top", fill="both", expand=1, pady=10)
        gas_label_frame = tk.Frame(gas_frame) 
        gas_label_frame.pack(side="top", fill="x", padx=5)
        gas_label = tk.Label(gas_label_frame, text="Default Gas Settings") 
        gas_label.pack(side="left") 
        co_gas_frame = tk.Frame(gas_frame) 
        co_gas_frame.pack(side="top", fill="x", pady=5) 
        co_gas_label = tk.Label(co_gas_frame, text="challengeOpponent: ") 
        co_gas_label.pack(side="left")
        co_gas_entry = tk.Entry(co_gas_frame, width=10) 
        co_gas_entry.pack(side="left", padx=5) 
        co_gas_entry.insert(0, self.config['default_gas_values']['challengeOpponent'])
        
        ac_gas_frame = tk.Frame(gas_frame) 
        ac_gas_frame.pack(side="top", fill="x", pady=5) 
        ac_gas_label = tk.Label(ac_gas_frame, text="acceptChallenge: ") 
        ac_gas_label.pack(side="left")
        ac_gas_entry = tk.Entry(ac_gas_frame, width=10) 
        ac_gas_entry.pack(side="left", padx=5)
        ac_gas_entry.insert(0, self.config['default_gas_values']['acceptChallenge'])

        m1_gas_frame = tk.Frame(gas_frame) 
        m1_gas_frame.pack(side="top", fill="x", pady=5) 
        m1_gas_label = tk.Label(m1_gas_frame, text="move: ") 
        m1_gas_label.pack(side="left")
        m1_gas_entry = tk.Entry(m1_gas_frame, width=10) 
        m1_gas_entry.pack(side="left", padx=5)
        m1_gas_entry.insert(0, self.config['default_gas_values']['move'])

        m2_gas_frame = tk.Frame(gas_frame) 
        m2_gas_frame.pack(side="top", fill="x", pady=5) 
        m2_gas_label = tk.Label(m2_gas_frame, text="move (check for win/tie): ") 
        m2_gas_label.pack(side="left")
        m2_gas_entry = tk.Entry(m2_gas_frame, width=10) 
        m2_gas_entry.pack(side="left", padx=5)
        m2_gas_entry.insert(0, self.config['default_gas_values']['moveCFW'])

        dw_gas_frame = tk.Frame(gas_frame) 
        dw_gas_frame.pack(side="top", fill="x", pady=5) 
        dw_gas_label = tk.Label(dw_gas_frame, text="declareWinDueToOverstall: ") 
        dw_gas_label.pack(side="left")
        dw_gas_entry = tk.Entry(dw_gas_frame, width=10) 
        dw_gas_entry.pack(side="left", padx=5)
        dw_gas_entry.insert(0, self.config['default_gas_values']['declareWinDueToOverstall'])        

        dr_gas_frame = tk.Frame(gas_frame) 
        dr_gas_frame.pack(side="top", fill="x", pady=5) 
        dr_gas_label = tk.Label(dr_gas_frame, text="declareRefundDueToChallengeExpiration: ") 
        dr_gas_label.pack(side="left")
        dr_gas_entry = tk.Entry(dr_gas_frame, width=10) 
        dr_gas_entry.pack(side="left", padx=5)
        dr_gas_entry.insert(0, self.config['default_gas_values']['declareRefundDueToChallengeExpiration'])  

        w_gas_frame = tk.Frame(gas_frame) 
        w_gas_frame.pack(side="top", fill="x", pady=5) 
        w_gas_label = tk.Label(w_gas_frame, text="withraw: ") 
        w_gas_label.pack(side="left")
        w_gas_entry = tk.Entry(w_gas_frame, width=10) 
        w_gas_entry.pack(side="left", padx=5)
        w_gas_entry.insert(0, self.config['default_gas_values']['withdraw'])

        btm_ribbon = tk.Frame(popup) 
        btm_ribbon.pack(side="bottom", fill="x") 
        submit_btn = ttk.Button(btm_ribbon, text="Save") 
        submit_btn.pack(side="right", padx=10) 
        submit_btn.bind("<Button-1>", lambda e: save_settings(
                url=provider_entry.get(), co=co_gas_entry.get(), ac=ac_gas_entry.get(), m1=m1_gas_entry.get(), m2=m2_gas_entry.get(),
                w=w_gas_entry.get(), dr=dr_gas_entry.get(), dw=dw_gas_entry.get()             
        ))
        cancel_btn = ttk.Button(btm_ribbon, text="Cancel", command=lambda: popup.destroy()) 
        cancel_btn.pack(side="right", padx=20) 

    def add_account(self, e=None, popup=None, listbox=None):
        def browse_for_privkey_file(e):
            file = askopenfile(mode='r') 
            if file is not None:
                keystore = json.loads(file.read()) 
                privkey_file_entry.config(state='normal')
                privkey_file_entry.insert(0, keystore)
                privkey_file_entry.config(state='disabled')      
        
        def save_account(nickname=None, password=None, keystore=None):       
            print("nn: ", nickname, " ; psswd: ", password, "privkfc: ", keystore)
            address = eval(keystore)['address']
            acct = {"nickname": nickname, "address": address, "password": password, "private_key": keystore}
            self.config["network"]["rinkeby"]["accounts"].append(acct)
            self.accounts_dd['values'] = (*self.accounts_dd['values'], nickname)        
            if listbox:
                acct_str = "   |   ".join([v for k,v in acct.items()])
                listbox.insert(tk.END, acct_str)
            child.destroy()

        child = tk.Toplevel(self)
        if popup:
            self.position_popup(child, parent=popup, dimensions="600x300")
        else:
            self.position_popup(child, dimensions="600x300")
        nickname_frame = tk.Frame(child) 
        nickname_frame.pack(side="top", fill='x', padx=5, pady=5) 
        nickname_label = tk.Label(nickname_frame, text="Nickname: ") 
        nickname_label.pack(side="left")
        nickname_entry = tk.Entry(nickname_frame, width=50) 
        nickname_entry.pack(side="left") 
        
        keystore = None 
        privkey_file_frame = tk.Frame(child)
        privkey_file_frame.pack(side="top", fill='x', pady=5)
        privkey_file_label = tk.Label(privkey_file_frame, text="Private Key File: ")
        privkey_file_label.pack(side="left")
        privkey_file_entry = tk.Entry(privkey_file_frame, width=50, state='disabled')
        privkey_file_entry.pack(side="left", padx=5)
        privkey_file_browse_btn = ttk.Button(privkey_file_frame, text="Browse")
        privkey_file_browse_btn.pack(side="right", padx=5)
        privkey_file_browse_btn.bind("<Button-1>", browse_for_privkey_file)
        psswd_frame = tk.Frame(child) 
        psswd_frame.pack(side="top", fill='x', pady=5)
        psswd_label = tk.Label(psswd_frame, text="Password: ") 
        psswd_label.pack(side="left")        
        psswd_entry = tk.Entry(psswd_frame, width=50)
        psswd_entry.pack(side="left", padx=5) 

        btm_ribbon = tk.Frame(child) 
        btm_ribbon.pack(side="bottom", fill="x") 
        submit_btn = ttk.Button(btm_ribbon, text="Save") 
        submit_btn.pack(side="right", padx=10) 
        submit_btn.bind("<Button-1>", lambda e: save_account(
                nickname=nickname_entry.get(), password=psswd_entry.get(), keystore=privkey_file_entry.get()
        ))
        cancel_btn = ttk.Button(btm_ribbon, text="Cancel", command=lambda: child.destroy()) 
        cancel_btn.pack(side="right", padx=20) 


    def position_popup(self, popup, parent=None, dimensions="400x500"):
        x = self.winfo_x()
        y = self.winfo_y()
        popup.wm_geometry(dimensions)           
        if parent:
            popup.lift(parent)
        else:
            popup.lift(self)
        

    def load_web3(self, init=False):
        if init == True:
            self.rinkeby_url = self.config['network']['rinkeby']['url']
        try:
            accounts = self.config['network']['rinkeby']['accounts']
        except KeyError:
            return True
        if self.rinkeby_url in ["", None] or accounts in [None, "", []]:
            return True 
        provider = Web3.HTTPProvider(self.rinkeby_url)
        self.w3 = Web3(provider)

        with open("abi.json") as f:
            abi = json.load(f)
        
        self.contract = self.w3.eth.contract(abi=abi, address="0xaB9d134F1D5c77531b50f458F733406d1312F293")
        # print(dir(self.contract.functions))

        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        self.w3.middleware_onion.add(middleware.simple_cache_middleware)

        numGames = self.contract.functions.numGames().call()
        # print("numGames: ", numGames)
        self.load_game_sb.config(to=numGames)
        return False  

    def refresh_game(self, e): 
        try:
            self.cancel_canvas_binds()
            self.get_game(self.current_game)
            self.load_game()
        except Exception as e:
            print("refresh error: ", e)

    def fill_slots_white(self):
        all_items = list(self.canvas.find_all())
        for item in all_items:
            if item not in self.taken_slots:
                self.canvas.itemconfig(item, fill='white')
    
    def on_canvas_hover(self, e):
        def set_target_slot(item):
            self.target_slot = item
            self.canvas.itemconfig(item, fill='green')
        
        x = self.canvas.canvasx(e.x) 
        y = self.canvas.canvasy(e.y) 

        self.fill_slots_white()
        column_items = list(self.canvas.find_overlapping(x, 0, x+1, 1000))
        
        if self.address == self.game_data[self.current_game]["player1"]:
            fill_color = "pink"
        else:
            fill_color = "yellow"
        
        empty_column = True 
        prev_item = None
        for item in column_items:
            if item not in self.taken_slots:
                self.canvas.itemconfig(item, fill=fill_color)
                prev_item = item
            else:
                if prev_item:
                    set_target_slot(prev_item)
                    empty_column = False 
             
        if empty_column == True and prev_item:
            set_target_slot(prev_item)

        if len(column_items) > 0:
            self.configure(cursor='hand1') 
            self.canvas.bind("<Button-1>", lambda e: self.commit_move())
        else:
            self.configure(cursor='arrow')
            self.canvas.unbind("<Button-1>")

    def cancel_canvas_binds(self, e=None):
        self.configure(cursor='arrow')
        self.canvas.unbind("<Enter>") 
        self.canvas.unbind("<Leave>")
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Button-1>")
        self.fill_slots_white()
        self.move_btn.config(text="Move") 
        players = [self.game_data[str(self.current_game)]["player1"], self.game_data[str(self.current_game)]["player2"]] 
        if players[int(self.game_data[str(self.current_game)]["whos_turn"]) - 1] == self.address:
            self.move_btn.config(state='normal') 
            self.move_btn.bind("<Button-1>", self.move)
        else:
            self.move_btn.config(state='disabled')
            self.move_btn.unbind("<Button-1>")

    def set_account(self, e):
        nickname = e.widget.get()
        acct = None 
        for acct in self.config['network']['rinkeby']['accounts']:
            if acct['nickname'] == nickname:
                addr = "0x" + acct["address"] 
                break 
        print("addr: ", addr)
        self.address = addr
        self.new_game_btn.config(state='normal')
        if self.current_game:
            self.refresh_game("")


    def load_game(self):
        game_index = int(self.load_game_sb.get()) - 1
        if game_index < 0:
            return 
        self.current_game = str(game_index)
        print("game_index: ", game_index)
        
        if str(game_index) not in list(self.game_data.keys()):
            self.get_game(game_index) 
        
        data = self.game_data[str(game_index)] 

        whos_turn = int(data["whos_turn"])
        if whos_turn == 1 and data["game_active"] == "1":
            p1_turn_str = " <--"
            p2_turn_str = ""
        elif whos_turn == 2 and data["game_active"] == "1":
            p1_turn_str = ""
            p2_turn_str = " <--"            
        else:
            p1_turn_str = ""
            p2_turn_str = ""

        lmt = int(data["last_move_time"])
        mst = int(data['max_stall_time'])
        cd = int(data["challenge_date"])
        acmt = int(data['accept_challenge_max_time'])

        self.player1_vlabel.config(text=data["player1"]+p1_turn_str) 
        self.player2_vlabel.config(text=data["player2"]+p2_turn_str) 
        lmt_str = self.datetime_from_timestamp(lmt)
        self.lmt_vlabel.config(text=lmt_str) 
        cd_str = self.datetime_from_timestamp(cd)
        self.cd_vlabel.config(text=cd_str)
    
        if self.address == data["player2"] and data["challenge_accepted"] == "0":
            self.accept_challenge_btn.config(state='normal')
            self.accept_challenge_btn.bind("<Button-1>", self.accept_challenge) 
        else:
            self.accept_challenge_btn.config(state='disabled')
            self.accept_challenge_btn.unbind("<Button-1>")
        
        players = [data["player1"], data["player2"]] 
        if players[whos_turn - 1] == self.address and data["challenge_accepted"] != "0" and data["winner"] not in players and data["game_active"] == "1":
            self.move_btn.config(state='normal') 
            self.move_btn.bind("<Button-1>", self.move)
        else:
            self.move_btn.config(state='disabled')
            self.move_btn.unbind("<Button-1>")

        if self.address == players[0]:
            self.player1_label.config(font="arial 12 bold")
            self.player2_label.config(font="arial 12")
        elif self.address == players[1]:
            self.player2_label.config(font="arial 12 bold")
            self.player1_label.config(font="arial 12")
        else:
            self.player2_label.config(font="arial 12")
            self.player1_label.config(font="arial 12")
        
        if data["winner"] == players[0]:
            self.player1_label.config(text="Player 1 (W):")
            self.player2_label.config(text="Player 2:")
        elif data['winner'] == players[1]:
            self.player1_label.config(text="Player 1:")
            self.player2_label.config(text="Player 2 (W):")
        elif data["tie_game"] == "1":
            self.player1_label.config(text="Player 1 (T):")
            self.player2_label.config(text="Player 2 (T):")
        else:
            self.player1_label.config(text="Player 1:")
            self.player2_label.config(text="Player 2:")           

        
        now = time()
        
        if data["game_active"] == "1":
            self.withdraw_btn.config(state='disabled')
            self.withdraw_btn.unbind("<Button-1>") 
            if data["challenge_accepted"] == '1':
                cr_str = " (Accepted)"
                cr_state = "disabled"
                self.claim_refund_btn.unbind("<Button-1>")
            elif data["challenge_accepted"] == '0' and players[1] == self.address:
                cr_str = " (P1 Only)"
                cr_state = "disabled"
                self.claim_refund_btn.unbind("<Button-1>")
            elif data["challenge_accepted"] == '0' and players[0] == self.address:
                if cd + acmt < now:
                    cr_str = ""
                    cr_state = "normal"
                    self.claim_refund_btn.bind("<Button-1>", self.claim_refund)
                else:
                    cr_str = "(" + self.datetime_from_timestamp(cd + acmt) + ")"
                    cr_state = "disabled"
                    self.claim_refund_btn.unbind("<Button-1>")
            else:
                cr_str = ""
                cr_state = "disabled"             
                self.claim_refund_btn.unbind("<Button-1>")
                     
            if (data['whos_turn'] == '1' and players[0] == self.address) or (data['whos_turn'] == '2' and players[1] == self.address):
                cwb_str = "(Your Turn)"
                cwb_state = "disabled"
                self.move_btn.config(text=f"Move (by {self.datetime_from_timestamp(lmt + mst)})")
                self.claim_win_btn.unbind("<Button-1>")
            elif (data['whos_turn'] == '2' and players[0] == self.address) or (data['whos_turn'] == '1' and players[1] == self.address):
                if lmt + mst < now and data['challenge_accepted'] == '1':
                    cwb_str = ""
                    cwb_state = "normal"
                    self.claim_win_btn.bind("<Button-1>", self.claim_win)
                    self.move_btn.config(text=f"Move (deadline passed)")
                else:
                    cwb_str = "(" + self.datetime_from_timestamp(cd + mst) + ")"
                    cwb_state = "disabled"
                    self.claim_win_btn.unbind("<Button-1>")
                    if data["challenge_accepted"] == '1':
                        self.move_btn.config(text=f"Move (by {self.datetime_from_timestamp(lmt + mst)})")
                    else:
                        self.move_btn.config(text=f"Move (challenge must be accepted first)")
            else:
                cwb_str = ""
                cwb_state = 'disabled'
                self.claim_win_btn.unbind("<Button-1>")
                self.move_btn.config(text=f"Move (by {self.datetime_from_timestamp(lmt + mst)})")
        else:
            cr_str = ""
            cr_state = "disabled"
            cwb_str = ""
            cwb_state = "disabled"
            self.claim_win_btn.unbind("<Button-1>")
            self.claim_refund_btn.unbind("<Button-1>")
            self.move_btn.config(text=f"Move")
            if (self.address == players[0] and int(data["p1_returns"]) > 0) or (self.address == players[1] and int(data["p2_returns"]) > 0):
                self.withdraw_btn.config(state='normal')
                self.withdraw_btn.bind("<Button-1>", self.withdraw_pending_returns)
            else:
                self.withdraw_btn.config(state='disabled')
                self.withdraw_btn.unbind("<Button-1>")                

        self.claim_win_btn.config(text="Claim Win " + cwb_str, state=cwb_state)
        self.claim_refund_btn.config(text="Claim Refund " + cr_str, state=cr_state)

        self.taken_slots = []

        for label, item in self.ovals.items():
            slot_vacancy = self.game_data[self.current_game]["board_state"][label] 
            if slot_vacancy == "1":
                self.canvas.itemconfig(item, fill="red")
                self.taken_slots.append(item)
            elif slot_vacancy == "2":
                self.canvas.itemconfig(item, fill="#de9726")
                self.taken_slots.append(item)
            elif slot_vacancy == "0":
                self.canvas.itemconfig(item, fill="white")

        try:
            balance = self.w3.eth.getBalance(Web3.toChecksumAddress(self.address))
        except TypeError:
            balance = "--"
        
        self.balance_label.config(text=f"Balance: {balance}")
    
    def get_game(self, game_index):
        result1 = self.contract.functions.getGameDetails(int(game_index)).call() 
        rdict = {"board_state": {}, "last_move_time": None, "whos_turn": 0, "max_stall_time": 0, "accept_challenge_max_time": 0, 
                    "p1_ante": 0, "p2_ante": 0, "player1": None, "player2": None, "challenge_date": 0, "challenge_accepted": 0, "game_active": 0, 
                    "tie_game": 0, "winner": None, "p1_returns": 0, "p2_returns": 0}
        r1split = result1.split("|") 
        board_state_split = r1split[0].split(";") 
        for item in board_state_split:
            try:
                values = item.split(":")
                if "BoardState" in values:
                    values = values[1:]
                rdict["board_state"][values[0]] = values[1] 
            except:
                continue 
        last_move_time = r1split[1]
        label, value = last_move_time.split(":") 
        rdict["last_move_time"] = value 
        whos_turn = r1split[2]
        label, value = whos_turn.split(":") 
        rdict["whos_turn"] = value 
        tie_game = r1split[3] 
        label, value = tie_game.split(":") 
        rdict["tie_game"] = value

        max_stall_time = r1split[4] 
        label, value = max_stall_time.split(":") 
        rdict["max_stall_time"] = value 

        accept_challenge_max_time = r1split[5]
        label, value = accept_challenge_max_time.split(":") 
        rdict["accept_challenge_max_time"] = value 

        p1_ante = r1split[6] 
        label, value = p1_ante.split(":") 
        rdict["p1_ante"] = value 

        p2_ante = r1split[7] 
        label, value = p1_ante.split(":") 
        rdict["p2_ante"] = value

        result2 = self.contract.functions.getGameAbstract(int(game_index)).call()

        r2split = result2.split("|") 
        players = r2split[0] 
        label, values = players.split(":") 
        player_vals = values.split(",") 
        rdict["player1"] = player_vals[0] 
        rdict["player2"] = player_vals[1] 

        challenge_date = r2split[1] 
        label, value = challenge_date.split(":") 
        rdict["challenge_date"] = value 

        challenge_accepted = r2split[2] 
        label, value = challenge_accepted.split(":") 
        rdict["challenge_accepted"] = value 

        game_active = r2split[3] 
        label, value = game_active.split(":") 
        rdict["game_active"] = value 
        
        winner = r2split[4] 
        label, value = winner.split(":")
        rdict["winner"] = value 
        
        p1_returns = r2split[5] 
        label, value = p1_returns.split(":") 
        rdict["p1_returns"] = value 

        p2_returns = r2split[6] 
        label, value = p2_returns.split(":") 
        rdict["p2_returns"] = value
        
        # print("data: ", rdict)

        self.game_data[f"{game_index}"] = rdict

    
    def new_game(self, e): 
        popup = tk.Toplevel(self) 
        self.position_popup(popup)

        from_frame = tk.Frame(popup) 
        from_frame.pack(side="top", pady=20, padx=5, fill="x") 
        from_label = tk.Label(from_frame, text=f"From: {self.address}") 
        from_label.pack(side="left") 

        opp_frame = tk.Frame(popup) 
        opp_frame.pack(side="top", pady=20, padx=5, fill="x") 
        opp_label = tk.Label(opp_frame, text="Opponent: ") 
        opp_label.pack(side="left") 
        opp_entry = tk.Entry(opp_frame, width=50) 
        opp_entry.pack(side="left", padx=10)        

        turn_frame = tk.Frame(popup) 
        turn_frame.pack(side="top", pady=20, padx=5, fill="x") 
        turn_label = tk.Label(turn_frame, text="Who's Turn (1 or 2): ") 
        turn_label.pack(side="left") 
        turn_entry = tk.Entry(turn_frame, width=50) 
        turn_entry.pack(side="left", padx=10)

        ante_frame = tk.Frame(popup) 
        ante_frame.pack(side="top", pady=20, padx=5, fill="x") 
        ante_label = tk.Label(ante_frame, text="Ante amount: ") 
        ante_label.pack(side="left") 
        ante_entry = tk.Entry(ante_frame, width=50) 
        ante_entry.pack(side="left", padx=10)

        mt2ac_frame = tk.Frame(popup) 
        mt2ac_frame.pack(side="top", pady=20, padx=5, fill="x") 
        mt2ac_label = tk.Label(mt2ac_frame, text="Max Time to accept Challenge: ") 
        mt2ac_label.pack(side="left") 
        mt2ac_entry = tk.Entry(mt2ac_frame, width=50) 
        mt2ac_entry.pack(side="left", padx=10)

        mt2s_frame = tk.Frame(popup) 
        mt2s_frame.pack(side="top", pady=20, padx=5, fill="x") 
        mt2s_label = tk.Label(mt2s_frame, text="Max Time to Move: ") 
        mt2s_label.pack(side="left") 
        mt2s_entry = tk.Entry(mt2s_frame, width=50) 
        mt2s_entry.pack(side="left", padx=10)

        btm_ribbon = tk.Frame(popup) 
        btm_ribbon.pack(side="bottom", fill="x") 
        submit_btn = ttk.Button(btm_ribbon, text="Submit") 
        submit_btn.pack(side="right", padx=10) 
        submit_btn.bind("<Button-1>", lambda e: self.challenge_opponent(
                opponent=opp_entry.get(), turn=turn_entry.get(), ante_amount=ante_entry.get(), 
                mt2ac=mt2ac_entry.get(), mt2s=mt2s_entry.get(), popup=popup
        ))
        cancel_btn = ttk.Button(btm_ribbon, text="Cancel", command=lambda: popup.destroy()) 
        cancel_btn.pack(side="right", padx=20) 

    def accept_challenge(self, e):
        popup = tk.Toplevel(self) 
        self.position_popup(popup)

        from_frame = tk.Frame(popup) 
        from_frame.pack(side="top", pady=20, padx=5, fill="x") 
        from_label = tk.Label(from_frame, text="From: ") 
        from_label.pack(side="left") 
        from_vlabel = tk.Label(from_frame, width=50, text=self.address) 
        from_vlabel.pack(side="left", padx=10)

        gi_frame = tk.Frame(popup) 
        gi_frame.pack(side="top", pady=20, padx=5, fill="x") 
        gi_label = tk.Label(gi_frame, text="Game Index: ") 
        gi_label.pack(side="left") 
        gi_vlabel = tk.Label(gi_frame, width=50, text=self.current_game) 
        gi_vlabel.pack(side="left", padx=10)          

        gaslimit_frame = tk.Frame(popup) 
        gaslimit_frame.pack(side="top", pady=20, padx=5, fill="x") 
        gaslimit_label = tk.Label(gaslimit_frame, text="Gas Limit: ") 
        gaslimit_label.pack(side="left") 
        gaslimit_entry = tk.Entry(gaslimit_frame, width=50) 
        gaslimit_entry.pack(side="left", padx=10)

        password_frame = tk.Frame(popup) 
        password_frame.pack(side="top", pady=20, padx=5, fill="x") 
        password_label = tk.Label(password_frame, text="Password: ") 
        password_label.pack(side="left") 
        password_entry = tk.Entry(password_frame, width=50) 
        password_entry.pack(side="left", padx=10)        
        
        ante_amount = self.game_data[self.current_game]["p1_ante"]
        aa_frame = tk.Frame(popup) 
        aa_frame.pack(side="top", pady=20, padx=5, fill="x") 
        aa_label = tk.Label(aa_frame, text=f"Required Ante Amount: {ante_amount}") 
        aa_label.pack(side="left")         

        btm_ribbon = tk.Frame(popup) 
        btm_ribbon.pack(side="bottom", fill="x") 
        submit_btn = ttk.Button(btm_ribbon, text="Submit") 
        submit_btn.pack(side="right", padx=10) 
        submit_btn.bind("<Button-1>", lambda e: self.accept_challenge_submit(
                from_=self.address, game_index=int(self.current_game), password=password_entry.get(), 
                gas_limit=gaslimit_entry.get(), popup=popup, ante_amount=ante_amount
        ))
        cancel_btn = ttk.Button(btm_ribbon, text="Cancel", command=lambda: popup.destroy()) 
        cancel_btn.pack(side="right", padx=20)     
    
    def challenge_opponent(self, **kwargs):
        checksum_address = Web3.toChecksumAddress(self.address)     
        opponent_address = Web3.toChecksumAddress(kwargs['opponent'])
        gas = self.contract.functions.challengeOpponent(opponent_address, int(kwargs['turn']), 
                                                                int(kwargs['mt2ac']), int(kwargs['mt2s'])).estimateGas({'from': checksum_address})

        data = self.contract.encodeABI(fn_name="challengeOpponent", args=[opponent_address, int(kwargs['turn']),
                                                                int(kwargs['mt2ac']), int(kwargs['mt2s'])])
 
        gas = 3000000
        value = Web3.toHex(int(kwargs['ante_amount']))
        self.handle_transaction(checksum_address, gas, data, value=value, popup=kwargs['popup'])

    def move(self, e):
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        e.widget.config(text="Cancel") 
        e.widget.unbind("<Button-1>") 
        e.widget.bind("<Button-1>", self.cancel_canvas_binds)

    def commit_move(self, **kwargs):
        def four_in_row_or_tie():
            tie = True 
            bs = self.game_data[self.current_game]["board_state"] 
            coordinate = None 
            print("target slot: ", self.target_slot)
            for k,v in self.ovals.items():
                if v == self.target_slot:
                    coordinate = k 
                    break 
            
            bs[coordinate] = int(self.game_data[self.current_game]["whos_turn"])
            taken_by_p1 = 0
            taken_by_p2 = 0
            empty_slots = 0

            # check verticals 
            for i in range(1, 8):
                for ii in range(3):
                    taken_by_p1 = 0
                    taken_by_p2 = 0
                    empty_slots = 0
                    combo = [f"{i},{ii+1}",f"{i},{ii+2}",f"{i},{ii+3}",f"{i},{ii+4}"]
                    for slot in combo:
                        # print("slot type: ", type(int(bs[slot])))
                        if int(bs[slot]) == 1:
                            taken_by_p1 += 1
                        elif int(bs[slot]) == 2:
                            taken_by_p2 += 1
                        else:
                            empty_slots += 1
                    if taken_by_p1 == 4:
                        return True 
                    elif taken_by_p2 == 4:
                        return True 
                    elif (taken_by_p1 >= 1 and taken_by_p2 == 0) or (taken_by_p2 >= 1 and taken_by_p1 == 0):
                        tie = False 

            # check horizs 
            for i in range(1, 7):
                for ii in range(1, 5):
                    taken_by_p1 = 0
                    taken_by_p2 = 0
                    empty_slots = 0
                    combo = [f"{ii},{i}",f"{ii+1},{i}",f"{ii+2},{i}",f"{ii+3},{i}"]
                    for slot in combo:
                        if int(bs[slot]) == 1:
                            taken_by_p1 += 1
                        elif int(bs[slot]) == 2:
                            taken_by_p2 += 1
                        else:
                            empty_slots += 1
                    if taken_by_p1 == 4:
                        return True 
                    elif taken_by_p2 == 4:
                        return True 
                    elif (taken_by_p1 >= 1 and taken_by_p2 == 0) or (taken_by_p2 >= 1 and taken_by_p1 == 0):
                        tie = False                                         

            # check slopes 
            possible_4inrow_startcoords = {"1": [[1,3],[4,1],[1,4],[4,6]], 
                                            "2": [[1,2], [3,1], [1,5], [3,6]], 
                                            "3": [[1,1], [2,1], [1,6], [2,6]]}
            for k,v in possible_4inrow_startcoords.items():
                for i in range(int(k)):
                    for ii, sc in enumerate(v):
                        taken_by_p1 = 0
                        taken_by_p2 = 0
                        empty_slots = 0
                        if ii <= 1:                   
                            combo = [f"{sc[0]+i},{sc[1]+i}",f"{sc[0]+i+1},{sc[1]+i+1}",f"{sc[0]+i+2},{sc[1]+i+2}",f"{sc[0]+i+3},{sc[1]+i+3}"]
                        else:
                            combo = [f"{sc[0]+i},{sc[1]-i}",f"{sc[0]+i+1},{sc[1]-i-1}",f"{sc[0]+i+2},{sc[1]-i-2}",f"{sc[0]+i+3},{sc[1]-i-3}"]
                        for slot in combo:
                            if int(bs[slot]) == 1:
                                taken_by_p1 += 1
                            elif int(bs[slot]) == 2:
                                taken_by_p2 += 1
                            else:
                                empty_slots += 1
                        if taken_by_p1 == 4:
                            return True 
                        elif taken_by_p2 == 4:
                            return True 
                        elif (taken_by_p1 >= 1 and taken_by_p2 == 0) or (taken_by_p2 >= 1 and taken_by_p1 == 0):
                            tie = False


            return tie 
   
        slot_coordinate = None 
        for label, slot in self.ovals.items():
            if slot == self.target_slot:
                slot_coordinate = label 
        
        self.cancel_canvas_binds()
        
        column, row = slot_coordinate.split(",") 

        checksum_address = Web3.toChecksumAddress(self.address)      
        
        check_for_win_or_tie = four_in_row_or_tie()
        # print("check for win/tie? ", check_for_win_or_tie)
        try:
            gas = self.contract.functions.move(int(column), int(self.current_game), check_for_win_or_tie).estimateGas({'from': checksum_address})
        except:
            if check_for_win_or_tie == True:
                move_func = "moveCFW"
            else:
                move_func = "move"
            gas = self.config['default_gas_values'][move_func]

        data = self.contract.encodeABI(fn_name="move", args=[int(column), int(self.current_game), check_for_win_or_tie])

        self.handle_transaction(checksum_address, gas, data)

    def accept_challenge_submit(self, **kwargs):
        
        checksum_address = Web3.toChecksumAddress(self.address)     

        try:
            gas = self.contract.functions.acceptChallenge(kwargs['game_index']).estimateGas({'from': checksum_address})
        except ValueError:
            gas = self.config['default_gas_values']['acceptChallenge']
        
        data = self.contract.encodeABI(fn_name="acceptChallenge", args=[kwargs['game_index']])

        value = Web3.toHex(int(kwargs['ante_amount']))
        self.handle_transaction(checksum_address, gas, data, value=value, popup=kwargs['popup'])
        
        
    def claim_win(self, e):
        checksum_address = Web3.toChecksumAddress(self.address)     
        
        gas = self.contract.functions.declareWinDueToOverstall(int(self.current_game)).estimateGas({'from': checksum_address})

        data = self.contract.encodeABI(fn_name="declareWinDueToOverstall", args=[int(self.current_game)])

        self.handle_transaction(checksum_address, gas, data)



    def claim_refund(self, e):
        checksum_address = Web3.toChecksumAddress(self.address)      
        
        try:
            gas = self.contract.functions.declareRefundDueToChallengeExpiration(int(self.current_game)).estimateGas({'from': checksum_address})
        except:
            gas = self.config['default_gas_values']['declareRefundDueToChallengeExpiration']

        data = self.contract.encodeABI(fn_name="declareRefundDueToChallengeExpiration", args=[int(self.current_game)])

        self.handle_transaction(checksum_address, gas, data)


    def withdraw_pending_returns(self, e):
        checksum_address = Web3.toChecksumAddress(self.address)     
        try:
            gas = self.contract.functions.withdraw(int(self.current_game)).estimateGas({'from': checksum_address})
        except:
            gas = self.config['default_gas_values']['withdraw']

        data = self.contract.encodeABI(fn_name="withdraw", args=[int(self.current_game)])

        self.handle_transaction(checksum_address, gas, data)        

    def handle_transaction(self, checksum_address, gas, data, value=None, popup=None):
        if not value:
            value = Web3.toHex(0)
        
        tr = {'to': self.contract.address, 
                'value': value, 
                'gas': Web3.toHex(gas), 
                'gasPrice': Web3.toHex(self.w3.eth.gasPrice), 
                'nonce': Web3.toHex(self.w3.eth.getTransactionCount(checksum_address)),
                'data': data
                }
        

        privkey = None 
        password = None 
        for acct in self.config['network']['rinkeby']['accounts']:
            if self.address == "0x" + acct['address']:
                privkey = acct['private_key']
                password = acct['password']
                break 

        privkey = self.w3.eth.account.decrypt(privkey, password)
        signed = w3.eth.account.signTransaction(tr, Web3.toHex(privkey))
        tx = self.w3.eth.sendRawTransaction(signed.rawTransaction)
        # print("tx_hash: ", tx)
        if popup:
            popup.destroy()

        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx)
        # print("tx_receipt: ", tx_receipt)

        self.render_receipt(tx_receipt)

    
    def render_receipt(self, tx_receipt):
        def close_receipt_popup(e):
            self.refresh_game("")
            popup.destroy()
        
        popup = tk.Toplevel(self)
        self.position_popup(popup, dimensions="400x500") 
        receipt_label = tk.Label(popup, text="Receipt") 
        receipt_label.pack(side="top", pady=10) 
        txt_box = tk.Text(popup)
        txt_box.pack(side="top", fill='both', expand=1, padx=5, pady=5)
        txr_txt = str(tx_receipt.__dict__) 
        txt_box.insert('1.0', txr_txt)
        txt_box.config(state='disabled')

        ok_btn = ttk.Button(popup, text="Ok") 
        ok_btn.pack(side="bottom") 
        ok_btn.bind("<Button-1>", close_receipt_popup)


if __name__ == '__main__':
    app = Connect4Dapp()
    app.mainloop()
