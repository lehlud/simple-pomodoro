import os, art, time, curses, random, subprocess as sp

if os.name not in ['posix', 'nt']:
    print('Error: os unsupported')
    exit(1)

notification_id = None

FONTS = ['poison', 'banner3', 'pebbles', 'colossal', 'lildevil', 'ghost', 'swampland', 'larry3d', 'nancyj-fancy', 'slide', 'tanja', 'jazmine']
FONT = random.choice(FONTS)
# FONT = random.choice(art.ASCII_FONTS)

def play_bells():
    if os.name == 'posix':
        sp.Popen(['bash', '-c', 'for i in {1..3}; do aplay bells.wav &> /dev/null; done'])

    elif os.name == 'nt':
        sp.Popen(['powershell', '-c', '$m=New-Object Media.SoundPlayer bells.wav;1..3 % {$m.PlaySync}'])

def lock_screen():
    if os.name == 'posix':
        sp.Popen(['xdg-screensaver', 'activate'])

    elif os.name == 'nt':
        sp.Popen(['rundll32', 'user32.dll,LockWorkStation'])

def unlock_screen():
    if os.name == 'posix':
        sp.Popen(['xdg-screensaver', 'reset'])

    elif os.name == 'nt':
        send_notification('Pomodoro!', 'Hey, you should login again!', 5000)

def send_notification(title: str, message: str, duration_ms: int = 3000):
    if os.name == 'posix':
        global notification_id
        args = ['notify-send', title, message, '-p', '-t', str(duration_ms)]
        if notification_id: args += ['-r', notification_id]
        stdout, _ = sp.Popen(args, stdout=sp.PIPE).communicate()
        notification_id = stdout.strip()

    elif os.name == 'nt':
        script = f"""
            Add-Type -AssemblyName System.Windows.Forms;
            $n = New-Object System.Windows.Forms.NotifyIcon;
            $n.Icon = [System.Drawing.SystemIcons]::Information;
            $n.BalloonTipTitle = @'{title}'@;
            $n.BalloonTipText = @'{message}'@;
            $n.Visible = $true;
            $n.ShowBalloonTip({duration_ms});
            Start-Sleep -Milliseconds {duration_ms};
            $n.Dispose();
        """

        sp.Popen(['powershell', '-c', script])

def write_centered(scr, texts: list[str]):
    height, width = scr.getmaxyx()

    total_lines = sum(len(text.split('\n')) - 1 for text in texts)
    start_y = 0 # (height - total_lines) // 2

    for i, text in enumerate(texts):
        lines = text.split('\n')

        max_line_width = max(len(line) for line in lines)
        start_x = (width - max_line_width) // 2

        for j, line in enumerate(lines):
            if line.strip() == '' and len(lines) > 1: continue

            try: scr.addstr(start_y, start_x, line, curses.A_BOLD)
            except: pass

            start_y += 1

def write_status(scr, heading: str, duration_s: int, remaining_s: int, paused: bool):
    art_heading = art.text2art(heading, font='small')

    is_break = duration_s != 25 * 60

    remaining_m = str(remaining_s // 60)
    remaining_s = str(remaining_s % 60)
    art_remaining = art.text2art(f'{remaining_m.rjust(2, "0")}:{remaining_s.rjust(2, "0")}', font=FONT)

    write_centered(scr, [art_heading, '', art_remaining, '', 'BREAK' if is_break else 'WORKY WORK', '', '(PAUSED)' if paused else ''])
    

def main(scr):
    try:
        curses.curs_set(0)
        scr.nodelay(True)
        scr.timeout(200)

        started = time.time()
        duration_s = 25 * 60
        remaining_duration_s = duration_s

        notifiers = [(600, '10 Minutes'), (120, '2 Minutes'), (60, '1 Minute'), (30, '30 Seconds'), (10, '10 Seconds'), (3, '3 Seconds'), (2, '2 Seconds'), (1, '1 Second')]

        paused = False
        triggered_end = False
        sent_notifiers = []

        def reset(new_duration: int):
            nonlocal duration_s, remaining_duration_s, paused, triggered_end, sent_notifiers, started
            duration_s = new_duration
            remaining_duration_s = duration_s

            paused = False
            triggered_end = False
            sent_notifiers = []

            started = time.time()

        def pause():
            nonlocal paused, remaining_duration_s, duration_s
            if paused: return
            paused = True
            remaining_duration_s = duration_s
            

        def resume():
            nonlocal paused, started
            if not paused: return
            paused = False
            started = time.time()

        while True:
            is_break = duration_s != 25 * 60
            
            remaining_s = int((remaining_duration_s - time.time() + started) // 1) if not paused else remaining_duration_s
            if remaining_s < 0: remaining_s = 0

            if not triggered_end and remaining_s == 0:
                triggered_end = True
            
                if is_break:
                    play_bells()
                    unlock_screen()
                else:
                    lock_screen()
                    reset(5 * 60)
                    continue

            for notifier_s, notifier_msg in notifiers:
                if notifier_s != remaining_s: continue
                if notifier_s in sent_notifiers: break

                send_notification('Pomodoro!', f'{notifier_msg} remaining')
                sent_notifiers.append(notifier_s)
                break

            scr.clear()
            write_status(scr, 'Pomodoro!', duration_s, remaining_s, paused)
            scr.refresh()

            key = scr.getch()
            if key == -1: continue

            if key == ord('q'):
                exit(0)
                continue
            
            if key == ord(' '):
                if paused and not is_break:
                    resume()
                    continue
                
                reset(25 * 60)
                if not is_break: pause()
                continue
    
    except KeyboardInterrupt:
        exit(0)
            
 

if __name__ == '__main__':
    curses.wrapper(main)
