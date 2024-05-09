import discord
from datetime import datetime
import asyncio
import requests
import json
import pytz
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
# 2040502 전민
itemids = [2040502]
tasks = {}
headers = {
    'next-action': '18c69a5b48b5955f6c4f162a815cbd62b87313bb',
}
url = 'https://mapleland.gg/item/%7Bitemid%7D'


def fetch_data(url=url, headers=headers, data=''):
    response = requests.post(url, headers=headers, data=data)
    response.encoding = 'utf-8'
    try:
        datas = json.loads(response.text.split('\n')[1][2:])
        return datas
    except json.JSONDecodeError:
        print("JSON 데이터 파싱 에러")
        return None

def process_data(datas):
    lis = []
    for info in datas:
        tradetype = info['tradeType']
        tradeStatus = info['tradeStatus']
        if tradetype == 'sell' or not tradeStatus:
            continue
        id = info['traderDiscordInfo']["id"]
        global_name = info['traderDiscordInfo']["global_name"]
        provider_id = info['traderDiscordInfo']['provider_id']
        itemName = info['itemName']
        itemPrice = info['itemPrice']
        itemQuantity = info['tradeOption']['each']
        date_str = info['created_at']
        date_str_no_micro = date_str.split('.')[0] + date_str[-6:]
        given_time = datetime.fromisoformat(date_str_no_micro).astimezone(pytz.utc)
        current_time = datetime.now(pytz.utc)
        time_difference = current_time - given_time

        lis.append({
            "itemName": itemName,
            "tradeType": tradetype,
            "itemPrice": itemPrice,
            "itemQuantity": itemQuantity,
            "timeDifference": time_difference,
            "id": id,
            "providerId": provider_id,
            "globalName": global_name
        })
    return lis

# 환경 변수 읽기
token = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = 1209697351128850454
TOKEN = token

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(status=discord.Status.online, activity=discord.Game("민성이 시다바리"))

@client.event
async def on_message(message):
    channel = client.get_channel(CHANNEL_ID)
    if message.author == client.user:
        return

    if message.content == "짖어":
         await channel.send("멍멍")

    if message.content == "손":
         await channel.send("챱")

    if message.content == "엄":
         await channel.send("준식")
    if message.content == "종료":
        for itemid in itemids:
            if itemid in tasks:
                tasks[itemid].cancel()
                await channel.send(f"{itemid} cancel")

    if message.content == "전민10":
        data = '["itemid",{},false]'.replace('itemid', str(2040502))
        datas = fetch_data(data=data)
        if not datas:
             await channel.send("데이터 없음")
             return
        lis = process_data(datas)
        if not lis:
            await channel.send("데이터 없음")
            return
        try:
            lis = sorted(lis, key=lambda x: x['timeDifference'])
        except:
            pass
        txt = ''
        for cur_user in lis:
            user_name = cur_user['globalName']
            if user_name == '':
                user_name = "unknown"
            txt += f"{user_name}, {cur_user['itemPrice']}메소 \n"
        await channel.send(txt)


    if message.content == "시작":
        await channel.send(f"전민10, 엄준식 알림 시작")
        for itemid in itemids:
            if itemid in tasks:
                print(f'func on_message"{itemid} cancel')
                tasks[itemid].cancel()  # 이미 실행 중인 태스크 취소
            tasks[itemid] = client.loop.create_task(send_periodic_message(itemid))  # 새 태스크 생성 및 저장




async def send_periodic_message(itemid):
    channel = client.get_channel(CHANNEL_ID)
    top_user = ''
    print(f"func send_periodic_message obverver {itemid}")
    while True:
        try:
            data = '["itemid",{},false]'.replace('itemid', str(itemid))
            datas = fetch_data(data=data)
            if not datas:
                continue

            lis = process_data(datas)
            if not lis:
                continue

            lis = sorted(lis, key=lambda x: x['timeDifference'])
            if top_user == lis[0]["id"]:
                continue

            top_user = lis[0]["id"]
            if top_user != lis[1]["id"]:
                cur_user = lis[0]
                await channel.send(f"{cur_user['itemName']}, {cur_user['itemPrice']}메소,  새로운 최상위 판매자: [{cur_user['globalName']}](discord://discord.com/users/{cur_user['providerId']})")
        except Exception as e:
            pass
        finally:
            await asyncio.sleep(10)


client.run(TOKEN)
