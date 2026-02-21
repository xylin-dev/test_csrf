import contextlib
import os
import subprocess
import threading
import time
from collections import namedtuple
from pathlib import Path
from subprocess import TimeoutExpired

import playwright.sync_api

ProcessDesc = namedtuple('Process', ['proc', 'name'])
ProcessDesc.__str__ = lambda self: f"Process(name={self.name}, pid={self.proc.pid})"


class ProcessGroup:
   def __init__(self):
      self.processes = []

   def __iter__(self):
      return iter(self.processes)

   def start_process(self, args, name, env=None, cwd=None):
      copy_env = os.environ.copy()
      copy_env.update(env or {})
      proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                              encoding='utf-8', env=copy_env, cwd=cwd)
      pd = ProcessDesc(proc, name)
      self.processes.append(pd)
      print("[*] 启动进程: " + str(pd))

   def kill(self):
      print('[*] 正在终止进程...')
      for pd in self:
         subprocess.run(["taskkill", "/F", "/T", "/PID", str(pd.proc.pid)], stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
         try:
            rc = pd.proc.wait(3)
            print(f'[*] 进程 {pd} 已终止，返回码 {rc}')
         except TimeoutExpired:
            print(f'[E] 进程 {pd} 终止超时')

   def wait(self):
      try:
         should_break = False
         while not should_break:
            for proc, name in self:
               if proc.poll() is not None:
                  print(f"[E] {name} 提前退出")
                  should_break = True
                  break
            time.sleep(1)
      except KeyboardInterrupt:
         print("[*] 收到中断信号")
      finally:
         self.kill()


class OutputWaiter:
   def __init__(self):
      self.events = []

   def add(self, proc, proc_name, expected_output, timeout=2):
      event = threading.Event()
      self.events.append((event, proc_name))

      def read_output():
         for line in proc.stdout:
            print(f'[{proc_name}] ' + line, end='')
            if expected_output in line:
               event.set()
               print(f'[*] {proc_name} 启动成功')

      threading.Thread(target=read_output, daemon=True).start()

   def wait(self):
      time.sleep(2)

      for event, proc_name in self.events:
         if not event.is_set():
            print(f'[E] 进程 {proc_name} 输出超时')
            self.timeout_process = proc_name
            return False
      return True


@contextlib.contextmanager
def run_sites_context():
   basedir = Path(__file__).parent

   pgroup = ProcessGroup()
   output_waiter = OutputWaiter()

   pgroup.start_process(["uv", "run", 'python', '-u', '-m', "site1.app"], 'site1', env=dict(PORT='5001'), cwd=basedir)
   pgroup.start_process(["uv", "run", 'python', '-u', '-m', "site2.app"], 'site2', env=dict(PORT='5002'), cwd=basedir)

   expected_outputs = {
      'site1': "Running on http://",
      'site2': "Serving HTTP on"
   }

   for proc, name in pgroup:
      output_waiter.add(proc, name, expected_outputs[name])

   if not output_waiter.wait():
      print(f"[E] {output_waiter.timeout_process} 输出超时")
      pgroup.kill()
      return

   try:
      yield
   finally:
      pgroup.kill()


def read_token_alice():
   return Path(__file__).parent.joinpath('site1/tokens/alice').read_text()


with run_sites_context(), playwright.sync_api.sync_playwright() as p:
   browser = p.chromium.launch(headless=False)
   context = browser.new_context()
   context.add_cookies([
      {
         'name': 'token',
         'value': read_token_alice(),
         'url': 'http://127.0.0.1:5001'
      }
   ])
   page1 = context.new_page()
   page2 = context.new_page()

   page1.goto('http://127.0.0.1:5001/accounts/me')
   page2.goto('http://127.0.0.1:5002')

   assert page1.text_content('body') == "Hello alice, your balance is 1000"

   page2.get_by_text('点击领奖').click()
   assert page2.url == 'http://127.0.0.1:5001/accounts/transfer'

   page1.reload()
   assert page1.text_content('body') == "Hello alice, your balance is 900"
   input('waiting...')
