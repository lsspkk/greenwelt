import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
SELECTED_FILE = os.path.join(os.path.dirname(__file__), 'selected.json')
IMAGES_PER_PAGE = 20

class ImageSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Image Selector')
        self.geometry('1400x900')
        self.selected = set()
        self.page = 0
        # Load images from selected.json if it exists, else use all images in downloads
        if os.path.exists(SELECTED_FILE):
            with open(SELECTED_FILE, 'r') as f:
                self.images = json.load(f)
            # Filter to only images that actually exist in downloads
            self.images = [f for f in self.images if os.path.exists(os.path.join(DOWNLOADS_DIR, f))]
        else:
            self.images = [f for f in os.listdir(DOWNLOADS_DIR)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            self.images.sort()
        self.image_labels = []
        self.check_vars = []
        self.create_widgets()
        self.show_page()

    def create_widgets(self):
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.pack(fill=tk.X, pady=10)
        self.prev_btn = ttk.Button(self.nav_frame, text='Previous', command=self.prev_page)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        self.next_btn = ttk.Button(self.nav_frame, text='Next', command=self.next_page)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        self.save_btn = ttk.Button(self.nav_frame, text='Save Selection', command=self.save_selection)
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        self.page_label = ttk.Label(self.nav_frame, text='')
        self.page_label.pack(side=tk.LEFT, padx=10)

    def show_page(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.image_labels.clear()
        self.check_vars.clear()
        start = self.page * IMAGES_PER_PAGE
        end = start + IMAGES_PER_PAGE
        page_images = self.images[start:end]
        self.page_label.config(text=f'Page {self.page + 1} / {max(1, (len(self.images) - 1) // IMAGES_PER_PAGE + 1)}')
        for idx, filename in enumerate(page_images):
            img_path = os.path.join(DOWNLOADS_DIR, filename)
            try:
                img = Image.open(img_path)
                img.thumbnail((160, 160))
                photo = ImageTk.PhotoImage(img)
            except Exception:
                continue
            var = tk.BooleanVar(value=filename in self.selected)
            chk = ttk.Checkbutton(self.frame, variable=var, command=lambda f=filename, v=var: self.toggle_select(f, v))
            lbl = ttk.Label(self.frame, image=photo, text=filename, compound='top')
            lbl.image = photo
            # Bind click event to label to toggle selection
            def on_label_click(event, f=filename, v=var):
                v.set(not v.get())
                self.toggle_select(f, v)
            lbl.bind('<Button-1>', on_label_click)
            # 5 images per row, 2 columns per image (image+checkbox)
            row = idx // 5
            col_img = (idx % 5) * 2
            col_chk = col_img + 1
            lbl.grid(row=row, column=col_img, padx=10, pady=10)
            chk.grid(row=row, column=col_chk, padx=2, pady=10)
            self.image_labels.append(lbl)
            self.check_vars.append(var)

    def toggle_select(self, filename, var):
        if var.get():
            self.selected.add(filename)
        else:
            self.selected.discard(filename)

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.show_page()

    def next_page(self):
        if (self.page + 1) * IMAGES_PER_PAGE < len(self.images):
            self.page += 1
            self.show_page()

    def save_selection(self):
        with open(SELECTED_FILE, 'w') as f:
            json.dump(sorted(self.selected), f, indent=2)
        self.quit()

if __name__ == '__main__':
    app = ImageSelector()
    app.mainloop()
