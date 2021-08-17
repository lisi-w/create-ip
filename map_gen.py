 
import time
import shutil
import subprocess
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from subprocess import PIPE

def send_msg(message, to_email):
    print("Sending email...")

    msg = MIMEMultipart()
    from_email = "witham3@llnl.gov" # can replace with ames4@llnl.gov
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Mapfile Gen Failure"
    body = message
    msg.attach(MIMEText(body, 'plain'))
    s = smtplib.SMTP('nospam.llnl.gov')  # llnl smtp: nospam.llnl.gov
    s.ehlo()
    s.starttls()
    text = msg.as_string()
    s.sendmail(from_email, to_email, text)
    s.quit()

    print("Done.")


def update_ini():
    w_dir = os.getcwd()
    os.chdir('/esg/config/esgcet')
    os.system("git pull")
    os.chdir(w_dir)


def main():
    run = True

    input_dir = '/export/witham3/create-ip-replica/CREATE-IP-list-todo'
    done_dir = '/export/witham3/create-ip-replica/CREATE-IP-list-done'
    output_dir = '/export/witham3/create-ip-replica/CREATE-IP-maps-todo'
    ini_dir = '/esg/config/esgcet'

    update_ini()

    with open("maps-resume.txt", "r") as m:
        pointer = int(m.readline())
        prev_file = m.readline().strip()
    while run:
        try:
            files = os.listdir(input_dir)
        except:
            print("Filesystem error occurred. Trying again in 20 minutes...")
            time.sleep(1200)
            continue
        count = len(files)
        if count == 0:
            print("No files found to do. Going to sleep.")
            time.sleep(1200)
            continue
        for n in range(count):
            i = 0
            filename = input_dir + '/' + files[n]
            if pointer != 0 and prev_file != "":
                filename = prev_file
                n -= 1
            print('Starting {}'.format(filename))
            try:
                test = open(filename, 'r')
                test.close()
            except:
                print("WARNING: " + filename + " not accessable.")
                break
            with open(filename, 'r') as fp:
                if pointer != 0:
                    print('InsteadResuming {}'.format(filename))
                    print("resuming at " + str(pointer))
                i = 0
                for line in fp:
                    if i < pointer:
                        i += 1
                        continue
                    try_again = True
                    count = 0
                    while try_again:
                        print("PROCESSING {}".format(line))
                        cmd = "esgmapfile -i " + ini_dir + " --project CREATE-IP --outdir " + output_dir + " --max-processes 8 --no-cleanup " + line
                        mp = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, shell=True)
                        ec = mp.returncode
                        mp_stderr = mp.stderr
                        with open("maps-resume.txt", "w") as m:
                            m.write(str(i) + "\n")
                            m.write(filename)
                        gotosleep = False
                        if ec == 255:
                            print("Error: stale file handle. Trying again in 20 minutes...")
                            time.sleep(1200)
                            try_again = True
                            count = 0
                        elif ec == 127:
                            print("Filesystem error likely. Trying again in 20 minutes...")
                            time.sleep(1200)
                            try_again = True
                            count = 0
                        elif ec != 0:
                            print("Error: " + str(ec))
                            msg = ""
                            for l in mp_stderr.splitlines():
                                print(l.decode('ascii'))
                                msg += l.decode('ascii') + "\n"
                                if 'such file or directory' in l.decode('ascii'):
                                    gotosleep = True
                            for l in mp.stdout.splitlines():
                                print(l.decode('ascii'))
                                msg += l.decode('ascii') + "\n"
                                if 'such file or directory' in l.decode('ascii'):
                                    gotosleep = True
                            count += 1
                            if count > 3 and not gotosleep:
                                msg += "esgmapfile " + line + " [FAIL] " + filename + "\nERROR: " + str(ec)
                                send_msg(msg, "e.witham@columbia.edu")
                                send_msg(msg, "ames4@llnl.gov")
                                exit(ec)
                            elif gotosleep:
                                print("Filesystem error. Trying again in 20 minutes...")
                                time.sleep(1200)
                                try_again = True
                                count = 0
                        else:
                            count = 0
                            try_again = False
                            i += 1
                            for l in mp.stdout.splitlines():
                                print(l.decode('ascii'))
            path = shutil.move(filename, done_dir)
            with open("maps-resume.txt", "w") as m:
                m.write("0")
            prev_file = ""
            pointer = 0


if __name__ == '__main__':
    main()
