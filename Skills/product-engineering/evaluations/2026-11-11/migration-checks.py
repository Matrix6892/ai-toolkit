import unittest, pathlib, tempfile, sqlite3, subprocess, sys, hashlib, threading, time, shutil, os
ROOT=pathlib.Path(__file__).resolve().parent
SCRIPT=pathlib.Path(os.environ.get('EVAL_MIGRATION_FILE',str(pathlib.Path.cwd()/'migrate.py')))
class Migration(unittest.TestCase):
 def setUp(self):
  self.tmp=pathlib.Path(tempfile.mkdtemp(prefix='oracle-',dir=ROOT));self.src=self.tmp/'источник с пробелом.sqlite';self.dst=self.tmp/'результат.sqlite'
 def tearDown(self):shutil.rmtree(self.tmp)
 def seed(self,orders=None,history=None,wal=False):
  c=sqlite3.connect(self.src)
  if wal:c.execute('pragma journal_mode=WAL')
  c.execute('create table orders(id TEXT PRIMARY KEY,status TEXT,address TEXT,revision INTEGER NOT NULL)');c.execute('create table history(order_id TEXT,seq INTEGER,event TEXT,PRIMARY KEY(order_id,seq))')
  rows=orders if orders is not None else [('а','created','улица\nдом',1),('b','pickup_ready','',2),('c','delivered','住所',3)]
  h=history if history is not None else [('а',1,'создан'),('b',1,'first'),('b',2,'second'),('c',1,'один'),('c',3,'три')]
  c.executemany('insert into orders values(?,?,?,?)',rows);c.executemany('insert into history values(?,?,?)',h);c.commit();c.close()
 def run_cli(self):return subprocess.run([sys.executable,str(SCRIPT),'--source',str(self.src),'--target',str(self.dst)],capture_output=True,text=True,timeout=30)
 def reject(self):
  before=hashlib.sha256(self.src.read_bytes()).hexdigest();r=self.run_cli();self.assertNotEqual(r.returncode,0);self.assertTrue((r.stderr+r.stdout).strip());self.assertFalse(self.dst.exists());self.assertEqual(before,hashlib.sha256(self.src.read_bytes()).hexdigest())
 def test_valid_preserves_values_and_history(self):
  self.seed();before=self.src.read_bytes();r=self.run_cli();self.assertEqual(r.returncode,0,r.stderr);c=sqlite3.connect(self.dst);self.assertEqual(c.execute('select * from orders order by id').fetchall(),[('b','ready_for_dispatch','',2),('c','completed','住所',3),('а','new','улица\nдом',1)]);s=sqlite3.connect(self.src);self.assertEqual(c.execute('select * from history order by order_id,seq').fetchall(),s.execute('select * from history order by order_id,seq').fetchall());self.assertEqual(c.execute('pragma integrity_check').fetchone()[0],'ok');c.close();s.close();self.assertEqual(before,self.src.read_bytes())
 def test_unknown_status_no_partial_target(self):self.seed([('x','ready','a',1)],[('x',1,'e')]);self.reject()
 def test_orphan_history_rejected(self):self.seed([('x','created','a',1)],[('missing',1,'e')]);self.reject()
 def test_empty_id_rejected(self):self.seed([('','created','a',1)],[('',1,'e')]);self.reject()
 def test_negative_revision_rejected(self):self.seed([('x','created','a',-1)],[('x',1,'e')]);self.reject()
 def test_bad_history_sequence_rejected(self):self.seed([('x','created','a',1)],[('x',0,'e')]);self.reject()
 def test_existing_target_preserved(self):
  self.seed();self.dst.write_bytes(b'preexisting target');before=self.dst.read_bytes();r=self.run_cli();self.assertNotEqual(r.returncode,0);self.assertEqual(self.dst.read_bytes(),before)
 def test_concurrent_target_publication(self):
  self.seed([(str(i),'created','a',1) for i in range(5000)],[(str(i),1,'e') for i in range(5000)])
  args=[sys.executable,str(SCRIPT),'--source',str(self.src),'--target',str(self.dst)]
  ps=[subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(4)]
  outputs=[p.communicate(timeout=30) for p in ps];codes=[p.returncode for p in ps]
  self.assertEqual(codes.count(0),1,(codes,outputs));c=sqlite3.connect(self.dst);self.assertEqual(c.execute('select count(*) from orders').fetchone()[0],5000);self.assertEqual(c.execute('pragma integrity_check').fetchone()[0],'ok');c.close()
 def test_source_missing_does_not_create_it(self):
  r=self.run_cli();self.assertNotEqual(r.returncode,0);self.assertFalse(self.src.exists());self.assertFalse(self.dst.exists())
 def test_concurrent_source_snapshot(self):
  rows=[(str(i),'created','v1',1) for i in range(5000)];h=[(str(i),1,'v1') for i in range(5000)];self.seed(rows,h,True);stop=threading.Event();ready=threading.Event();failures=[]
  def writer():
   try:
    c=sqlite3.connect(self.src,timeout=10);v=1
    while not stop.is_set():
     v+=1;c.execute('begin immediate');c.execute('update orders set revision=?,address=? where id=\'0\'',(v,'v'+str(v)));c.execute('insert into history values(?,?,?)',('0',v,'v'+str(v)));c.commit();ready.set();time.sleep(.001)
    c.close()
   except Exception as e:failures.append(str(e));ready.set()
  t=threading.Thread(target=writer);t.start();self.assertTrue(ready.wait(10))
  try:
   c=sqlite3.connect(self.src);min_v=c.execute('select revision from orders where id=\'0\'').fetchone()[0];c.close();r=self.run_cli()
  finally:stop.set();t.join(10)
  self.assertFalse(failures,failures);self.assertEqual(r.returncode,0,r.stderr);c=sqlite3.connect(self.dst);v,address=c.execute('select revision,address from orders where id=\'0\'').fetchone();last=c.execute('select max(seq) from history where order_id=\'0\'').fetchone()[0];self.assertEqual(v,last);self.assertGreaterEqual(v,min_v);self.assertEqual(address,'v'+str(v));self.assertEqual(c.execute('select count(*) from orders').fetchone()[0],5000);c.close()
if __name__=='__main__':unittest.main(verbosity=2)
