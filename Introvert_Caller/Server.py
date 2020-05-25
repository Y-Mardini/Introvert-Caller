from tinydb import TinyDB, Query    # Database library
from gtts import gTTS               # Google translate library
from textblob import TextBlob       # Language detection
from shutil import copyfile  # To be able to copy json files
import cherrypy  # Server library
import queue  # To execute POST requests in order
import time  # To create time stamps
import wave  # To open WAV file
import contextlib  # To get frames and fps of WAV file
import subprocess  # To execute system processes
import requests  # To disable the http requests warnings when accessing Google.Translate API
import configparser  # To access and read configuration file
import os  # for locating the config file & checking whether the directory exist or not
import pjsua as pj


# CONFIGURAT

config_loc = os.path.abspath('.') + '/configuration.ini'

cfg = configparser.ConfigParser()
cfg = configparser.ConfigParser()
cfg.read(config_loc)

host_var = str(cfg['SERVER']['server_socket_host'])
port_var = int(cfg['SERVER']['server_socket_port'])


# Directories check-up:
if not os.path.exists(cfg['PATH']['edb_loc']):
    os.makedirs(os.path.abspath('.') + '/Database')


if not os.path.exists(cfg['PATH']['dbbkb_loc']):
    os.makedirs(cfg['PATH']['edb_loc'] + "database_backup/")

#X_X WE DONT NEED TO CREATE MEDIA FOLDER, BECAUSE IT'S AN ESSENTIAL FOLDER IN THE SYSTEM WITH ITS FILES

# if not os.path.exists(cfg['PATH']['mp3_file_loc']):
#     os.makedirs(os.path.abspath("Media/"))


# To store events and updates to be sent back to the client as report
edb = TinyDB(cfg['PATH']['edb_loc'] + 'events_db.json')

# To update the SIP operation status:
tick = TinyDB(cfg['PATH']['tick_loc'] + 'tick.json')

# Database Limit
db_limit = cfg['DATABASE']['db_limit']
db_limit = int(db_limit) + 1



# To disable all insecure connection requests, used for the google translate request
requests.packages.urllib3.disable_warnings()

# Error recorder
edb_stage_var = {
    'Audio_File_Saved': False,
    'Audio_File_Converted': False,
    'SIP_Operated': False,
    'SIP_Called': False
}


# Initial values
queue_var = {}
seq = 0
fifo = queue.Queue()
ok = 1
busy = False
op_id_var = 1
dbbkb_loc = 'null'
purge = False
config_doc = 'null'
cdb = 'null'
third_plus = False
unlucky = False

language_code = {
    "Afrikaans": 'af',
    "Arabic": 'ar',
    "Armenian": 'hy',
    "Azerbaijani": 'az',
    "Bengali": 'bn',
    "Catalan": 'ca',
    "Chinese": 'zh-CN',
    "Croatian": 'hr',
    "Czech": 'cs',
    "Danish": 'da',
    "Dutch": 'nl',
    "English": 'en',
    "Finnish": 'fi',
    "French": 'fr',
    "German": 'de',
    "Greek": 'el',
    "Hindi": 'hi',
    "Hungarian": 'hu',
    "Icelandic": 'is',
    "Indonesian": 'id',
    "Italian": 'it',
    "Japanese": 'ja',
    "Khmer": 'km',
    "Korean": 'ko',
    "Latvian": 'lv',
    "Nepali": 'ne',
    "Norwegian": 'no',
    "Polish": 'pl',
    "Portuguese": 'pt',
    "Romanian": 'ro',
    "Russian": 'ru',
    "Serbian": 'sr',
    "Shona": 'sn',
    "Sinhala": 'si',
    "Slovak": 'sk',
    "Spanish": 'es',
    "Swahili": 'sw',
    "Swedish": 'sv',
    "Tamil": 'ta',
    "Thai": 'th',
    "Turkish": 'tr',
    "Vietnamese": 'vi'
}


@cherrypy.expose
@cherrypy.tools.json_out()
@cherrypy.tools.json_in()
class TextToVoiceCallingService(object):
    @cherrypy.tools.accept(media='application/json')
    def PUT(self):
        global busy

        edb = TinyDB(cfg['PATH']['edb_loc'] + 'events_db.json')
        get_data = cherrypy.request.json

        if len(edb) == 0:
            info_var = 'NO Records to be shown. '+str(get_data['get_id'])
        else:
            config_doc = edb.get(doc_id=1)

            if not get_data['get_id'].isdigit():
                info_var = '(error) Invalid ID number: ' + get_data['get_id'] + '\n'


            # -----------------------------------------------------------------------------------------------------
            # SEND BACK ALL THE CALL RECORDS
            # -----------------------------------------------------------------------------------------------------
            elif get_data['get_id'] == "0":
                busy =True
                i = 2
                while i <= len(edb):
                    doc_cont = edb.get(doc_id=i)
                    if i == 2:

                        info_var = \
                            "-Record ID:" + str(doc_cont['OP_ID']) + \
                            "\n-Phone Number: " + str(doc_cont['Phone_Number']) + \
                            "\n-Text Message: " + str(doc_cont['Text_Message']) + \
                            "\n-Language: " + str(doc_cont['Language']) + \
                            "\n-Message Repetition: " + str(doc_cont['Play_Repetitions']) + \
                            "\n-Answered?: " + str(doc_cont['Answered?']) + \
                            "\n-Feedback: " + str(doc_cont['Feedback']) + \
                            "\n-Time & Date: " + str(doc_cont['Time&Date']) + \
                            "\n--------------------------------------------------------------------------------------"
                    else:
                        info_var = info_var + \
                            "\n-Record ID:" + str(doc_cont['OP_ID']) + \
                            "\n-Phone Number: " + str(doc_cont['Phone_Number']) + \
                            "\n-Text Message: " + str(doc_cont['Text_Message']) + \
                            "\n-Language: " + str(doc_cont['Language']) + \
                            "\n-Message Repetition: " + str(doc_cont['Play_Repetitions']) + \
                            "\n-Answered?: " + str(doc_cont['Answered?']) + \
                            "\n-Feedback: " + str(doc_cont['Feedback']) + \
                            "\n-Time & Date: " + str(doc_cont['Time&Date']) + \
                            "\n--------------------------------------------------------------------------------------"

                    i = i + 1
                busy= False

            # -----------------------------------------------------------------------------------------------------


            elif int(get_data['get_id']) > (config_doc['black_log'] + len(edb) - 1):

                info_var = '(error) There is no record with ID: ' + get_data['get_id'] +\
                           '\n Existing Records = ' + \
                           str(config_doc['black_log'] + len(edb)-1)

            elif busy:
                info_var = "The system is processing previous GET request, please try again in a second. TQ "


            else:
                busy = True
                get_id = int(get_data['get_id'])

                if config_doc['black_log'] >= get_id:

                    while config_doc['black_log'] >= get_id:
                        dbbkb_loc = cfg['PATH']['dbbkb_loc'] + 'DB_' + str(config_doc['black_log']) + ':\n[' + \
                                    str(config_doc['db_birthday']) + "]\n" \
                                                                     "[" + str(config_doc['db_last_date']) + ']\n.json'
                        dbbkb = TinyDB(dbbkb_loc)

                        config_doc = dbbkb.get(doc_id=1)

                    doc_cont = dbbkb.get(Query().OP_ID == get_id)

                else:
                    doc_cont = edb.get(Query().OP_ID == get_id)

                if doc_cont['Connected?']:

                    if doc_cont['Answered?']:
                        ans_var = "Yes"
                    else:
                        ans_var = "No"

                    if doc_cont['Language'].upper() =='AUTO':

                        b = TextBlob(str(doc_cont['Text_Message']))
                        lan_var = b.detect_language()

                    else:
                        lan_var = doc_cont['Language']

                    info_var = \
                        "-Record ID:" + str(doc_cont['OP_ID']) + \
                        "\n-Phone Number: " + str(doc_cont['Phone_Number']) + \
                        "\n-Text Message: " + str(doc_cont['Text_Message']) +\
                        "\n-Language: " + str(lan_var) + \
                        "\n-Message Repetition: " + str(doc_cont['Play_Repetitions']) + \
                        "\n-Answered?: " + ans_var + \
                        "\n-Feedback: " + str(doc_cont['Feedback']) + \
                        "\n-Time & Date: " + str(doc_cont['Time&Date'])
                else:

                    info_var = \
                        "xxxxxxxxxxxxxxxxxxxxxxxFAILEDxCALLxREQUESTxxxxxxxxxxxxxxxxxxxxxxxxxx\n" \
                        "-Record ID:" + str(doc_cont['OP_ID']) + \
                        "\n-Phone Number: " + str(doc_cont['Phone_Number']) + \
                        "\n-Text Message: " + str(doc_cont['Text_Message']) + \
                        "\n-Message Repetition: " + str(doc_cont['Play_Repetitions']) + \
                        "\n-Time & Date: " + str(doc_cont['Time&Date']) + \
                        "\n*Error: \n-----------------------\n" + str(doc_cont['Error']) + "\n-----------------------" \
                                                                                           "\nOPERATION STAGES:" + \
                        "\nAudio_File_Saved: " + str(doc_cont['Stage']['Audio_File_Saved']) + \
                        "\nAudio_File_Converted: " + str(doc_cont['Stage']['Audio_File_Converted']) + \
                        "\nSIP_Operated: " + str(doc_cont['Stage']['SIP_Operated']) + \
                        "\nSIP_Called: " + str(doc_cont['Stage']['SIP_Called'])
                busy = False

        return info_var

    @cherrypy.tools.accept(media='application/json')
    def POST(self):
        global fifo, seq, queue_var, ok, edb_stage_var, op_id_var, dbbkb_loc, purge, config_doc, db_limit, \
            cdb, edb_instant, third_plus, unlucky, sip_loc, language_code

        info_var = ""
        go = True
        post_data = cherrypy.request.json

        # Validate phone number:
        if not post_data['phone'].isdigit() or (len(post_data['phone']) <= 4 or len(post_data['phone']) > 14):
            info_var = "(ERROR)\n" \
                       " The phone number is invalid: " + post_data['phone'] + "\n" + \
                       "(Please check the country_code in the configuration file in case the phone number is correct)"
            go = False

        # Validate the message
        elif len(post_data['text']) < 1:
            info_var = "(ERROR)\n" \
                                  " The text message is invalid: " + post_data['text'] + "\n"
            go = False
        elif len(post_data['text']) < 3 and post_data['language'].upper() == "AUTO":
            info_var = "( ERROR ) \n" +\
                "The message must be at least THREE letters long, for its language to be detected\n" \
                "(Remove AUTO and specify a language for message < 3 letters)"
            go = False

        # Validate the repetition number
        elif not post_data['repetitions'].isdigit() or\
                (int(post_data['repetitions']) > 8 or int(post_data['repetitions']) < 1):

            info_var = "(ERROR)\n" \
                        " Repetitions value is invalid: " + post_data['repetitions'] + \
                       ". 'Maximum repetitions is 8 and the provided value must be numerical'"
            go = False

        # Validate the language code of the message
        elif not post_data['language'] in language_code.values() and post_data['language'].upper() != 'AUTO':
            info_var = "(ERROR)\n"\
                        "The language code you entered is invalid.\n"
            go = False

        elif unlucky:
            info_var = "Your request is unfortunate:\n " \
                       "@ the exact same time with database removal within 0.111750 second."
            go = False

        if go:

            seq = seq + 1

            # ----------------------------------------------------------------------------------------------------------
            # DATABASE:

            # No database (first time running the server)

            if len(edb) == 0:

                timeanddate = time.asctime(time.localtime(time.time())) and time.strftime("%H:%M:%S|%d-%b-%Y")
                edb.insert({'black_log': 0,
                            'db_limit': db_limit,
                            'db_birthday': timeanddate,
                            'db_last_date': 'To come',
                            'Description': 'The document#[1] will always be the configuration document of the db'})

                edb_instant = edb.insert({'OP_ID': 1,
                                          'Time&Date': timeanddate,
                                          'Phone_Number': post_data['phone'],
                                          'Text_Message': post_data['text'],
                                          'Language': post_data['language'],
                                          'Play_Repetitions': post_data['repetitions'],
                                          'Feedback': 'NO RESPONSE',
                                          'Stage': edb_stage_var,
                                          'Error': "NULL",
                                          'Connected?': False,
                                          'Answered?': False
                                          })

            else:

                config_doc = edb.get(doc_id=1)
                timeanddate = time.asctime(time.localtime(time.time())) and time.strftime("%H:%M:%S|%d-%b-%Y")
                edb_instant = edb.insert({'OP_ID': 1,
                                          'Time&Date': timeanddate,
                                          'Phone_Number': post_data['phone'],
                                          'Text_Message': post_data['text'],
                                          'Language': post_data['language'],
                                          'Play_Repetitions': post_data['repetitions'],
                                          'Feedback': 'NO RESPONSE',
                                          'Stage': edb_stage_var,
                                          'Error': "NULL",
                                          'Connected?': False,
                                          'Answered?': False
                                          })

                op_id_var = (edb_instant - 1) + config_doc['black_log']
                edb.update({'OP_ID': op_id_var}, doc_ids=[edb_instant])

            # When the database limit is reached
            if len(edb) == db_limit:
                purge = True

            # ----------------------------------------------------------------------------------------------------------
            # POST REQUEST RETURN VALUES:
            if fifo.empty() and ok == 1:
                info_var = "REQUEST#" + str(seq) + \
                           "\nRECEIVED:  OK" \
                           "\nPROCESSED: OK" \
                           "\nID:[" \
                           + str(op_id_var) + "]"
            else:
                info_var = "REQUEST#" + str(seq) + \
                           "\nRECEIVED:  OK" \
                           "\nPROCESSED: AFTER REQ#" + str(seq - 1) + " IS FINISHED" \
                                                                      "\nID:[" \
                           + str(op_id_var) + "]"
            # ----------------------------------------------------------------------------------------------------------
            # Start the queue
            fifo.put(edb_instant)

            # REQUEST EXECUTION PROCESS:
            while not fifo.empty() and ok != 0:
                ok = 0
                bag = "COMPLETED SUCCESSFULLY"
                tx_doc_id = fifo.get()
                db_basket = edb.get(doc_id=tx_doc_id)

                # ------------------------------------------------------------------------------------------------------
                # TEXT TO SPEECH CONVERSION:

                # Detect the language of the message
                if db_basket['Language'].upper() == "AUTO":
                    ld = TextBlob(db_basket['Text_Message'])
                    lang_var = ld.detect_language()
                else:
                    lang_var = db_basket['Language']

                # Convert the fetched text using Google API
                text_audio = gTTS(db_basket['Text_Message'], lang=lang_var, slow=False)

                # Save the voice message in a specific location
                c_1 = text_audio.save(cfg['PATH']['mp3_file_loc'] + 'ttv_audio.mp3')

                # Wait
                time.sleep(0.1)

                # Check#1
                if str(c_1) == "None":
                    edb_stage_var['Audio_File_Saved'] = True
                else:
                    edb.update({'Error': str(c_1)}, doc_ids=[tx_doc_id])
                    edb.update({'Stage': edb_stage_var}, doc_ids=[tx_doc_id])
                    ok = 1
                    break

                # ------------------------------------------------------------------------------------------------------
                # AUDIO FILE CONVERSION:

                # Convert the MP3 google file to WAV. *(SIP library requirement)
                c_2 = subprocess.call(['/usr/bin/sox',
                                       cfg['PATH']['mp3_file_loc'] + "ttv_audio.mp3",
                                       cfg['PATH']['wav_file_loc'] + "ttv_audio.wav", 'rate', '24000'])
                # Check#2
                if c_2 == 0:
                    edb_stage_var['Audio_File_Converted'] = True
                else:
                    edb.update({'Error': 'Unable to convert MP3 file @ the location: '
                                         + cfg['PATH']['mp3_file_loc'] + 'ttv_audio.mp3'
                                         + " Return Code:"
                                         + str(c_2)},
                               doc_ids=[tx_doc_id])
                    edb.update({'Stage': edb_stage_var}, doc_ids=[tx_doc_id])
                    ok = 1
                    break

                # Fetch the duration of the converted WAV file:
                with contextlib.closing(wave.open(cfg['PATH']['wav_file_loc'] + 'ttv_audio.wav', 'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    voice_msg_len = frames / float(rate)

                # ------------------------------------------------------------------------------------------------------
                # SIP OPERATOR EXECUTION:

                command_line = 'python3 SIP_Operator.py {0} {1} {2} {3} {4}'.format(
                    str(db_basket['Phone_Number']),
                    str(voice_msg_len),
                    str(config_loc),
                    str(db_basket['Play_Repetitions']),
                    str(lang_var))

                tick.purge()
                tick.insert({'Answered?': False,
                             'Time&Date': 'NULL',
                             'Connected?': False,
                             'Error': 'NULL',
                             'Choice': 'NULL'
                             })
                c_3 = subprocess.call(command_line, shell=True, cwd=cfg['PATH']['SIP_file_loc'])

                # Check#3
                if c_3 == 134 or c_3 == 0:
                    edb_stage_var['SIP_Operated'] = True

                else:
                    edb.update({'Error': "Running the SIP file resulted in code error#: " + str(c_3)},
                               doc_ids=[tx_doc_id])
                    bag = edb_stage_var

                tick_var = tick.get(doc_id=1)

                # Update the record document with the SIP operation retrieved data
                if tick_var['Answered?']:
                    edb.update({'Answered?': True,
                                'Time&Date': tick_var['Time&Date'],
                                'Connected?': True,
                                'Feedback' : tick_var['Choice']}, doc_ids=[tx_doc_id])
                    edb_stage_var['SIP_Called'] = True

                elif tick_var['Connected?']:
                    edb.update({'Connected?': True,
                                'Time&Date': tick_var['Time&Date']}, doc_ids=[tx_doc_id])
                    edb_stage_var['SIP_Called'] = True

                # Check#4
                elif c_3 != 134 or c_3 != 0:
                    edb.update({'Error':str(tick_var['Error'])},
                               doc_ids=[tx_doc_id])
                    bag = edb_stage_var

                # Insert the database stage information into the document.
                edb.update({'Stage': bag}, doc_ids=[tx_doc_id])

                # Reset values
                edb_stage_var = {
                    'Audio_File_Saved': False,
                    'Audio_File_Converted': False,
                    'SIP_Operated': False,
                    'SIP_Called': False
                }

                # ------------------------------------------------------------------------------------------------------
                # DATABASE BACKUP & TERMINATION:

                if purge and fifo.empty():
                    unlucky = True

                    # Update the limit size from the configuration file
                    db_limit = cfg['DATABASE']['db_limit']
                    db_limit = int(db_limit) + 1

                    # Copy the database to archives
                    last_doc = edb.get(doc_id=int(len(edb)))
                    first_doc = edb.get(doc_id=2)
                    timeanddate = time.asctime(time.localtime(time.time())) and time.strftime("%H:%M:%S|%d-%b-%Y")


                    dbbkb_loc = cfg['PATH']['dbbkb_loc'] + 'DB_' + str(last_doc['OP_ID']) + ':\n[' + \
                                str(first_doc['Time&Date'][9:20]) + "]\n" \
                                                                    "[" + last_doc['Time&Date'][9:20] + ']\n.json'

                    copyfile(cfg['PATH']['edb_loc'] + 'events_db.json', dbbkb_loc)

                    # Erase the current database
                    edb.purge()

                    # Recreate the database
                    edb.insert({'black_log': last_doc['OP_ID'],
                                'db_limit': db_limit,
                                'db_birthday': timeanddate[9:20],
                                'db_last_date': str(last_doc['Time&Date'][9:20]),
                                'Description': 'The document#[1] will always be the configuration document of the db'})

                    unlucky = False
                    purge = False

                # ------------------------------------------------------------------------------------------------------
                # EXECUTION LOOP UNLOCK:
                ok = 1

        return info_var


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }
    }

    cherrypy.config.update({'server.socket_host': host_var,
                            'server.socket_port': port_var
                            })

    cherrypy.quickstart(TextToVoiceCallingService(), '/', conf)

