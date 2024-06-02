from GUI import app
import tkinter as tk
from tkinter import ttk


def main():
    # # Заранее заданный словарь с данными
    #
    # # Создание главного окна
    # root = tk.Tk()
    # root.title("Таблица с данными")
    #
    # # Создание стиля для таблицы
    # style = ttk.Style()
    #
    # style.theme_use("default")
    #
    # style.configure("Treeview",
    #                 background="#2a2d2e",
    #                 foreground="white",
    #                 rowheight=30,
    #                 fieldbackground="#343638",
    #                 bordercolor="#343638",
    #                 borderwidth=0,
    #                 font=(None, 15))
    # style.map('Treeview', background=[('selected', '#22559b')])
    #
    # style.configure("Treeview.Heading",
    #                 background="#565b5e",
    #                 foreground="white",
    #                 relief="flat",
    #                 font=(None, 18, "bold"))
    #
    # style.map("Treeview.Heading",
    #           background=[('active', '#3484F0')])
    #
    # tree = ttk.Treeview(root, columns=('Value 1', 'Value 2', 'Value 3'), show='headings', style="Treeview")
    # tree.grid(sticky="nsew")
    #
    # tree.heading('Value 1', text='Value 1')
    # tree.heading('Value 2', text='Value 2')
    # tree.heading('Value 3', text='Value 3')
    #
    # tree.insert('', "end", values=["aaaaa", "bbbbbb", "cccccc"], tags=("odd",))
    # tree.insert('', "end", values=["aaaaa", "bbbbbb", "cccccc"], tags=("even",))
    # tree.insert('', "end", values=["aaaaa", "bbbbbb", "cccccc"], tags=("odd",))
    #
    # tree.tag_configure("odd", foreground="black", background="lightgrey")
    # tree.tag_configure("even", foreground="black", background="white")
    #
    # root.mainloop()

    appl = app.App()
    appl.mainloop()


if __name__ == "__main__":
    main()
