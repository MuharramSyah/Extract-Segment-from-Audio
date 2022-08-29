import os
import spacy
from subprocess import run
from sr import Speech
from telethon import TelegramClient, events, utils
import asyncio
from pydub import AudioSegment
from configparser import ConfigParser
from arcgis.gis import GIS

configparser = ConfigParser()
configparser.read('config.ini')

api_id = configparser.getint('telegram', 'api_id')
api_hash = configparser.get('telegram', 'api_hash')
api_name = configparser.get('telegram', 'api_name')
api_token = configparser.get('telegram', 'api_token')
channel = configparser.get('telegram', 'channel_url')
portal = configparser.get('arcgis', 'portal')
username = configparser.get('arcgis', 'username')
password = configparser.get('arcgis', 'password')
model_path = configparser.get('model', 'model_path')
segment_lane_fs = configparser.get('arcgis', 'segment_lane_fs')

gis = GIS(portal=portal, username=username, password=password)
fs_lane = gis.content.get(segment_lane_fs)
nlp = spacy.load(model_path)

sr = Speech()
client = TelegramClient(api_name, api_id, api_hash)
client.start(bot_token=api_token)


def merge_dicts(dicts):
    """
    :param dicts:
    :return:
    """
    d = {}
    for dict in dicts:
        for key in dict:
            try:
                d[key].append(dict[key])
            except KeyError:
                d[key] = [dict[key]]
    return d


def extract(doc):
    """
    :param doc:
    :return:
    """
    dict_ = list()
    for ent in doc.ents:
        dict_.append({ent.label_: ent.text})
    out = merge_dicts(dict_)
    if len(dict_) == 0:
        return ''
    return out


def extract_segment(segment):
    """

    :param segment:
    :return:
    """
    segment = segment.split(',')[0]
    track = segment[-1:]
    km = int(''.join(i for i in segment if i.isdigit()))
    if km < 1000:
        km *= 1000

    if track.isdigit():
        track = ''

    return km, track


def get_geometry(kilometer):
    """
    :param kilometer:
    :return:
    """
    segment, track = extract_segment(kilometer)
    where = "route_name='{}{}'".format(segment, track)
    output = fs_lane.query(where=where)
    if len(output.sdf) <= 0:
        return None
    else:
        geo = output.sdf.iloc[0].SHAPE.project_as(3857).centroid
        return geo[0], geo[1], track

print('[INFO] Client Start...')
@client.on(events.NewMessage(chats=channel))
async def newMessageListener(e):
    """
    Extract audio to Text
    Step:
    1. Getting Message media especially audio/recording
    2. Convert OGA to WAV format using FFMPEG
    3. Detect text from audio
    :param e:
    :return:
    text via telegram
    """
    private_message = "Text : {}\n" \
                      "Segment: {}\n" \
                      "Vehicle: {}\n" \
                      "Casualties: {}\n" \
                      "Total Vehicle: {}\n"

    if e.message.media is not None:
        ext = utils.get_extension(e.message.media)
        if ext == '.oga':
            await e.message.download_media("raw")

        file = os.listdir('raw')[0]
        output = os.path.join('voice', file[:-4]+'.wav')
        process = run(['ffmpeg', '-i', os.path.join('raw', file), output])
        print(' Convert '.center(40, "="))
        print(f'Output File: {output}')
        # Remove file raw audio
        os.remove(os.path.join('raw', file))

        text = sr.extract_from_file(output)
        doc = nlp(text)
        result = extract(doc)
        # os.remove(os.path.join('voice', file[:-4]+'.wav'))

        if result != '' or result is not None:
            segment = 'Tidak diketahui'
            track = 'Tidak diketahui'
            vehicle = 'Tidak diketahui'
            casualties = 'Tidak diketahui'
            total_vehicle = 'Tidak diketahui'
            if 'Segment' in result.keys():
                segment = result['Segment'][0]
            if 'Vehicle' in result.keys():
                vehicle = ','.join(result['Vehicle'])
            if 'Casualties' in result.keys():
                casualties = result['Casualties'][0]
            if 'Total_Vehicle' in result.keys():
                total_vehicle = result['Total_Vehicle'][0]

            # x, y, track = get_geometry(segment)
            # print(x, y)

            await client.send_message(e.message.peer_id.channel_id,
                                      message=private_message.format(
                                          text, segment, vehicle, casualties, total_vehicle
                                      ),
                                      reply_to=e.message.id)
        else:
            message = f"Text is : {text}"

            # Send back the result to channels
            await client.send_message(e.message.peer_id.channel_id, message=message, reply_to=e.message.id)
    else:
        await client.send_message(e.message.peer_id.channel_id, message="Pesan tidak mengandung audio", reply_to=e.message.id)

with client:
    client.run_until_disconnected()
