import ftplib
import logging
import os
import re
import sys
from sys import stderr

import telegram
from telegram import Update, Chat
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, CallbackContext, Filters

#configuring Logging
logging.basicConfig(
    level = logging.INFO,format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s,"
)
logger = logging.getLogger()


#################################
#                               #
#     ENVIRONMENT VARIABLES     #
#                               #
#################################
TOKEN = os.getenv('TOKEN')
if TOKEN is None:
    print("TOKEN environment variable is not specified",file=stderr)
    exit(1)

channel_id = int(os.getenv('channel_id'))

if channel_id is None:
    print("channel_id environment variable is not specified")
    exit(1)

if os.getenv('goat_id',None) is None:
    print("goat_id environment varible is not specified")
    exit(1)

goat_id = list(map(int,str(os.getenv('goat_id')).split(' ')))


main_dir = '/data/'
if os.getenv('LOCAL',None) is not None:
    main_dir = './'
    
unproc_file_name = main_dir + 'unprocessed'
resume_filename = main_dir + 'resume'
past_filename = main_dir + 'past'
#some telegram special chars
special_chars = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

def help_text():
    return '''
        /plus Annade un elemento a la lista de elementos disponibles
        FORMAT: /plus (Un titula mamado)[https://t.me/goatstuffs/123]
        
        /add Annade elementos al resumen
        -> arreglado error de espacio entre numeros [Ya no importa si pones cualquier caracter, el solo lee los numeros que pones]
        FORMAT: /add 1 2 3 4
        
        /remove Elimina elementos del resumen
        
        /build Muestra los elementos disponibles para annadir al resumen
        
        /pastlink Configura el link del ultimo Resumen
        FORMAT: /pastlink (256)[https://cubadebate.cu]
        
        /show Muestra el resumen actual
        
        /send Envia el resumen al canal
    
    '''

def parse_text(text):
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    ans = ''
    for i in text:
        if i in special_chars:
            ans += '\\'
        ans += i
    return ans


def new_unprocessed_post(link,title):
    assert(isinstance(link, str))
    assert(isinstance(title, str))
    
    try:
        unproc_file = open(unproc_file_name,'ab')
    except OSError:
        raise Exception('Could not open unprocessed posts file')
    else:
        post_obj = bytes(link,'utf-8') + b'\x00' + bytes(title,'utf-8') + b'\x01'
        if not unproc_file.write(post_obj) == len(post_obj):
            raise Exception('Could not write data to unprocessed file')
        else:
            unproc_file.close()
            return True
    

def get_unproc_posts():
    '''
    returns a list of al unprocessed posts link and title
    [(link,title),(link1,title1),...]
    '''
    try:
        unproc_file = open(unproc_file_name,'rb')
    except OSError:
        raise Exception('Could not open unprocessed file for reading data')
    else:
        search = re.findall(b'(https://t\\.me/[a-zA-Z_0-9]+/[0-9]+)\x00([^\x01]+)\x01',unproc_file.read(-1))
        unproc_file.close()

    return search


def get_unproc_posts_message():
    '''
    returns a list with unprocessed post messages
    '''

    posts = get_unproc_posts()
    print(posts)

    res = []
    curr = ''
    cnt = 1
    for post in posts:
        link = f'{cnt} \\- [{parse_text(post[1])}]({parse_text(post[0])})\n'
        if len(curr) + len(link) >= 4096:
            res.append(curr)
            curr = ''
        curr += link
        cnt += 1
    
    if len(curr) == 0:
        return []
    res.append(curr)

    return res

def new_resume_element(link,title):
    
    try:
        resume = open(resume_filename,'ab')
    except OSError:
        raise  Exception('Could not open resume file')
    else:
        resume_obj = bytes(link) + b'\x00' + bytes(title)  + b'\x01'

        if not resume.write(resume_obj) == len(resume_obj):
            raise Exception('Could not write data to file')
        else:
            return True

def get_resume_posts():

    try:
        resume = open(resume_filename,'rb')
    except OSError:
        raise Exception('Could not open a file')
    else:
        search = re.findall(b'(https://t\\.me/[a-zA-Z_0-9]+/[0-9]+)\x00([0-9]+)\x01',resume.read(-1))
        resume.close()
    
    res = []

    for m in search:
        a = m[0].decode('utf-8')
        b = m[1].decode('utf-8')
        res.append((a,b))

    return res

def get_past_link():
    '''
    returns the past resume link
    '''
    try:
        past = open(past_filename,'rb')
    except OSError:
        raise Exception('Could not open past link file')
    else:
        match = re.match(b'(https://t\\.me/[a-zA-Z_0-9]+/[0-9]+)\x00([0-9]+)',past.read(-1))
        if match is None:
            return ['https://t.me/GoatsStuffs', 0]
        return [match.group(1).decode('utf-8'),int(match.group(2).decode('utf-8'))]

def build_resume_text(curr_num):

    res = []

    past_resume = get_past_link()

    curr = f'「Rezumen {curr_num}」\n\n• [Resumen {past_resume[1]}]({past_resume[0]})\n\n'

    posts = get_resume_posts()

    for post in posts:
        resume = f'• [{parse_text(post[1])}]({post[0]}) \n\n'
        if len(curr) + len(resume) >= 4096:
            res.append(curr)
            curr = ''
        curr += resume
    resume = f'ⓘ • `Uza el #rezumen para navegar mejor por todo el kontenido del Kanal\\.`'
    if len(curr) + len(resume) >= 4096:
        res.append(curr)
        curr = ''
    curr += resume

    res.append(curr)

    return res

    
def update_past_link(link,num):
    '''
    updates past resume link
    '''
    try:
        past = open(past_filename,'wb')
    except OSError:
        raise Exception('Could not open past link file')
    else:
        past.write(bytes(link,'utf-8') + b'\x00' + bytes(num,'utf-8'))
        return True
    




def remove_unprocessed():
    '''
    Delete file content 
    '''
    try:
        unproc_file = open(unproc_file_name,'w')
    except Exception:
        return False
    else:
        unproc_file.close()
        return True

def remove_resume():
    '''
    Delete file content 
    '''
    try:
        resume = open(resume_filename,'w')
    except Exception:
        return False
    else:
        resume.close()
        return True


#################################
#                               #
#   Command Handlers functions  #
#                               #
#################################

def help(update: Update, ctxt: CallbackContext):
    text = help_text()
    update.effective_chat.send_message(text)

#handles channel posts
def process_channel_post(update:Update,ctxt:CallbackContext):
    '''
    process channel post
    '''
    if update.effective_chat.type not in (Chat.CHANNEL,):
        return None
    if update.effective_chat.id not in (channel_id,):
        return None
    try:
        post_title = update.effective_message.text
        if post_title is None:
            post_title = update.effective_message.caption
        
        pos = post_title.find('\n')
        if pos == -1:
            pos = len(post_title)

        post_title = post_title[:pos]
    except Exception as e:
        print(e)
        return None
    
    post_link = f'https://t.me/{update.effective_chat.username}/{update.effective_message.message_id}'

    new_unprocessed_post(post_link, post_title)

#builds resume
def build(update:Update,ctxt:CallbackContext):
    '''
    shows unprocessed posts
    '''
    update.effective_chat.send_message(
        text = 'A continuacion los posts disponibles. Para añadir uno al resumen use el comando /add'
    )

    unproc_message_posts = get_unproc_posts_message()

    print(unproc_message_posts)

    for msg in unproc_message_posts:
        update.effective_chat.send_message(
            text = msg,
            parse_mode='MarkdownV2',
            disable_web_page_preview=True
        )
    
    if len(unproc_message_posts) == 0:
        update.effective_chat.send_message(
            text = 'No hay posts nuevos',
            disable_web_page_preview=True
        )


#sends resume to channel
def send(update,ctxt):
    '''
    sends resume to channel
    ''' 
    past_resume = get_past_link()
    curr_resume = build_resume_text(past_resume[1] + 1)

    link = None

    for message in curr_resume:
        message = ctxt.bot.send_message(
            chat_id = channel_id,
            text = message,
            parse_mode = 'MarkdownV2',
            disable_web_page_preview = True
        )
        if link is None:
            link = f'https://t.me/{message.chat.username}/{message.message_id}'

    update_past_link(link, str(past_resume[1] + 1))
    remove_resume()
    remove_unprocessed()

    update.effective_chat.send_message(
        text = 'Enviado correctamente'
    )

#show current resume
def show(update,context):
    '''
    shows current resume
    '''
    past_resume = get_past_link()
    
    curr_resume = build_resume_text(past_resume[1] + 1)

    for message in curr_resume:
        update.effective_chat.send_message(
            text = message,
            parse_mode = 'MarkdownV2',
            disable_web_page_preview = True
        )

    


def add(update:Update,ctxt:CallbackContext):
    '''
    add elemets to resume.
    command:
    /add a_1 [ a_2 [ a_3 ...]]
    add element a_1 a_2 a_3 to resume
    '''

    elements = re.findall(r'[0-9]+', update.effective_message.text)

    elements = list(map(int, elements))

    unproc_elements = get_unproc_posts()

    cnt = 0

    for i in elements:
        try:
            new_resume_element(unproc_elements[i-1][0], unproc_elements[i-1][1])
        except IndexError:
            pass
        else:
            cnt += 1

    update.effective_chat.send_message(
        text = f'añadidos {cnt} elementos'
    )




def remove(update,context):
    '''
    remove an element from resume    
    command:
    /remove a_1 [ a_2 [ a_3]]
    remove elements a_1 a_2 a_3 from resume
    '''

    elements = re.findall(r'[0-9]+', update.effective_message.text)
    elements = list(map(int, elements))

    resume_posts = get_resume_posts()

    cnt = 0

    for i in elements:
        try:
            resume_posts.pop(i-1)
        except IndexError:
            pass
        else:
            cnt += 1
        
    try:
        resume = open(resume_filename,'wb')
    except OSError:
        raise Exception('Could not open resume file')
    else:
        for i in resume_posts:
            resume.write(i[0] + b'\x00' + i[1] + b'\x01')
        resume.close()

    update.effective_chat.send_message(
        text = f'removidos {cnt} elementos'
    )
    



#adds elements to resume manualy
def plus(update,context):
    '''
    El comando se usa de la siguiente manera:
    /plus (*post_title*)[*post_link*]
    '''

    match = re.match(r'/plus \(([\w\W]+)\)\[([\w\W]+)\]',update.effective_message.text)

    if match is None:
        update.effective_chat.send_message(
            text = 'Formato incorrecto'
        )
        return None

    if new_unprocessed_post(match.group(2), match.group(1)):
        update.effective_chat.send_message(
            text = 'añadido correctamente'
        )


    
    
    
def edit_past_link(update,context):
    '''
    el comando se usa de la siguiente manera:
    /pastlink (*numero_de_resumen_actual*)[*link_del_anterior_resumen*]
    '''
    match = re.match(r'/pastlink \(([\w\W]+)\)\[([\w\W]+)\]',update.message.text)

    if match is None:
        update.effective_chat.send_message(
            text = 'Formato incorrecto'
        )
        return None

    if update_past_link(match.group(2), match.group(1)):
        update.effective_chat.send_message(
            text = 'añadido correctamente'
        )



def error_handler(update,context):
    CHAT_ID = update.effective_chat.id
    context.bot.send_message(
        chat_id = goaty_id[0],
        text = str(sys.exc_info())
    )


if __name__ == '__main__':
    my_bot = telegram.Bot(token = TOKEN)

updater = Updater(my_bot.token,use_context = True);
dp = updater.dispatcher

dp.add_handler(CommandHandler("build",build, filters= Filters.chat(chat_id = goat_id )))#sends a message of available post
dp.add_handler(CommandHandler("send",send, filters= Filters.chat(chat_id = goat_id)))#sends resume to channel
dp.add_handler(CommandHandler("show",show, filters= Filters.chat(chat_id = goat_id)))#show current resume
dp.add_handler(CommandHandler("add",add, filters= Filters.chat(chat_id = goat_id)))#adds element to resume
dp.add_handler(CommandHandler('remove',remove, filters= Filters.chat(chat_id = goat_id)))#remove element from resume
dp.add_handler(CommandHandler('plus',plus, filters= Filters.chat(chat_id = goat_id)))#adds element manualy
dp.add_handler(CommandHandler('pastlink',edit_past_link, filters= Filters.chat(chat_id = goat_id)))# edit last resume link stuff
dp.add_handler(CommandHandler('help', help, filters= Filters.chat(chat_id = goat_id)))
dp.add_handler(MessageHandler(Filters.all,process_channel_post))
dp.add_handler(MessageHandler(Filters.photo,process_channel_post))
dp.add_error_handler(error_handler)


updater.start_polling()

updater.idle()

