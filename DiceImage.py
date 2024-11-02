from PIL import Image
from PIL import ImageDraw, ImageFont

class DiceImage():
    def __init__(self, bg_path="./font/bg.jpg", font_path="./font/Casino3DLinesMarquee.ttf", dice_game_image_path="./game_state.jpg", ledger_font_path="./font/timesnewroman.ttf", ledger_image_path="./ledger.png"):
        self.bg=Image.open(bg_path)
        self.font_path=font_path
        self.border=20
        self.dice_game_image_path=dice_game_image_path
        self.ledger_font_path=ledger_font_path
        self.ledger_image_path=ledger_image_path
        
    def generate_number(self, number: int):
        image = self.bg.copy()
        width, height = image.size
        # Initialize the drawing context
        draw = ImageDraw.Draw(image)

        # Define the text and font
        text = str(number)
        if number==0:
            text="ROLL"
        font_size = 300
        font = ImageFont.truetype(self.font_path, font_size)

        # Calculate text position to center it
        text_width, text_height = draw.textsize(text, font=font)
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2

        # Draw the text on the image
        text_color = (0, 0, 0)  # Black
        draw.text((text_x, text_y), text, fill=text_color, font=font)
        
        image=self.overlay(Image.new('RGB', (width+self.border*2, height+self.border*2), (235, 232, 52)), image)
        
        return image
        
    def overlay(self, bg, im):
        
        base_image = bg.convert("RGBA")
        paste_image = im.convert("RGBA")

        base_image.paste(paste_image, (int(base_image.size[0]//2-paste_image.size[0]//2), int(base_image.size[1]//2-paste_image.size[1]//2)))
        
        return base_image
    
    
    def header(self, text, font_size, text_color=(0,0,0)):
        width, height=self.border*2+self.bg.size[0], 100
        # Initialize the drawing context
        background_color = (255, 255, 255)  # White
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)
        #font = ImageFont.truetype(self.font_path, font_size)
        font = ImageFont.truetype(self.font_path, font_size)
        # Calculate text position to center it
        text_width, text_height = draw.textsize(text, font=font)
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2

        draw.text((text_x, text_y), text, fill=text_color, font=font)
        
        return image
        
    def dice_game_image(self, roll, round_num, stake, player_names, scores, turn):
        if scores[0]==scores[1]:
            score_msg="SCORE TIED AT "+str(scores[0])
        elif scores[0]>scores[1]:
            score_msg=player_names[0]+" WINNING BY "+str(scores[0])
        else: 
            score_msg=player_names[1]+" WINNING BY "+str(scores[1])
        board=self. generate_number(roll)
        round_header=self.header("DICE ROLL ROUND "+str(round_num), 100)
        score_header=self.header(score_msg, 70)
        stake_header=self.header("Current Bet: "+str(stake), 70)
        images=[score_header, stake_header, board]
        if roll==1:
            images.append(self.header(player_names[(turn+1)%2]+" Lost", 90))
        else:
            images.append(self.header(player_names[turn]+"'s turn", 100))
        output=round_header
        for im in images:
            output=self.concat_images(output, im, "below")
        w,h=output.size
        output=output.resize((int(w//2), int(h//2)), Image.ANTIALIAS)
        output.save(self.dice_game_image_path)
        return output
    
    def cell(self, width, height, text, border):
        background_color = (255, 249, 219)
        border_color=(173, 171, 158)
        text_color=(0,0,0)
        
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.ledger_font_path, height)
        draw.text((0,0), text, fill=text_color, font=font)
        
        image=self.overlay(Image.new('RGB', (width+border*2, height+border*2), border_color), image)
        
        return image
    
    def ledger_image(self, name, ledger_dict, avatar_image):
        border_w=2
        header_h=30
        entry_h=20
        particular_w=150
        debt_w=100
        credit_w=100
        whole_w=particular_w+debt_w+credit_w+border_w*4
        avatar_height=int(header_h*1.5+border_w*2)
        name_row=self.list_concat([avatar_image.resize((avatar_height, avatar_height), Image.Resampling.LANCZOS),
                                  self.cell(whole_w-avatar_height, avatar_height-border_w*2, name, border_w)],
                                 "right")
        
        header_row=self.list_concat(
            [self.cell(particular_w, header_h,"Particular", border_w), 
             self.cell(debt_w, header_h,"Debt", border_w), 
             self.cell(credit_w, header_h,"Credit", border_w)], "right")
        value_rows=[]
        total_debt, total_credit=0,0
        for key, value in ledger_dict.items():
            if value>0:
                credit=value
                debt=0
                total_credit+=credit
            elif value<0:
                credit=0
                debt=value*-1
                total_debt+=debt
            else:
                debt, credit=0,0
                
            value_rows.append(self.list_concat(
            [self.cell(particular_w, entry_h, str(key), border_w), 
             self.cell(debt_w, entry_h,str(debt), border_w), 
             self.cell(credit_w, entry_h,str(credit), border_w)], "right"))
        
        total_row=self.list_concat(
            [self.cell(particular_w, header_h,"Total", border_w), 
             self.cell(debt_w, header_h, str(total_debt), border_w), 
             self.cell(credit_w, header_h,str(total_credit), border_w)], "right")
        
        worth_row=self.cell(whole_w, header_h, "Net Worth: "+str(total_credit-total_debt), border_w)
        
        table=self.list_concat([name_row, header_row]+value_rows+[total_row,worth_row], "below")
        
        table.save(self.ledger_image_path)
        return table
    
    def list_concat(self, images, direction):
        if len(images)>0:
            output=images[0]
            for im in images[1:]:
                output=self.concat_images(output, im, direction)
            return output
        else:
            return None
        
    def concat_images(self, im1, im2, direction, bg_color=(0,0,0)):
        if direction=="above":
            return self.concat_images(im2, im1, "below", bg_color)
        elif direction=="left":
            return self.concat_images(im2, im1, "right", bg_color)
        elif direction=="right":
            background=Image.new(mode="RGB", size=(im1.size[0]+im2.size[0],max(im1.size[1],im2.size[1])), color=bg_color)
            Image.Image.paste(background, im1, (0,0))
            Image.Image.paste(background, im2, (im1.size[0],0))
            return background
        elif direction=="below":
            background=Image.new(mode="RGB", size=(max(im1.size[0],im2.size[0]),im1.size[1]+im2.size[1]), color=bg_color)
            Image.Image.paste(background, im1, (0,0))
            Image.Image.paste(background, im2, (0,im1.size[1]))
            return background
        else:
            print("Incorrect direction: Pick from [below, above, right, left]")
            return None