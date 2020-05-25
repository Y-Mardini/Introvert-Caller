import requests
import json
import os
import configparser

# 621739081
# 621478554 Alex
# 24243494 Shenglan (美丽优于丑陋)
# 621358217 Moh
language_code = {
    "Afrikaans":'af',
    "Arabic":'ar',
    "Armenian":'hy',
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


def print_codes():

    print ("Accepted Codes By GOOGLE API: \n")
    for i in language_code:
        print ('%-14s%-1s' % (i , language_code[i]))


def welcome_text():
    print ( """
Introvert Caller V1.0                                Copyright (c) Quarkania Productions 2019                   
                    ___________
                   /.---------.\`-._
                  //          ||    `-._
                  || `-._     ||        `-._
                  ||     `-._ ||            `-.
                  ||    _____ ||`-._           |
            _..._ ||   | __ ! ||    `-._       |
          _/     \||   .'  |~~||        `-._   |
      .-``     _.`||  /  __|~~||    .----.  `-.|
     |      _.`  _|| |  |123| ||   / :::: \    |
     \ _.--`  _.` || |  |456| ||  / ::::: |    |
      |   _.-`  _.|| |  |879| ||  |   _..-'    |
      _\-`   _.`O || |  |_0_| ||  |::|         |
    .`    _.`O `._||  \    |  ||  |::|         |
 .-`   _.` `._.'  ||   '.__|--||  |::|         |
`-._.-` \`-._     ||   | ":  !||  |  '-.._     |
         \   `--._||   |_:"___||  | ::::: |    |
          \  /\   ||     ":":"||   \ :::: |    |
           \(  `-.||       .- ||    `.___/     |
           |    | ||   _.-    ||               |
           |    / ||.-________||____.....------'
           \    -.      \ |         |
            \     `.     \ \        | 
 __________  `.    .'\    \|        |\  _________
              `..'   \    |        | \          
                     .'    |       /  .`.
                | \.'      |       |.'   `-._
                 \     _ . /       \_\-._____)
                  \_.-`  .`'._____.'`.
                    \_\-|             |
                         `._________.'
            
            """
    )


config_loc = os.path.abspath('.') + '/configuration.ini'

cfg = configparser.ConfigParser()
cfg = configparser.ConfigParser()
cfg.read(config_loc)

host_var = str(cfg['SERVER']['server_socket_host'])
port_var = str(cfg['SERVER']['server_socket_port'])

url_var = 'http://'+host_var+':'+port_var+'/'

option = 0

welcome_text()

while option != 3:

    option = int(input("(1) Message by Call"
                       "\n(2) Get Call Record "
                        "\n(3) Exit"
                       "\n\n(Enter Option Number): ") or "0")


    if option == 1:
            print("\n--------------------------------------------------------------------------------------")
            phone = str(input("Phone Number: ") or "661978178")
            text = str(input("Text Message: ") or "Alert!")
            repetitions = str (input("Number of Voice Message Rpeatations: ") or "2")
            language = str(input("Language (AUTO by default): ") or "en")
            print ("\n--------------------------------------------------------------------------------------")

            s = requests.Session()
            post_data = {
                    'phone': phone,
                    'text': text,
                    'repetitions': repetitions,
                    'language': language
                    }

            r = s.post(url_var, json=post_data, headers={'Accept': 'application/json'})

            # Alternative approach: r = requests.post(url_var, data = {'phone':phone, 'text':text})
            print('Status('+str(r.status_code)+')')
            print("\n--------------------------------------------------------------------------------------")
            if r.status_code == 200:
                response = r.json()
                print(response)
                if "language code" in response:
                    print_codes()
                print("\n--------------------------------------------------------------------------------------")

    elif option == 2:
        print("\n--------------------------------------------------------------------------------------")
        get_id = str(input("Record ID (Press 0 to get all the records): ") or "2")
        print("\n--------------------------------------------------------------------------------------")

        s = requests.Session()
        get_data = {'get_id': get_id}

        r = s.put(url_var, json=get_data, headers={'Accept': 'application/json'})


        print('Status(' + str(r.status_code) + ')')
        print("\n--------------------------------------------------------------------------------------")
        if r.status_code == 200:
            response = r.json()
            print(response)
            print("\n--------------------------------------------------------------------------------------")

    elif option == 3:

        print("Bye")
        break

    elif option == 0:
        print("")


    else:
        print (
            "\nxxxxxxxxxxxxxx"
            "\nInvalid Input!"
            "\nxxxxxxxxxxxxxx"
            "\n--------------------------------------------------------------------------------------"
            "\n")

