import csv, io, sqlite3, tkinter as tk
from tkinter import ttk, messagebox as mb, filedialog, simpledialog
from collections import Counter
from pathlib import Path
import database as db
import security, intelligence, mailer

BG='#111827'; PANEL='#1f2937'; FG='#f9fafb'; MUTED='#cbd5e1'; BLUE='#6366f1'

class App:
    def __init__(self):
        db.setup()
        self.root=tk.Tk();self.root.title('CineMind AI — интеллектуальный каталог фильмов');self.root.geometry('1160x730');self.root.minsize(850,570)
        self.root.configure(bg=BG)
        style=ttk.Style();style.theme_use('clam')
        style.configure('Treeview',background=PANEL,foreground=FG,fieldbackground=PANEL,rowheight=29,borderwidth=0)
        style.configure('Treeview.Heading',background='#374151',foreground=FG,font=('Segoe UI',10,'bold'))
        style.map('Treeview',background=[('selected',BLUE)])
        style.configure('TCombobox',padding=5)
        self.user=None;self.selected=set();self.last_report='';self.main_login()
    def clear(self):
        for item in self.root.winfo_children():item.destroy()
    def frame(self,parent=None,**kw):return tk.Frame(parent or self.root,bg=kw.pop('bg',BG),**kw)
    def label(self,parent,text,size=11,color=FG,bold=False,**kw):
        return tk.Label(parent,text=text,fg=color,bg=parent.cget('bg'),font=('Segoe UI',size,'bold' if bold else 'normal'),**kw)
    def btn(self,parent,title,command,primary=False):
        return tk.Button(parent,text=title,command=command,bg=BLUE if primary else '#374151',fg='white',activebackground='#4f46e5',activeforeground='white',relief='flat',cursor='hand2',padx=12,pady=9,font=('Segoe UI',10,'bold'))
    def entry(self,parent,show=None,width=32):
        return tk.Entry(parent,show=show, width=width,relief='flat',font=('Segoe UI',11),bg='#f8fafc',fg='#111827',insertbackground='#111827')
    def show_error(self,e):mb.showerror('Ошибка',str(e))
    def run(self,func):
        try:return func()
        except (ValueError,sqlite3.Error,RuntimeError, OSError) as e:self.show_error(e)
    def field(self,parent,title,show=None,value=''):
        self.label(parent,title,color=MUTED).pack(anchor='w',pady=(9,3))
        e=self.entry(parent,show=show);e.pack(fill='x',ipady=7)
        if value:e.insert(0,value)
        return e
    def main_login(self):
        self.user=None;self.clear()
        outer=self.frame();outer.pack(expand=True)
        self.label(outer,'CINEMIND AI',30,bold=True).pack(pady=(0,5))
        self.label(outer,'Интеллектуальный каталог фильмов',12,color=MUTED).pack(pady=(0,20))
        email=self.field(outer,'Электронная почта');pwd=self.field(outer,'Пароль','*')
        def enter():
            def action():self.user=security.login(email.get(),pwd.get());db.log(self.user['id'],'Вход');self.dashboard()
            self.run(action)
        self.btn(outer,'Войти',enter,True).pack(fill='x',pady=(18,6))
        self.btn(outer,'Создать аккаунт',self.register_window).pack(fill='x',pady=3)
        self.btn(outer,'Забыли пароль?',self.forgot_window).pack(fill='x',pady=3)
        pwd.bind('<Return>',lambda _:enter())
    def popup(self,title):
        win=tk.Toplevel(self.root);win.title(title);win.configure(bg=BG);win.geometry('430x530');win.transient(self.root);win.grab_set();return win
    def register_window(self):
        w=self.popup('Регистрация');f=self.frame(w);f.pack(fill='both',expand=True,padx=35,pady=25)
        self.label(f,'Регистрация',19,bold=True).pack()
        n=self.field(f,'Имя и фамилия');e=self.field(f,'Email');p=self.field(f,'Пароль (8+ символов)','*');c=self.field(f,'Повторите пароль','*')
        def done():
            def action():
                uid=security.register(n.get(),e.get(),p.get(),c.get());db.log(uid,'Регистрация');mb.showinfo('Готово','Аккаунт создан. Войдите в приложение.');w.destroy()
            self.run(action)
        self.btn(f,'Зарегистрироваться',done,True).pack(fill='x',pady=20)
    def forgot_window(self):
        w=self.popup('Восстановление пароля');f=self.frame(w);f.pack(fill='both',expand=True,padx=30,pady=22)
        self.label(f,'Сброс пароля',18,bold=True).pack()
        email=self.field(f,'Ваш email');code=self.field(f,'Код из письма');pwd=self.field(f,'Новый пароль','*')
        def send_code():
            def action():
                token=security.generate_reset(email.get())
                try:mailer.send(email.get(),'CineMind AI: восстановление пароля',f'Ваш код: {token}. Действует 10 минут.')
                except Exception as ex:
                    # Не отображать код в интерфейсе или логах.
                    self.show_error('Не удалось отправить письмо. Настройте SMTP и запросите новый код. '+str(ex));return
                mb.showinfo('Код отправлен','Проверьте вашу почту.')
            self.run(action)
        def reset():
            def action():security.reset_password(email.get(),code.get(),pwd.get());w.destroy();mb.showinfo('Успешно','Пароль изменён.')
            self.run(action)
        self.btn(f,'Отправить код на почту',send_code).pack(fill='x',pady=12)
        self.btn(f,'Изменить пароль',reset,True).pack(fill='x',pady=8)
    def dashboard(self,section='Каталог'):
        if not self.user:return self.main_login()
        self.clear();wrapper=self.frame();wrapper.pack(fill='both',expand=True)
        side=self.frame(wrapper,bg=PANEL,width=205);side.pack(side='left',fill='y');side.pack_propagate(False)
        self.label(side,'CINEMIND AI',19,bold=True).pack(pady=(25,18))
        for name in ['Каталог','Избранное','ИИ-рекомендации','Сравнение','Статистика','История','Отчёты','Профиль']:
            self.btn(side,name,lambda name=name:self.dashboard(name),name==section).pack(fill='x',padx=13,pady=5)
        self.btn(side,'Выйти',self.logout).pack(side='bottom',fill='x',padx=13,pady=20)
        content=self.frame(wrapper);content.pack(side='left',fill='both',expand=True,padx=23,pady=20)
        self.label(content,section,23,bold=True).pack(anchor='w',pady=(0,17))
        try:getattr(self,'page_'+{'Каталог':'catalog','Избранное':'favorites','ИИ-рекомендации':'ai','Сравнение':'compare','Статистика':'stats','История':'history','Отчёты':'reports','Профиль':'profile'}[section])(content)
        except (sqlite3.Error,ValueError) as e:self.show_error(e)
    def logout(self):
        db.log(self.user['id'],'Выход');self.selected.clear();self.user=None;self.main_login()
    def table(self,parent,cols,widths=None,height=12):
        f=self.frame(parent);f.pack(fill='both',expand=True,pady=8)
        tree=ttk.Treeview(f,columns=cols,show='headings',height=height,selectmode='extended')
        for i,col in enumerate(cols):tree.heading(col,text=col);tree.column(col,width=(widths or [140]*len(cols))[i],anchor='w')
        sc=ttk.Scrollbar(f,orient='vertical',command=tree.yview);tree.configure(yscrollcommand=sc.set)
        tree.pack(side='left',fill='both',expand=True);sc.pack(side='right',fill='y');return tree
    def movie_toolbar(self,f,load):
        row=self.frame(f);row.pack(fill='x')
        q=self.entry(row,width=29);q.pack(side='left',padx=(0,8),ipady=6)
        genre=ttk.Combobox(row,values=['Все','Фантастика','Драма','Боевик','Комедия','Мультфильм','Триллер','Мелодрама'],width=14,state='readonly');genre.set('Все');genre.pack(side='left',padx=5)
        sort=ttk.Combobox(row,values=['Рейтинг ↓','Рейтинг ↑','Год ↓','Год ↑','Название'],width=13,state='readonly');sort.set('Рейтинг ↓');sort.pack(side='left',padx=5)
        self.btn(row,'Найти',lambda:load(q.get(),genre.get(),sort.get())).pack(side='left',padx=6)
        q.bind('<Return>',lambda e:load(q.get(),genre.get(),sort.get()))
        return q,genre,sort
    def page_catalog(self,f):
        status=self.label(f,'Каталог: добавляйте, редактируйте, удаляйте и ищите фильмы',10,color=MUTED);status.pack(anchor='w',pady=(0,10))
        tree=self.table(f,('ID','Фильм','Год','Жанр','Рейтинг','Минут','Описание'),[45,180,60,110,65,65,250])
        # toolbar deliberately comes above table by pack order; controls are accessible below table.
        bar=self.frame(f);bar.pack(fill='x',pady=4)
        q=self.entry(bar, width=22);q.pack(side='left',ipady=6,padx=4)
        g=ttk.Combobox(bar,values=['Все','Фантастика','Драма','Боевик','Комедия','Мультфильм','Триллер','Мелодрама'],width=13,state='readonly');g.set('Все');g.pack(side='left',padx=4)
        s=ttk.Combobox(bar,values=['Рейтинг ↓','Рейтинг ↑','Год ↓','Год ↑','Название'],width=12,state='readonly');s.set('Рейтинг ↓');s.pack(side='left',padx=4)
        def load():
            tree.delete(*tree.get_children());rows=db.movies(q.get(),g.get(),s.get())
            for m in rows:tree.insert('', 'end',iid=str(m['id']),values=tuple(m[key] for key in ['id','title','year','genre','rating','duration','description']))
            status.configure(text=f'Найдено фильмов: {len(rows)}')
            db.log(self.user['id'],'Поиск',q.get()+' / '+g.get()+' / '+s.get())
        self.btn(bar,'Поиск',load,True).pack(side='left',padx=4);q.bind('<Return>',lambda _:load())
        buttons=self.frame(f);buttons.pack(fill='x',pady=8)
        def selected_id():
            if not tree.selection():raise ValueError('Сначала выберите фильм.')
            return int(tree.selection()[0])
        def form(edit=False):
            def action():
                movie=None
                if edit:
                    mid=selected_id()
                    with db.connect() as c:movie=c.execute('SELECT * FROM movies WHERE id=?',(mid,)).fetchone()
                w=self.popup('Редактировать фильм' if edit else 'Добавить фильм');w.geometry('450x650');body=self.frame(w);body.pack(fill='both',expand=True,padx=25,pady=14)
                fields={}
                for key,label in [('title','Название'),('year','Год'),('genre','Жанр'),('rating','Рейтинг (0–10)'),('duration','Длительность (мин)'),('description','Описание')]:fields[key]=self.field(body,label,value=str(movie[key]) if movie else '')
                def save():
                    def inner():
                        values=(fields['title'].get().strip(),int(fields['year'].get()),fields['genre'].get().strip(),float(fields['rating'].get()),int(fields['duration'].get()),fields['description'].get().strip())
                        if not all([values[0],values[2],values[5]]) or not(1880<=values[1]<=2100) or not(0<=values[3]<=10) or values[4]<=0:raise ValueError('Проверьте название, жанр, описание, год, рейтинг и длительность.')
                        with db.connect() as c:
                            if edit:c.execute('UPDATE movies SET title=?,year=?,genre=?,rating=?,duration=?,description=? WHERE id=?',values+(mid,))
                            else:c.execute('INSERT INTO movies(title,year,genre,rating,duration,description) VALUES(?,?,?,?,?,?)',values)
                        db.log(self.user['id'],'Редактирование фильма' if edit else 'Создание фильма',values[0]);w.destroy();load();mb.showinfo('Успех','Данные сохранены.')
                    self.run(inner)
                self.btn(body,'Сохранить',save,True).pack(fill='x',pady=18)
            self.run(action)
        def delete():
            def action():
                mid=selected_id()
                if mb.askyesno('Подтверждение','Удалить выбранный фильм?'):
                    with db.connect() as c:c.execute('DELETE FROM movies WHERE id=?',(mid,))
                    db.log(self.user['id'],'Удаление фильма',str(mid));load()
            self.run(action)
        def favorite():
            def action():
                mid=selected_id()
                with db.connect() as c:c.execute('INSERT OR IGNORE INTO favorites VALUES(?,?)',(self.user['id'],mid))
                db.log(self.user['id'],'Добавлено в избранное',str(mid));mb.showinfo('Готово','Фильм добавлен в избранное.')
            self.run(action)
        def select_compare():
            def action():self.selected.update(map(int,tree.selection()));mb.showinfo('Сравнение',f'Выбрано фильмов: {len(self.selected)}. Перейдите в раздел «Сравнение».')
            self.run(action)
        for title,fun in [('Добавить',lambda:form()),('Изменить',lambda:form(True)),('Удалить',delete),('★ Избранное',favorite),('⇄ К сравнению',select_compare)]:self.btn(buttons,title,fun).pack(side='left',padx=3)
        load()
    def page_favorites(self,f):
        with db.connect() as c:rows=c.execute('SELECT m.* FROM movies m JOIN favorites fav ON m.id=fav.movie_id WHERE fav.user_id=? ORDER BY rating DESC',(self.user['id'],)).fetchall()
        tree=self.table(f,('ID','Название','Жанр','Рейтинг'),[45,240,150,90])
        for m in rows:tree.insert('','end',iid=str(m['id']),values=(m['id'],m['title'],m['genre'],m['rating']))
        def remove():
            if not tree.selection():return mb.showwarning('Выбор','Выберите фильм.')
            mid=int(tree.selection()[0]);self.run(lambda:self._remove_favorite(mid))
        self.btn(f,'Удалить из избранного',remove).pack(anchor='w')
    def _remove_favorite(self,mid):
        with db.connect() as c:c.execute('DELETE FROM favorites WHERE user_id=? AND movie_id=?',(self.user['id'],mid))
        db.log(self.user['id'],'Удалено из избранного',str(mid));self.dashboard('Избранное')
    def page_ai(self,f):
        self.label(f,'Текстовый анализ TF-IDF: описание + жанр + ваши избранные фильмы.',11,color=MUTED).pack(anchor='w')
        q=self.field(f,'Что хотите посмотреть? Например: космос приключения любовь');
        tree=self.table(f,('Фильм','Жанр','Рейтинг','Балл','Объяснение'),[180,110,70,70,350],9)
        def recommend():
            def action():
                with db.connect() as c:ids=[r[0] for r in c.execute('SELECT movie_id FROM favorites WHERE user_id=?',(self.user['id'],))]
                data=intelligence.recommend(q.get(),ids)
                tree.delete(*tree.get_children())
                for m,score,why in data:tree.insert('','end',values=(m['title'],m['genre'],m['rating'],f'{score:.3f}',why))
                db.log(self.user['id'],'ИИ-поиск',q.get()+' → '+', '.join(x[0]['title'] for x in data[:3]))
            self.run(action)
        self.btn(f,'Получить рекомендации',recommend,True).pack(anchor='w',pady=9)
        self.label(f,'Ограничение: TF-IDF сопоставляет слова и интересы, но не понимает смысл как большая языковая модель.\nБалл — комбинированный показатель сходства и рейтинга, а не вероятность.',10,color=MUTED,justify='left').pack(anchor='w',pady=10)
        recommend()
    def page_compare(self,f):
        self.label(f,'Выберите 2–5 фильмов в каталоге кнопкой «К сравнению».',11,color=MUTED).pack(anchor='w',pady=4)
        self.label(f,'Метод взвешенной суммы: рейтинг 50%, новизна 30%, короткая длительность 20%.',10,color=MUTED).pack(anchor='w',pady=4)
        tree=self.table(f,('Место','Фильм','Рейтинг','Год','Минуты','Итоговый балл','Формула'),[50,170,70,70,70,100,310],10)
        def calculate():
            def action():
                if len(self.selected)<2:raise ValueError('Выберите как минимум 2 фильма.')
                with db.connect() as c:
                    ids=sorted(self.selected);films=c.execute('SELECT * FROM movies WHERE id IN ('+','.join('?'*len(ids))+')',ids).fetchall()
                ranks=intelligence.compare(films)
                tree.delete(*tree.get_children())
                for pos,(m,score,why) in enumerate(ranks,1):tree.insert('','end',values=(pos,m['title'],m['rating'],m['year'],m['duration'],f'{score:.2f}/100',why))
                self.last_report='Сравнение фильмов\n'+'\n'.join(f'{pos}. {m["title"]}: {score:.2f} — {why}' for pos,(m,score,why) in enumerate(ranks,1))
                db.log(self.user['id'],'Сравнение',self.last_report[:500]);mb.showinfo('Результат',f'Лучший вариант: {ranks[0][0]["title"]} ({ranks[0][1]:.2f}/100)')
            self.run(action)
        bar=self.frame(f);bar.pack(fill='x')
        self.btn(bar,'Сравнить',calculate,True).pack(side='left',padx=5)
        self.btn(bar,'Сбросить выбор',lambda:(self.selected.clear(),tree.delete(*tree.get_children()))).pack(side='left',padx=5)
        self.label(f,f'В списке сравнения сейчас: {len(self.selected)}',10,color=MUTED).pack(anchor='w',pady=14)
    def page_stats(self,f):
        rows=list(db.movies());count=len(rows)
        if not count:return self.label(f,'Нет фильмов').pack()
        avg=sum(m['rating'] for m in rows)/count
        genres=Counter(m['genre'] for m in rows)
        self.label(f,f'Всего фильмов: {count}     Средний рейтинг: {avg:.2f}     Жанров: {len(genres)}',15,bold=True).pack(anchor='w',pady=15)
        canvas=tk.Canvas(f,bg=PANEL,highlightthickness=0,height=360);canvas.pack(fill='x',pady=10)
        def draw(event=None):
            canvas.delete('all');w=max(canvas.winfo_width(),400);mx=max(genres.values(),default=1)
            for i,(genre,n) in enumerate(genres.most_common()):
                y=15+i*40;length=(w-225)*n/mx
                canvas.create_text(15,y+13,text=genre,fill=FG,anchor='w',font=('Segoe UI',10))
                canvas.create_rectangle(140,y,140+length,y+27,fill=BLUE,outline='')
                canvas.create_text(150+length,y+13,text=str(n),fill=FG,anchor='w')
        canvas.bind('<Configure>',draw)
        tree=self.table(f,('Жанр','Количество','Доля'),[200,130,120],5)
        for genre,n in genres.most_common():tree.insert('','end',values=(genre,n,f'{n/count:.1%}'))
        db.log(self.user['id'],'Просмотр статистики')
    def page_history(self,f):
        b=self.frame(f);b.pack(fill='x')
        query=self.entry(b,width=28);query.pack(side='left',ipady=6,padx=6)
        tree=self.table(f,('Дата','Действие','Подробности'),[150,190,480],14)
        def refresh():
            with db.connect() as c:rows=c.execute('SELECT * FROM history WHERE user_id=? AND (action LIKE ? OR detail LIKE ?) ORDER BY id DESC LIMIT 400',(self.user['id'],f'%{query.get()}%',f'%{query.get()}%')).fetchall()
            tree.delete(*tree.get_children())
            for r in rows:tree.insert('','end',values=(r['created_at'],r['action'],r['detail']))
        self.btn(b,'Искать в истории',refresh).pack(side='left');query.bind('<Return>',lambda _:refresh());refresh()
    def report_text(self):
        films=db.movies();genres=Counter(m['genre'] for m in films)
        lines=['CineMind AI — Отчёт по каталогу',f'Всего фильмов: {len(films)}',f'Средний рейтинг: {sum(m["rating"] for m in films)/len(films):.2f}' if films else 'Нет фильмов','Жанры: '+', '.join(f'{k} ({v})' for k,v in genres.items()),'','Список фильмов:']
        lines += [f"{m['title']} ({m['year']}), {m['genre']}, рейтинг {m['rating']}, {m['duration']} мин" for m in films]
        if self.last_report:lines+=['','Последнее сравнение:',self.last_report]
        return '\n'.join(lines)
    def page_reports(self,f):
        self.label(f,'Отчёт формируется из текущей базы данных и последнего сравнения.',11,color=MUTED).pack(anchor='w',pady=8)
        text=tk.Text(f,wrap='word',bg=PANEL,fg=FG,insertbackground=FG,font=('Consolas',10),height=20)
        text.pack(fill='both',expand=True,pady=8)
        report=self.report_text();text.insert('1.0',report)
        bar=self.frame(f);bar.pack(fill='x')
        def save():
            filename=filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Текстовый отчёт','*.txt'),('CSV','*.csv')])
            if not filename:return
            def action():
                if filename.lower().endswith('.csv'):
                    with open(filename,'w',newline='',encoding='utf-8-sig') as fh:
                        writer=csv.writer(fh);writer.writerow(['ID','Название','Год','Жанр','Рейтинг','Минуты','Описание'])
                        for m in db.movies():writer.writerow([m[x] for x in ['id','title','year','genre','rating','duration','description']])
                else:Path(filename).write_text(text.get('1.0','end-1c'),encoding='utf-8')
                db.log(self.user['id'],'Экспорт',Path(filename).name);mb.showinfo('Сохранено',filename)
            self.run(action)
        def email():
            dest=simpledialog.askstring('Отправка отчёта','Email получателя:',parent=self.root)
            if dest is None:return
            if not security.valid_email(dest):return self.show_error('Неверный адрес электронной почты.')
            def action():mailer.send(dest,'CineMind AI — отчёт',text.get('1.0','end-1c'));db.log(self.user['id'],'Отправка отчёта',dest);mb.showinfo('Успех','Отчёт отправлен.')
            self.run(action)
        self.btn(bar,'Сохранить TXT / CSV',save,True).pack(side='left',padx=5)
        self.btn(bar,'Отправить отчёт по email',email).pack(side='left',padx=5)
    def page_profile(self,f):
        with db.connect() as c:user=c.execute('SELECT * FROM users WHERE id=?',(self.user['id'],)).fetchone()
        box=self.frame(f);box.pack(anchor='w',fill='x')
        name=self.field(box,'Имя',value=user['name']);email=self.field(box,'Email',value=user['email'])
        def update():
            def action():
                n=name.get().strip();e=email.get().strip().lower()
                if not n or not security.valid_email(e):raise ValueError('Проверьте имя и email.')
                with db.connect() as c:c.execute('UPDATE users SET name=?,email=? WHERE id=?',(n,e,self.user['id']))
                self.user['name']=n;self.user['email']=e;db.log(self.user['id'],'Обновление профиля');mb.showinfo('Успех','Профиль обновлён.')
            self.run(action)
        self.btn(box,'Сохранить профиль',update,True).pack(anchor='w',pady=15)
        self.label(box,'Смена пароля',17,bold=True).pack(anchor='w',pady=10)
        old=self.field(box,'Старый пароль','*');new=self.field(box,'Новый пароль','*')
        def update_pw():
            def action():security.change_password(self.user['id'],old.get(),new.get());db.log(self.user['id'],'Смена пароля');old.delete(0,'end');new.delete(0,'end');mb.showinfo('Успех','Пароль изменён.')
            self.run(action)
        self.btn(box,'Изменить пароль',update_pw).pack(anchor='w',pady=14)
    def start(self):self.root.mainloop()

if __name__=='__main__':App().start()
