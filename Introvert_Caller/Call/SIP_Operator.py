import sys
import pjsua as pj
import time
from tinydb import TinyDB, Query
import configparser  # To access and read configuration file

if __name__ == "__main__":
    phone_number = sys.argv[1]
    msg_len = sys.argv[2]
    config_loc = sys.argv[3]
    repetitions_var = sys.argv[4]
    language_var = sys.argv [5]



# CONFIGURATION:
cfg = configparser.ConfigParser()
cfg.read(config_loc)


# OPTIONS FILE LANGUAGE
if language_var == 'en':
    option_file = 'options_en.wav'
    gratitude_file = 'gratitude_en.wav'
    ques_time = 7.488

elif language_var == 'fr':
    option_file = 'options_fr.wav'
    gratitude_file = 'gratitude_fr.wav'
    ques_time = 8.616

elif language_var == 'de':
    option_file = 'options_de.wav'
    gratitude_file = 'gratitude_de.wav'
    ques_time = 9.528

else :
    option_file = 'options_en.wav'
    gratitude_file = 'gratitude_en.wav'
    ques_time = 7.488


tick = TinyDB(cfg['PATH']['tick_loc'] + 'tick.json')
domain = str(cfg['SIP']['domain'])
username = str(cfg['SIP']['username'])
password = str(cfg['SIP']['password'])
audio_loc = str(cfg['PATH']['wav_file_loc']) + "ttv_audio.wav"
options_loc = str(cfg['PATH']['wav_file_loc']) + option_file
tone_loc = str(cfg['PATH']['wav_file_loc']) + "tone.wav"
note_loc = str(cfg['PATH']['wav_file_loc']) + "note.wav"
thank_loc = str(cfg['PATH']['wav_file_loc']) + gratitude_file
silence_loc = str(cfg['PATH']['wav_file_loc']) + "silence_0.6.wav"
silence_before_play = float(cfg['SOUND']['silence_before_play'])
ques_rep = int(cfg['SOUND']['questionnaire_repeat'])
ans_time = float(cfg['SOUND']['question_answer_time'])
sip_expiry = float(cfg['SIP']['timeout'])
reaching_time = float(cfg['SIP']['reaching_time'])  # How long the phone will keep ringing





msg_len = float(msg_len)
repetitions_var = int(repetitions_var)


timeanddate = 'NULL'
loading = ["CALL STATUS: Calling ",
           "CALL STATUS: Calling .",
           "CALL STATUS: Calling ..",
           "CALL STATUS: Calling ...",
           "CALL STATUS: Calling ....",
           "CALL STATUS: Calling ...",
           "CALL STATUS: Calling ..",
           "CALL STATUS: Calling .",
           "CALL STATUS: Calling ", ]
c1 = 0
c2 = 0
digitz = [999]
allow = False
go = True
stop = False
sip_time = 0
play_list = [0] * ((repetitions_var * 2) + (ques_rep * 2))
option_time = (ques_time + 7.488) * ques_rep + ans_time
thanks_time = (0.888 + 1.71428571429) #Thank You + Note
message_time = (msg_len * repetitions_var) + silence_before_play + 0.3


# Processing received digits

def options( number , pli):

    global allow, stop

    update = [0] * 5

    # Get the player's conference bridge's slot number
    playlist_slot = lib.playlist_get_slot(pli)

    # Get the receiver's phone slot
    phone_slot = my_cb.call.info().conf_slot

    # Stop the option voice message. (the receiver can choose when the beep is played before the automated message)
    lib.conf_disconnect(playlist_slot, phone_slot)

    # Create the tone player
    player_id = lib.create_player(filename=note_loc,loop=False)

    # Play the note
    lib.conf_connect(lib.player_get_slot(player_id),phone_slot)

    #1 or 2 has been pressed
    if 1<= number <= 2:

        # Don't receive digits
        allow = False

        pli = lib.create_player(filename=thank_loc, loop=False)
        time.sleep(silence_before_play)
        player_slot = lib.player_get_slot(pli)
        lib.conf_connect(player_slot, phone_slot)

        update [0] = thanks_time

        if number == 1:
            tick.update({'Choice': 'CONFIRMED'}, doc_ids=[1])

        else:
            tick.update({'Choice': 'DECLINED'}, doc_ids=[1])

    # 3 is pressed. Repeat the message
    elif number == 3:

        # Don't receive digits
        allow = False

        # Cease the loop
        stop = True

        lib.playlist_destroy(pli)
        pli = lib.create_playlist(filelist=play_list, loop=False)
        time.sleep(silence_before_play)
        playlist_slot = lib.playlist_get_slot(pli)
        lib.conf_connect( playlist_slot, phone_slot)
        update[2] = pli
        update[3] = message_time + option_time
        tick.update({'Choice': 'Repeat the message (NO CONFIRMATION)'}, doc_ids=[1])

    #wrong number pressed. the options question will be repeated
    else:

        pli = lib.create_player(filename=options_loc, loop=False)
        time.sleep(silence_before_play)
        player_slot = lib.player_get_slot(pli)
        lib.conf_connect(player_slot, phone_slot)
        update[0] = 0
        update[1] = 0
        update[2] = pli
        update[3] = option_time

    return update

# Logging callback

def log_cb(level, str, len):
    print (str)


# Callback to receive events from Call
class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)

    # Notification when call state has changed
    def on_state(self, repeat=True):
        global timeanddate
        finish = False
        call_confirmation = False
        if self.call.info().state_text == "EARLY" and repeat is True:
            # print "Call is ", self.call.info().state_text
            # print "last code =", self.call.info().last_code
            print ("##################")
            print ("[" + self.call.info().last_reason + "]")
            print ("##################\n")
            timeanddate = time.asctime(time.localtime(time.time())) and time.strftime("%H:%M:%S|%d-%b-%Y")
            tick.update({'Connected?': True, 'Time&Date': timeanddate}, doc_ids=[1])
            repeat = False

        if self.call.info().state_text == 'CONFIRMED':
            call_confirmation = True

        if self.call.info().state == pj.CallState.DISCONNECTED:
            finish = True
            "Call Status: DISCONNECTED"

        return finish, call_confirmation, timeanddate

    # Notification when call's media state has changed.
    def on_media_state(self):
        global lib, playlist_id

        c = 0
        for i in range(repetitions_var):
            play_list[ i + c] = audio_loc
            play_list[ i + 1 + c] = silence_loc
            c = c + 1

        c = 0
        for i in range(ques_rep):
            play_list[(repetitions_var*2)  + i + c] = tone_loc
            play_list[(repetitions_var*2) + i + 1 + c] = options_loc
            c = c + 1

        playlist_id = lib.create_playlist(filelist=play_list, loop=False)

        if self.call.info().media_state == pj.MediaState.ACTIVE and self.call.info().state_text == 'CONFIRMED':
            time.sleep(silence_before_play)

            lib.playlist_get_slot(playlist_id)
            lib.conf_connect(lib.playlist_get_slot(playlist_id), self.call.info().conf_slot)


    def on_dtmf_digit(self, digits=999):
        global allow

        if not allow:
            print ("The Receiver is pressing before the tone: " + str(digits))

        elif not str(digits).isdigit():

            digitz[0] = 0

        elif digits != 999:

            digitz[0] = digits

        else:
            digitz[0] = 999

        return digitz


try:
    # Create library instance
    lib = pj.Lib()

    # Init library with default config
    lib.init(log_cfg=pj.LogConfig(level=3, callback=log_cb))

    # Create UDP transport which listens to any available port
    transport = lib.create_transport(pj.TransportType.UDP)

    # Start the library
    lib.start()

    # Create local/user-less account
    # This will start "class Account()"
    # || acc = lib.create_account_for_transport(transport)

    # Prepare the destination URI for SIP
    rx_dst_uri = 'sip:'+ phone_number + '@' + domain
    uri_check = lib.verify_sip_url(rx_dst_uri)

    # Validate URI
    if uri_check != 0:
        tick.update({'Error': "URI Verification Status:" + str(
            uri_check) + "\n" + "Invalid URI, please check your SIP configuration."},
                    doc_ids=[1])

    # If there's no username or password
    elif len(password) < 1 or len(username) < 1:
        tick.update({'Error': "URI Verification Status: " + str(
            uri_check) + "\nInvalid URI, please check your SIP username/password."},
                    doc_ids=[1])

    # SIP register
    acc_cfg = pj.AccountConfig(
        domain=domain,
        username=username,
        password=password
    )

    # Create account with user
    acc = lib.create_account(acc_config=acc_cfg)
    account_info = acc.info()

    # print account_info
    # print "reg_active: " + str(account_info.reg_active)
    # print 'online_text: ' + str(account_info.online_text)
    # print 'online_status: ' + str(account_info.online_status)
    # print 'reg_expires: ' + str(account_info.reg_expires)
    # print 'reg_status: ' + str(account_info.reg_status)

    if not (account_info.reg_status == 100):
        tick.update({'Error': "SIP Register Status:" + str(
            account_info.reg_status) + "\n" + "The connection to SIP server was unsuccessful."}, doc_ids=[1])
        go = False

    # Make call
    # The method "make_call" is fetched from class Account()
    # Note that the method create_account return the instance class Account. that's why we were able to request Account methods.

    if go:

        go = False
        my_cb = MyCallCallback()
        call = acc.make_call(dst_uri=rx_dst_uri, cb=my_cb)
        print (rx_dst_uri)
        active_call = my_cb.on_state(repeat=True)


        # print "--------------------------------------------------"

        # print 'account: ' + str(call_info.account)
        # print 'call_time ' + str(call_info.call_time)
        # print 'conf_slot ' + str(call_info.conf_slot)
        # print 'remote_contact ' + str(call_info.remote_contact)
        # print 'sip_call_id ' + str(call_info.sip_call_id)
        # print 'state ' + str(call_info.state)
        # print 'state_text ' + str(call_info.state_text)
        # print 'CALL IS:'+str(active_call[0])
        # print 'total_time ' + str(call_info.total_time)
        # print "uri: " + str(call_info.uri)
        # print"---------------------------------------------------"

        while call.info().state_text == "CALLING" and sip_time < sip_expiry:
            sip_time = sip_time + 0.1
            time.sleep(0.01)

        if call.info().state_text == "CALLING":
            tick.update({'Error': "SIP Register Status:" + str(
                account_info.reg_status) + "\n" + "Connection timeout! Please check your SIP configuration."},
                        doc_ids=[1])
        else:
            go = True

    if go:

        # Keep connected till the call is disconnected from the receiver's end:

        exp_time = 0.0
        execute = True  # For one time execution
        connect_time = reaching_time  # How long will the connection stay online
        t_var = 1.0

        # -------------------------------------------------------------------------------------------
        while active_call[0] is False and exp_time < connect_time:

            if execute and active_call[1]:

                timeanddate = time.asctime(time.localtime(time.time())) and time.strftime("%H:%M:%S|%d-%b-%Y")

                print("\rCALL STATUS: Answered @ " + timeanddate)

                # Update the time the call is answered and the status:

                tick.update({'Answered?': True, 'Time&Date': timeanddate, 'Connected?': True}, doc_ids=[1])
                account_info = acc.info()

                exp_time = 0.0  # Reset the timer
                connect_time = message_time + option_time  # The call will stay connected till eveything is played
                execute = False  # To execute this if section once only
                start = time.time()

            else:

                if execute:
                    t_var = 0.2
                    exp_time = exp_time + 0.2
                    c2 = c2 + 1
                    # --------------------------------------
                    if c2 == 0 or c2 > 6:
                        sys.stdout.write("\r" + loading[c1])
                        sys.stdout.flush()
                        c1 = c1 + 1
                        if c1 == len(loading):
                            c1 = 0
                        c2 = 1
                        sys.stdout.flush()
                    # -------------------------------------

                else:
                    if stop and not allow:
                        t_var = message_time - silence_before_play
                        stop = False
                    else:
                        t_var = message_time

                    time.sleep(t_var)
                    allow = True
                    in_digits = my_cb.on_dtmf_digit()
                    t_var = 0
                    exp_time = message_time

                    # Awaiting the receiver's digits
                    while exp_time < connect_time and not stop and active_call[1]:

                        exp_time = exp_time + 0.1
                        time.sleep(0.1)
                        active_call = my_cb.on_state(repeat=False)

                        if int(in_digits[0]) != 999 :

                            # Reset the dtmf digit variable
                            pressed = in_digits[0]
                            in_digits = my_cb.on_dtmf_digit()
                            io = options(number=int(pressed), pli=playlist_id)

                            # Reset the timers
                            exp_time = io[1]
                            t_var = io[0]
                            playlist_id = io[2]
                            connect_time = io[3]

                time.sleep(t_var)

                active_call = my_cb.on_state(repeat=False)
        #----------------------------------------------------------------------------------------------------------------------



        if connect_time != reaching_time:
            end = time.time()

            print ("Connection time: " + str(round(end - start)) + " seconds")

        else:
            sys.stdout.flush()
            print ("\rCALL STATUS: No answer from +352 " + str(
                phone_number) + "\nThe system ceased calling after: " + str(reaching_time) + " seconds")

        account_info = acc.info()

        print ("SIP connection was successfully established within  " + str(sip_time) + " seconds")

        print ("\n##################")
        print ("[Session Finished]")
        print ("##################\n")
        lib.hangup_all()
    # _______________________________________________________________________________________________________________________

    # We're done, shutdown the library
    transport = None
    acc.delete()
    acc = None
    lib.destroy()
    lib = None

except pj.Error as e:
    print ("Exception: " + str(e))
    lib.destroy()
    lib = None

