import base64
from datetime import datetime
from os import mkdir
from tkinter import Tk, filedialog, Frame, messagebox, PhotoImage, Label, Entry, IntVar, Radiobutton, StringVar, messagebox, Toplevel, Scale, HORIZONTAL, NORMAL, DISABLED
#from tkinter.ttk import *
from tkinter.ttk import Button, Combobox
import urllib.request

import cv2
import numpy as np
from PIL import ImageTk, Image
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileName, FileType, FileContent, Disposition

def connect(host='http://google.com'):
    try:
        urllib.request.urlopen(host)
        return True
    except:
        return False

class GreenScreen(object):
    def __init__(self):
        self.root = Tk()
        self.root.wm_title('HVGB Green Screen Editor')
        self.lower_green = np.array([0, 80, 0])
        self.upper_green = np.array([120, 255, 150])
        self.lower_blue = np.array([0, 0, 50])  # This was set due to the new light setup. slider can change that
        self.upper_blue = np.array([120, 150, 255])
        self.has_internet = connect()
        self.blue_green = IntVar(self.root,1)
        self.send_email = IntVar(self.root, 1)
        self.name_var = StringVar()
        self.email_var = StringVar()
        self.portrait_land = IntVar(self.root, 0)
        self.landscape_bg = StringVar()
        self.lower_bound = IntVar()
        self.lower_bound.set(self.lower_blue[2])
        try:
            with open('new_key.txt', 'r') as key_mat:
                key = key_mat.readlines()[0].strip()
            self.sg = SendGridAPIClient(key)
        except FileNotFoundError:  # key is not available
            self.has_internet = False
        if not self.has_internet:
            self.send_email = 2

    def run(self):
        self.make_gui()
        self.root.mainloop()

    def set_key(self):
        try:
            with open('new_key.txt', 'r') as key_mat:
                key = key_mat.readlines()[0].strip()
            self.sg = SendGridAPIClient(key)
            return True
        except FileNotFoundError:  # key is not downloaded
            return False

    def check_internet(self):
        if connect():
            if self.set_key():
                self.has_internet = True
            else:
                self.has_internet = False
        else:
            self.has_internet = False
        if not self.has_internet:
            self.send_email = 2
            self.send_email_button.state = DISABLED
            self.send_email_button.grid(row=3, column=0)
            self.no_email_button.state = DISABLED
            self.no_email_button.grid(row=3, column=1)
            self.auto_delivery = Label(self.root, text='CANNOT do auto-delivery', fg='red')
            self.auto_delivery.grid(row=0, column=1)
        else:
            self.send_email_button.state = NORMAL
            self.send_email_button.grid(row=3, column=0)
            self.no_email_button.state = NORMAL
            self.no_email_button.grid(row=3, column=1)
            self.auto_delivery = Label(self.root, text='Can do auto-delivery')
            self.auto_delivery.grid(row=0, column=1)

    def set_lower_bound(self, val):
        if self.blue_green.get() == 1:
            self.lower_blue = np.array([0, 0, val])
            print(self.lower_blue)
        elif self.blue_green.get() == 2:
            self.lower_green = np.array([0, val, 0])
            print(self.lower_green)
    
    def set_slider(self):
        if self.blue_green.get() == 1:
            self.lower_bound.set(self.lower_blue[2])
        elif self.blue_green.get() == 2:
            self.lower_bound.set(self.lower_green[1])

    def choice_popup(self):
        if self.portrait_land.get():
            win = Toplevel()
            win.wm_title('Select Background')
            l = Label(win, text="Select your background")
            l.grid(row=0, column=0)
            box = Combobox(win, textvariable=self.landscape_bg)
            box['values'] = ['cemetery.jpg', 'cemeteryillustration.jpg', 'Ecto-1.jpg', 'ghostsgraveyard.jpg', 'HauntedMansion.jpg', 'HauntedMansion_Int.jpg', 'LavaForest.jpg']
            box['state'] = 'readonly'
            box.grid(row=1, column=0)
            b = Button(win, text='Okay', command=win.destroy)
            b.grid(row=2, column=0)
            self.root.wait_window(win)
        self.do_greenscreen()

    def select_input_file(self):
        file_types = (
            ('images', '*.jpg'),
            ('images', '*.png'),
            ('All files', '*.*')
        )
        self.filename = filedialog.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=file_types
        )
        image = Image.open(self.filename)
        image.thumbnail((500,400))
        image.save('thumbnails/thumbnail.png')
        self.input_image = ImageTk.PhotoImage(image.rotate(90))
        self.input_image_label = Label(self.root, image=self.input_image)
        self.input_image_label.grid(row=1, column=0)
        #self.input_image = PhotoImage(file=self.filename)
        #self.input_image_label = Label(self.root, image=self.input_image)
        #self.input_image_label.grid(row=1, column=0)

    def do_email(self, dirname, filename, name, email):
        message = Mail(
            from_email='photos@hudsonvalleyghostbusters.org',
            to_emails=email,
            subject='Photo from Hudson Valley Ghostbusters!',
            html_content='''
                Hi {0},<br>Please enjoy the attached photo from the Hudson Valley Ghostbusters!
            '''.format(name)
        )
        with open('{0}/{1}_ghostbusters.jpg'.format(dirname, filename), 'rb') as img:
            data = img.read()
        encoded_file = base64.b64encode(data).decode()
        attached_file = Attachment(
            FileContent(encoded_file),
            FileName('{0}_ghostbusters.jpg'.format(filename)),
            FileType('image/jpg'),
            Disposition('attachment')
        )
        message.attachment = attached_file
        try:
            response = self.sg.send(message)
            print(response.status_code, response.body, response.headers)
        except Exception as e:
            print(e.message)
            messagebox.showinfo('Error!', 'Oops, could not send email. Please try manually')
            
    def do_greenscreen(self):
        if not self.name_var.get() or not self.email_var.get():
            messagebox.showinfo("Error!", "Please check that both name and email are filled in")
            return
        image = cv2.imread(self.filename)
        if self.portrait_land.get():
            background = cv2.imread('backgrounds/' + self.landscape_bg.get())
        else:
            background = cv2.imread('backgrounds/GhostBustersBackground.jpg')
        height, width, colors = image.shape
        bg_height, bg_width, bg_colors = background.shape
        image_copy = np.copy(image)
        image_copy = cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB)
        background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
        if bg_width > width:
            background = cv2.resize(background, (width, height))
        if self.blue_green.get() == 1:
            mask = cv2.inRange(image_copy, self.lower_blue, self.upper_blue)
        else:
            mask = cv2.inRange(image_copy, self.lower_green, self.upper_green)
        masked_image = np.copy(image_copy)
        masked_image[mask != 0] = [0,0,0]
        background[mask == 0] = [0, 0, 0]
        dirname = "D:/" + self.name_var.get().replace(' ', '_') + datetime.now().strftime("__%Y_%m_%d__%H_%M_%S")
        #dirname = self.name_var.get().replace(' ', '_') + datetime.now().strftime("__%Y_%m_%d__%H_%M_%S")
        mkdir(dirname)
        name = self.name_var.get()
        email = self.email_var.get()
        with open('{0}/info.txt'.format(dirname), 'w') as output_text:
            output_text.write('Name: {0}\n'.format(name))
            output_text.write('Email: {0}\n'.format(email))
        filename = self.name_var.get().split()[0]
        cv2.imwrite('{0}/{1}_ghostbusters.jpg'.format(dirname, self.name_var.get().split()[0]), cv2.cvtColor(background + masked_image, cv2.COLOR_RGB2BGR))
        if self.has_internet and self.send_email.get() == 1:
            self.do_email(dirname, filename, name, email)
        #image = Image.open('{0}/{1}_ghostbusters.jpg'.format(dirname, filename))
        #image.thumbnail((500,400))
        #image.save('D:/thumbnails/thumbnail.png')
        #self.output_image = ImageTk.PhotoImage(image)
        #self.output_image_label = Label(self.root, image=self.input_image)
        #self.input_image_label.grid(row=3, column=0)
        #vigo_background = cv2.imread('vigo_background.jpg')
        #vigo_background = cv2.cvtColor(vigo_background, cv2.COLOR_BGR2RGB)
        #v_height, v_width, v_colors = vigo_background.shape
        #if height > v_height and width > v_width:
        #    # crop the input picture
        #    cropped_image = cv2.resize(image_copy, (v_width, v_height))
        #    # get center of width
        #    #diff_width = width - v_width
        #    #half_diff_width = int(diff_width/2)
        #    #r_width = width - half_diff_width
        #    #bottom = height - v_height
        #    #cropped_image = cropped_image[half_diff_width:r_width, bottom:v_height]
        #    mask = cv2.inRange(cropped_image, self.lower_green, self.upper_green)
        #    masked_image = np.copy(cropped_image)
        ##    masked_image[mask != 0] = [0,0,0]
        #    vigo_background[mask == 0] = [0,0,0]
        #    dirname = self.name_var.get().replace(' ', '') + datetime.now().strftime("__%Y_%m_%d__%H_%M_%S")
        #    mkdir(dirname)
        #    with open('{0}/info.txt'.format(dirname), 'w') as output_text:
        #        output_text.write('Name: {0}\n'.format(self.name_var.get()))
        #        output_text.write('Email: {0}\n'.format(self.email_var.get()))
        #    cv2.imwrite('{0}/vigo.jpg'.format(dirname), cv2.cvtColor(vigo_background + masked_image, cv2.COLOR_RGB2BGR)) 
            
    def make_gui(self):
        #self.root.geometry("1500x1500")
        page = Frame(self.root)
        open_button = Button(self.root, text='Open file', command=self.select_input_file)
        open_button.grid(row=0, column=0)
        if self.has_internet:
            text = 'Can do auto-delivery'
        else:
            text = 'CANNOT do auto-delivery'
        if self.has_internet:
            self.auto_delivery = Label(self.root, text=text)
        else:
            self.auto_delivery = Label(self.root, text=text, fg='red')
        self.auto_delivery.grid(row=0, column=1)
        internet_button = Button(self.root, text='Check internet', command=self.check_internet)
        internet_button.grid(row=0, column=2)
        image = Image.open('logo.jpg')
        image.thumbnail((200,200))
        image.save('logo_thumnbail.png')
        self.input_image = ImageTk.PhotoImage(image)
        self.input_image_label = Label(self.root, image=self.input_image)
        self.input_image_label.grid(row=1, column=0)
        #self.input_image = ImageTk.PhotoImage(Image.open('logo.jpg'))
        #self.input_image = ImageTk.PhotoImage(image)
        #self.input_image_label = Label(self.root, image=self.input_image)
        #self.input_image_label.grid(row=1, column=0)
        sub_frame = Frame(self.root)
        sub_frame.grid(row=1, column=1)
        name_label = Label(sub_frame, text='Name: ')
        name_label.grid(row=0, column=0)
        email_label = Label(sub_frame, text='Email: ')
        email_label.grid(row=1, column=0)
        self.name_entry = Entry(sub_frame, textvariable=self.name_var)
        self.email_entry = Entry(sub_frame, textvariable=self.email_var)
        self.name_entry.grid(row=0, column=1)
        self.email_entry.grid(row=1, column=1)
        Radiobutton(sub_frame, text='Blue Screen', variable=self.blue_green, value=1, command=self.set_slider).grid(row=2, column=0)
        Radiobutton(sub_frame, text='Green Screen', variable=self.blue_green, value=2, command=self.set_slider).grid(row=2, column=1)
        self.send_email_button = Radiobutton(sub_frame, text='Send Email', variable=self.send_email, value=1, state=NORMAL if self.has_internet else DISABLED)
        self.send_email_button.grid(row=3, column=0)
        self.no_email_button = Radiobutton(sub_frame, text="Don't Send Email", variable=self.send_email, value=2, state=NORMAL if self.has_internet else DISABLED)
        self.no_email_button.grid(row=3, column=1)
        Radiobutton(sub_frame, text='Portrait', variable=self.portrait_land, value=0).grid(row=4, column=0)
        Radiobutton(sub_frame, text='Landscape', variable=self.portrait_land, value=1).grid(row=4, column=1)
        Scale(sub_frame, label='Lower bound', variable=self.lower_bound, command=self.set_lower_bound, from_=20, to=100, orient=HORIZONTAL, resolution=5).grid(row=5, columnspan=2)
        edit_button = Button(self.root, text='Do greenscreen magic', command=self.choice_popup)
        edit_button.grid(row=2, column=0)

GreenScreen().run()
