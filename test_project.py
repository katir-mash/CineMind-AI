import os, tempfile, unittest
from pathlib import Path
import database as db, security, intelligence

class ProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();db.DB=Path(cls.tmp.name)/'test.db';db.setup()
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_seed_and_crud(self):
        self.assertGreaterEqual(len(db.movies()),18)
        with db.connect() as c:
            mid=c.execute('INSERT INTO movies(title,year,genre,rating,duration,description) VALUES(?,?,?,?,?,?)',('Тест',2024,'Драма',7.5,110,'Тестирование')).lastrowid
            c.execute('UPDATE movies SET rating=? WHERE id=?',(8.5,mid))
            self.assertEqual(c.execute('SELECT rating FROM movies WHERE id=?',(mid,)).fetchone()[0],8.5)
            c.execute('DELETE FROM movies WHERE id=?',(mid,))
            self.assertIsNone(c.execute('SELECT id FROM movies WHERE id=?',(mid,)).fetchone())
    def test_registration_authorization(self):
        uid=security.register('Студент','TEST@example.com','passWord123','passWord123')
        self.assertEqual(security.login('test@example.com','passWord123')['id'],uid)
        with self.assertRaises(ValueError):security.login('test@example.com','wrong')
        with self.assertRaises(ValueError):security.register('Другой','test@example.com','passWord123','passWord123')
        security.change_password(uid,'passWord123','anotherPass123')
        self.assertEqual(security.login('test@example.com','anotherPass123')['id'],uid)
        code=security.generate_reset('test@example.com')
        with self.assertRaises(ValueError):security.reset_password('test@example.com','111111' if code!='111111' else '222222','finalPass123')
        security.reset_password('test@example.com',code,'finalPass123')
        self.assertEqual(security.login('test@example.com','finalPass123')['id'],uid)
    def test_ai_three_datasets(self):
        for prompt in ['космос наука приключения','семья любовь дружба','детектив тайна расследование']:
            items=intelligence.recommend(prompt)
            self.assertGreaterEqual(len(items),3)
            self.assertEqual(len({row[0]['id'] for row in items}),len(items))
            self.assertTrue(all(0<=score<=1 for _,score,_ in items))
    def test_comparison(self):
        ranks=intelligence.compare(db.movies()[:4]);self.assertEqual(len(ranks),4)
        self.assertEqual([x[1] for x in ranks],sorted((x[1] for x in ranks),reverse=True))
    def test_search_filter_sort(self):
        self.assertTrue(all(r['genre']=='Драма' for r in db.movies(genre='Драма')))
        ratings=[r['rating'] for r in db.movies(sort='Рейтинг ↓')]
        self.assertEqual(ratings,sorted(ratings,reverse=True))

if __name__=='__main__':unittest.main(verbosity=2)
