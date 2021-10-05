import logging
import os,re
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
channel_id = int(os.getenv('channel_id'))
goat_id = int(os.getenv('goat_id'))



special_chars = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
link_chars = '[]()'

def fix(String:str) -> str:
    ans = ''
    ant = ''
    flag = False
    isIn = False
    for i in String:
        if i == '[':
            isIn = True
        if i == ']':
            isIn = False
        if isIn and i == '.':
            ans += '\\' + '.'
            continue
        if i in '[(':
            flag = True
        elif i in '])':
            flag = False
        if i == '~':
            ant = i
            continue
        if i == '.' and flag == True:
            ans += i
            continue
        if i not in special_chars or ant == '~':
            ans += i
        elif i not in link_chars:
            ans += str('\\')
            ans += i
        else:
            ans += i
        ant = i
    return ans


def sendMessage(update,context,text):
    chatId = update.message['chat']['id']
    return context.bot.sendMessage(chat_id = chatId,parse_mode = "MarkdownV2",text = fix(text),disable_web_page_preview=True)

def sendMessageById(Id,context,text):
    return context.bot.sendMessage(chat_id = Id,parse_mode = "MarkdownV2",text = fix(text),disable_web_page_preview =True)

def get_past_link():
    #return (14,'https://t.me/unCanalWe/56')
    try:
        arc = open(past,'r')
        number = arc.readline()
        if number[-1] == '\n':
            number = number[:-1]
        link = arc.readline()
        if link[-1] == '\n':
            link = link[:-1]
        return (int(number),link)
        arc.close()
    except:
        return (14,'https://t.me/unCanalWe/56')
    return None

def save_link(curr_num,link):
    try:
        arc = open(past,'w')
        arc.write(str(curr_num))
        arc.write('\n')
        arc.write(link)
        arc.write('\n')
        arc.close()
    except:
        return False
    return True

def build_resume_text(delete=False):
    num,pastLink = get_past_link()
    ans = f'「Rezumen {num+1}」\n\n•*[Rezumen {num}]({pastLink})*\n\n'
    try:
        arc = open(resume,'r',encoding='utf-8')
    except FileNotFoundError:
        arc = open(resume,'w')
        arc.close()
        arc = open(resume,'r',encoding='utf-8')
    for line in arc:
        ans += '• *' + line + '*\n'
    arc.close()
    ans += 'ⓘ • ~`Uza el~` #rezumen ~`para navegar mejor por todo el kontenido del Kanal.~`'
    if delete:
        arc = open(resume,'w')
        arc.close()
    return ans


#add element to File
def add_element(element):
    arc = open(resume,'a',encoding='utf-8')
    arc.write(element)
    arc.close()

def remove_element(element_idx):
    try:
        arc = open(resume,'r',encoding='utf-8')
    except FileNotFoundError:
        arc = open(resume,'w')
        arc.close()
        arc = open(resume,'r',encoding='utf-8')

    cnt = 1
    ans = ''
    for line in arc:
        if cnt == element_idx:
            continue
        cnt += 1
        ans += line
    arc.close()
    arc = open(resume,'w')
    arc.close()
    add_element(ans)

def send_resume(update,context,text):
    return sendMessageById(channel_id,context,text)

#add unprocessed post element to file
def add_unproc_post(update):
    message_id = update.channel_post['message_id']
    channel_name = update.channel_post['sender_chat']['username']
    Link = f'https://t.me/{channel_name}/{message_id}'
    caption = update.channel_post['text']
    element_name = ''
    for i in caption:
        if i == '\n':
            break
        element_name += i
    arc = open(unprocessed,'a',encoding='utf-8')
    arc.write(f'[{element_name}]({Link})\n')
    arc.close()

#get unprocessed posts from file
def get_unproc_post():
    try:
        arc = open(unprocessed,'r',encoding='utf-8')
    except FileNotFoundError:
        arc = open(unprocessed,'w')
        arc.close()
        arc = open(unprocessed,'r',encoding='utf-8')
    ans = ''
    cnt = 1
    for line in arc:
        ans += str(cnt) + '- ' + line
        cnt += 1
    arc.close()
    return ans
def remove_unprocessed():
    arc = open(unprocessed,'w')
    arc.close()

def validate_post(update):
    print(update.channel_post['sender_chat']['id'],goat_id)
    return int(update.channel_post['sender_chat']['id']) == goat_id

def validate_command(update):
    return int(update.message['chat']['id']) == goat_id

#################################
#                               #
#   Command Handlers functions  #
#                               #
#################################
def recv_msg(update,context):
    if update.channel_post is not None:
        print(validate_post(update))
        if validate_post(update):
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

#sends resume to channel
def send(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return
    texto = build_resume_text(True)
    Message = send_resume(update,context,texto)
    sendMessage(update,context,'Resumen enviado!')
    save_link(get_past_link()[0]+1,f'https://t.me/{Message.chat.username}/{Message.message_id}')
    remove_unprocessed()    

def show(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return
    text = build_resume_text()
    sendMessage(update,context,text)
    sendMessage(update,context,f'Para eliminar un elemento use el comando /remove.Para enviar el resumen use el comando /send')

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
        arc = open(unprocessed,'r',encoding='utf-8')
    except FileNotFoundError:
        arc = open(unprocessed,'w')
        arc.close()
        arc = open(unprocessed,'r',encoding='utf-8')

    list_items = [line for line in arc]
    arc.close()
    items = [int(i) for i in caption.split(' ')]
    for item in items:
        add_element(list_items[item-1])
    sendMessage(update,context,f'Elementos añadidos!')
    
def remove(update,context):
    if not validate_command(update):
        sendMessage(update,context,f'Este bot no lo puedes usar')
        return

    caption = update.message['text'][7:].strip()
    if len(caption) == 0:
        sendMessage(update,context,f'Formato incorrecto')
        return
        
    items = [int(i) for i in caption.split(' ')]
    for i in items:
        remove_element(i)
    sendMessage(update,context,f'Eliminado!')
if __name__ == '__main__':
    my_bot = telegram.Bot(token = TOKEN)

updater = Updater(my_bot.token,use_context = True);
dp = updater.dispatcher

dp.add_handler(CommandHandler("build",build))
dp.add_handler(CommandHandler("send",send))
dp.add_handler(CommandHandler("show",show))
dp.add_handler(CommandHandler("add",add))
dp.add_handler(CommandHandler('remove',remove))
dp.add_handler(MessageHandler(Filters.text,recv_msg))

heroku_app_name = os.getenv("HEROKU_APP_NAME")
PORT = int(os.environ.get("PORT","8443"))
updater.start_webhook(listen="0.0.0.0",port=PORT,url_path=TOKEN,webhook_url=f"https://{heroku_app_name}.herokuapp.com/{TOKEN}")
