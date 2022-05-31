#Stuff to be Done: add regex 

import logging
import os,re,ftplib,urllib.request,sys
import telegram
from telegram.ext import Updater,CommandHandler,MessageHandler,Filters 
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
unprocessed = os.getenv('unprocessed')
resume = os.getenv('resume')
past = os.getenv('past')
channel_id = os.getenv('channel_id')
goat_id = list(map(int,str(os.getenv('goat_id')).split(' ')))
#FTP variables
host = os.getenv('host')
username = os.getenv('username')
password = os.getenv('password')
###END#####
#ftplib.error_perm

def max(x,y):
    if x > y:
        return x
    return y

#Uploads File to FTP server
def upload_file(destiny_file,origin_file):
    site_address = os.getenv('site_address') or 'http://www.python.org/'
    urllib.request.urlopen(site_address)
    
    session = ftplib.FTP(host, username, password)
    try:
        file = open(origin_file, 'rb')  # file to send
    except FileNotFoundError:
        file = open(origin_file,'w')
        file.close()
        file = open(origin_file,'rb')
        print(destiny_file)
    session.storbinary('STOR '+destiny_file, file)  # send the file
    session.quit()
    file.close()  # close file and FTP session
    
#download file from FTP server
def download_file(filename,open_type='a',encoding=True):
    site_address = os.getenv('site_address') or 'http://www.python.org/'
    urllib.request.urlopen(site_address)
    
    session = ftplib.FTP(host, username, password)
    localfile = filename[max(filename.rfind('/')+1,0):] 
    f = open(localfile, 'wb')  # save into local file
    try:
        session.retrbinary('RETR ' + filename, f.write, 2048)
    except ftplib.error_perm: #if file not in FTP
        f.close()
        if encoding:
            return open(localfile,open_type,encoding='utf-8')
        else:
            return open(localfile,open_type)

    f.close()  # close file and FTP session
    session.quit()
    if encoding:
        return open(localfile,open_type,encoding='utf-8') 
    else:
        return open(localfile,open_type)

#some telegram special chars
special_chars = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

def parse_text(text):
    ans = ''
    for i in text:
        if i in special_chars:
            ans += '\\'
        ans += i
    return ans


def parse_link(text):
    re_exp = r'\[(.*)\](\(https://[a-zA-Z0-9/.?_]+\))'
    match = re.match(re_exp,text)
    if match is None:
        raise Exception
    return f'[{parse_text(match.group(1))}]{match.group(2)}'



link_chars = '[]()'


def sendMessage(update,context,text):
    chatId = update.message['chat']['id']
    try:
        return context.bot.sendMessage(chat_id = chatId,parse_mode = "MarkdownV2",text = text,disable_web_page_preview=True)
    except:
        print('<-ERROR->',text,type(text))
        return -1
    
def sendMessageById(Id,context,text):
    try:
        return context.bot.sendMessage(chat_id = Id,parse_mode = "MarkdownV2",text = text,disable_web_page_preview =True)
    except:
        print('<-ERROR->  ',text,type(text))
        return -1
    
#returns link of last resume
def get_past_link():
    try:
        arc = download_file(f"htdocs/goaty_robot/{past}",'r')
        number = arc.readline()
        if number[-1] == '\n':
            number = number[:-1]
        link = arc.readline()
        if link[-1] == '\n':
            link = link[:-1]
        return (int(number),link)
        arc.close()
        upload_file(f"htdocs/goaty_robot/{past}",past)
    except:
        return (14,'https://t.me/unCanalWe/56')
    return None

#saves link of sent resume
def save_link(curr_num,link):
    try:
        arc = download_file(f"htdocs/goaty_robot/{past}",'w')
        arc.write(str(curr_num))
        arc.write('\n')
        arc.write(link)
        arc.write('\n')
        arc.close()
        upload_file(f"htdocs/goaty_robot/{past}",past)
    except:
        return False
    return True

#builds resume text
def build_resume_text(delete=False):
    num,pastLink = get_past_link()
    ans = f'「Rezumen {parse_text(str(num+1))}」\n\n•*[Rezumen {parse_text(str(num))}]({pastLink})*\n\n'
    arc = download_file(f"htdocs/goaty_robot/{resume}",open_type="r")
    res = []
    for line in arc:
        try:
            parsed_link = parse_link(line)
        except:
            print(f'Error : {line}')
            continue
        if len(ans + '• *' + parsed_link + '*\n') >= 4096:
            res.append(ans)
            ans = ''
        ans += '• *' + parse_link(line) + '*\n\n'
    ans += '\nⓘ • `Uza el` \\#rezumen `para navegar mejor por todo el kontenido del Kanal\\.`'
    res.append(ans)
    arc.close()
    upload_file(f"htdocs/goaty_robot/{resume}",resume)
    
    if delete:
        arc = open(resume,'w')
        arc.close()
        upload_file(f"htdocs/goaty_robot/{resume}",resume)
    return res


#add element to resume
def add_element(element):
    arc = download_file(f"htdocs/goaty_robot/{resume}")
    arc.write(element)
    arc.close()
    upload_file(f"htdocs/goaty_robot/{resume}",resume)

#removes element from resume
def remove_element(element_idx):
    arc = download_file(f"htdocs/goaty_robot/{resume}",open_type='r')

    cnt = 1
    ans = ''
    for line in arc:
        if cnt == element_idx:
            cnt+=1
            continue
        cnt += 1
        ans += line
    arc.close()
    arc = open(resume,'w')
    arc.close()
    upload_file(f"htdocs/goaty_robot/{resume}",resume)
    add_element(ans)

#sends resume to channel
def send_resume(update,context,text):
    ans = sendMessageById(channel_id,context,text[0])
    for value in text[1:]:
        sendMessageById(channel_id,context,value)
    return value

#add unprocessed post element to file
def add_unproc_post(update=None,link=None,name=None):
    #this functions is used to add manualy or automatic
    #by recving channel post
    if name==None and link == None and update == None:
        return
    if update == None and link is not None and name is not None: #adding element entered manualy
        arc = download_file(f"htdocs/goaty_robot/{unprocessed}")
        arc.write(f'[{name}]({link})\n')
        arc.close()
        upload_file(f"htdocs/goaty_robot/{unprocessed}",unprocessed)
    if update == None:
        return
    message_id = update.channel_post['message_id']
    channel_name = update.channel_post['sender_chat']['username'] or update.channel_post['sender_chat']['title'] or update.channel_post['chat']['title']  
    Link = f'https://t.me/{channel_name}/{message_id}'
    caption = update.channel_post['text']
    if caption == None:
        caption = update.channel_post['caption']
    element_name = ''
    for i in caption:
        if i == '\n':
            break
        element_name += i
    arc = download_file(f"htdocs/goaty_robot/{unprocessed}")
    arc.write(f'[{element_name}]({Link})\n')
    arc.close()
    upload_file(f"htdocs/goaty_robot/{unprocessed}",unprocessed)

#get unprocessed posts from file
def get_unproc_post():
    arc = download_file(f"htdocs/goaty_robot/{unprocessed}",open_type='r')
    ans = ''
    res = []
    cnt = 1
    for line in arc:
        try:
            parsed_link = parse_link(line)
        except:
            res.append(f'no se pudo parsear el link siguiente: {parse_text(line)}')
            continue
        if len(ans + parse_text(str(cnt)) + '\\- ' + parsed_link) >= 4096:
            res.append(ans)
            ans = ''
        ans += parse_text(str(cnt)) + '\\- ' + parse_link(line) + '\n'
        cnt += 1
    res.append(ans)
    arc.close()
    return res

#deletes not used posts
def remove_unprocessed():
    arc = open(unprocessed,'w')
    arc.close()
    upload_file(f"htdocs/goaty_robot/{unprocessed}",unprocessed)

#if post is from goat's channel
def validate_post(update):
    return update.channel_post['sender_chat']['id'] == channel_id

#if command is goat's
def validate_command(update):
    print(goat_id)
    return update.message['chat']['id'] in goat_id

#################################
#                               #
#   Command Handlers functions  #
#                               #
#################################

#handles channel posts
def recv_msg(update,context):
    print(update)
    if update.channel_post is not None:
        if validate_post(update):
            print(update)
            add_unproc_post(update)

#builds resume
def build(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return
    sendMessage(update,context,'A continuacion los posts disponibles,\nPara añadir uno al resumen use el comando /add')
    texto = get_unproc_post()
    if len(texto) == 0:
        texto = f'No hay posts nuevos'
        sendMessage(update,context,texto)
        return
    for msg in texto:
        sendMessage(update,context,msg)

#sends resume to channel
def send(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return
    texto = build_resume_text(True)
    Message = send_resume(update,context,texto)
    sendMessage(update,context,parse_text('Resumen enviado!'))
    save_link(get_past_link()[0]+1,f'https://t.me/{Message.chat.username}/{Message.message_id}')
    remove_unprocessed()    

#show current resume
def show(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return
    texto = build_resume_text()
    for text in texto:
        sendMessage(update,context,text)
    sendMessage(update,context,f'Para eliminar un elemento use el comando /remove\\.Para enviar el resumen use el comando /send')

#adds element to resume
def add(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return

    caption = update.message['text'][4:].strip()
    if len(caption) == 0:
        sendMessage(update,context,f'Formato incorrecto')
        return
    try:
        arc = download_file(f"htdocs/goaty_robot/{unprocessed}",open_type='r')
    except FileNotFoundError:
        arc = open(unprocessed,'w')
        arc.close()
        arc = open(unprocessed,'r',encoding='utf-8')

    list_items = [line for line in arc]
    arc.close()
    items = [int(i) for i in caption.split(' ')]
    for item in items:
        add_element(list_items[item-1])
    sendMessage(update,context,f'Elementos añadidos\\!')

#handles removal of elements from resume
def remove(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return

    caption = update.message['text'][7:].strip()
    items = [int(i) for i in caption.split(' ')]
    for i in items:
        remove_element(i)
    sendMessage(update,context,f'Eliminado\\!')

#adds elements to resume manualy
def plus(update,context):
    '''
    El comando se usa de la siguiente manera:
    /plus (*post_name*)[*post_link*]
    '''
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return

    caption = update.message['text'][5:].strip()
    isIn = [False,False]
    name,link = "",""
    for i in caption:
        if i == ']':
            isIn[1] = False
        if i == ')':
            isIn[0] = False
        if isIn[0]:
            name += i
        if isIn[1]:
            link += i
        if i == '(':
            isIn[0] = True
        if i == '[':
            isIn[1] = True
    
    add_unproc_post(link=link,name=name)
    sendMessage(update,context,"Elemento añadido a la lista de Posts disponibles")
    
    
def edit_past_link(update,context):
    '''
    el comando se usa de la siguiente manera:
    /pastlink (*numero_de_resumen_actual*)[*link_del_anterior_resumen*]
    '''
    caption = update.message['text'][9:].strip()
    isIn = [False,False]
    number,link = "",""
    for i in caption:
        if i == ']':
            isIn[1] = False
        if i == ')':
            isIn[0] = False
        if isIn[0]:
            number += i
        if isIn[1]:
            link += i
        if i == '(':
            isIn[0] = True
        if i == '[':
            isIn[1] = True    
    number = int(number)
    save_link(number-1,link)

def backup_resume(update,context):
    CHAT_ID = update.message.chat.id
    if CHAT_ID not in goat_id:
        context.bot.send_message(chat_id = CHAT_ID,text='No puedes usar este bot')
        return 

    v = download_file(f'htdocs/goaty_robot/{resume}','rb',encoding=False)
    if len(v.read()) > 0:
        context.bot.send_document(
            chat_id = CHAT_ID,
            document = open('resume.txt','rb'),
            filename="past.txt"
        )
    else :
        context.bot.send_message(
            chat_id = CHAT_ID,
            text = 'No hay nada en el resumen.'
        )

    v = download_file(f'htdocs/goaty_robot/{unprocessed}','rb',encoding=False)
    if len(v.read()) > 0:
        context.bot.send_document(
            chat_id = CHAT_ID,
            document = open(unprocessed,'rb')
        )
    else:
        context.bot.send_message(
            chat_id = CHAT_ID,
            text = 'No hay post nuevos.'
        )

def error_handler(update,context):
    CHAT_ID = update.effective_chat.id
    context.bot.send_message(
        chat_id = CHAT_ID,
        text = str(sys.exc_info())
    )


if __name__ == '__main__':
    my_bot = telegram.Bot(token = TOKEN)

updater = Updater(my_bot.token,use_context = True);
dp = updater.dispatcher

dp.add_handler(CommandHandler("build",build))#sends a message of available post
dp.add_handler(CommandHandler("send",send))#sends resume to channel
dp.add_handler(CommandHandler("show",show))#show current resume
dp.add_handler(CommandHandler("add",add))#adds element to resume
dp.add_handler(CommandHandler('remove',remove))#remove element from resume
dp.add_handler(CommandHandler('plus',plus))#adds element manualy
dp.add_handler(CommandHandler('pastlink',edit_past_link))# edit last resume link stuff
dp.add_handler(CommandHandler('backup',backup_resume))
dp.add_handler(MessageHandler(Filters.text,recv_msg))
dp.add_handler(MessageHandler(Filters.photo,recv_msg))
dp.add_error_handler(error_handler)



heroku_app_name = os.getenv("HEROKU_APP_NAME")
PORT = int(os.environ.get("PORT","8443"))
updater.start_webhook(listen="0.0.0.0",port=PORT,url_path=TOKEN,webhook_url=f"https://{heroku_app_name}.herokuapp.com/{TOKEN}")

